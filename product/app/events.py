"""Log estructurado: una línea JSON por evento, siempre pasada por el redactor.

Con nivel ``debug`` se agregan eventos de detalle (``startup``, ``agent_step`` y
``model_call``) que solo llevan los campos de su lista blanca.
"""

import json
import logging
import re
import sys
import threading
import traceback
from datetime import timezone
from pathlib import PurePath

INFO_LEVEL = "info"
DEBUG_LEVEL = "debug"
LOG_LEVELS = (INFO_LEVEL, DEBUG_LEVEL)
REDACTED = "[REDACTED]"
SENSITIVE_NAME_PARTS = (
    "authorization",
    "api_key",
    "api-key",
    "token",
    "secret",
    "password",
    "cookie",
)
TOKEN_COUNTERS = frozenset({"input_tokens", "output_tokens"})
BEARER_PATTERN = re.compile(r"\bBearer\s+\S+", re.IGNORECASE)
BEARER_REDACTED = f"Bearer {REDACTED}"
PLAIN_VALUES = (bool, int, float, type(None))
DEBUG_EVENT_FIELDS = {
    "startup": ("environment", "model_provider", "log_level", "credentials"),
    "agent_step": ("step", "tools", "latency_ms"),
    "model_call": (
        "model", "status", "latency_ms",
        "input_tokens", "output_tokens", "cached",
    ),
}
THIRD_PARTY_LOGGERS = ("httpx", "httpcore")
PYTHON_SUFFIX = ".py"


def format_timestamp(moment):
    """Da formato ISO 8601 en UTC con milisegundos y ``Z``.

    :param moment: Fecha y hora con zona
    :type moment: datetime.datetime
    :return: Texto como ``2026-11-07T10:15:30.123Z``
    :rtype: str
    """
    utc = moment.astimezone(timezone.utc)
    millis = utc.microsecond // 1000
    return f"{utc.strftime('%Y-%m-%dT%H:%M:%S')}.{millis:03d}Z"


def _is_sensitive_name(name):
    """Indica si el nombre de un campo es sensible.

    :param name: Nombre del campo (clave de diccionario)
    :type name: object
    :return: ``True`` si contiene una parte sensible y no es un contador de tokens
    :rtype: bool
    """
    lowered = str(name).lower()
    if lowered in TOKEN_COUNTERS:
        return False
    return any(part in lowered for part in SENSITIVE_NAME_PARTS)


class Redactor:  # pylint: disable=too-few-public-methods
    """Tapa lo sensible de un evento antes de escribirlo.

    Reglas, sin excepciones por valor:

    - Un campo de diccionario con nombre sensible vale ``[REDACTED]``.
    - Cada secreto conocido se reemplaza dentro de cualquier texto.
    - ``Bearer <algo>`` pasa a ``Bearer [REDACTED]``.

    La regla por nombre mira solo las claves de los diccionarios, nunca el contenido
    de un texto.

    :param secrets: Secretos conocidos; los vacíos se ignoran
    :type secrets: collections.abc.Iterable[str]
    """

    def __init__(self, secrets=()):
        unique = {secret for secret in secrets if secret}
        self._secrets = tuple(sorted(unique, key=len, reverse=True))

    def redact(self, value):
        """Devuelve una copia de ``value`` con lo sensible reemplazado.

        :param value: Diccionario, lista, tupla, texto u otro valor
        :type value: object
        :return: Copia redactada; las tuplas salen como listas
        :rtype: object
        """
        if isinstance(value, dict):
            return {
                key: REDACTED if _is_sensitive_name(key) else self.redact(item)
                for key, item in value.items()
            }
        if isinstance(value, (list, tuple)):
            return [self.redact(item) for item in value]
        if isinstance(value, PLAIN_VALUES):
            return value
        return self._redact_text(str(value))

    def _redact_text(self, text):
        """Reemplaza los secretos conocidos y los valores ``Bearer``.

        :param text: Texto original
        :type text: str
        :return: Texto redactado
        :rtype: str
        """
        for secret in self._secrets:
            text = text.replace(secret, REDACTED)
        return BEARER_PATTERN.sub(BEARER_REDACTED, text)


def whitelisted_fields(event, fields):
    """Deja solo los campos de la lista blanca de un evento de debug.

    :param event: Nombre del evento de debug
    :type event: str
    :param fields: Campos propuestos
    :type fields: dict
    :return: Campos permitidos; un evento sin lista blanca no conserva ninguno
    :rtype: dict
    """
    allowed = DEBUG_EVENT_FIELDS.get(event, ())
    return {name: fields[name] for name in allowed if name in fields}


def stack_frames(error):
    """Resume el stack trace de una excepción sin su mensaje ni sus variables.

    Solo se conservan los frames de archivos ``.py``, con el nombre corto del archivo
    (la ruta absoluta revela usuario y máquina).

    :param error: Excepción capturada
    :type error: BaseException
    :return: Frames como ``"archivo.py:línea:función"``, del más externo al más
        interno
    :rtype: list[str]
    """
    frames = []
    for frame in traceback.extract_tb(error.__traceback__):
        name = PurePath(frame.filename).name
        if name.endswith(PYTHON_SUFFIX):
            frames.append(f"{name}:{frame.lineno}:{frame.name}")
    return frames


def quiet_third_party_loggers():
    """Fija ``httpx`` y ``httpcore`` en ``WARNING``.

    En ``DEBUG`` esas librerías imprimen encabezados, entre ellos ``Authorization``.
    """
    for name in THIRD_PARTY_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)


class EventLogger:
    """Escribe eventos JSON de una línea con los campos comunes.

    Todo evento pasa por el redactor antes de convertirse en JSON.

    :param service: Nombre del servicio (campo ``service``)
    :type service: str
    :param clock: Reloj que da la hora de cada evento
    :type clock: app.clock.Clock
    :param stream: Flujo de texto; ``None`` usa la salida estándar
    :type stream: io.TextIOBase or None
    :param level: ``info`` o ``debug``; en ``info`` se descartan los eventos de debug
    :type level: str
    :param redactor: Redactor de los eventos; ``None`` usa uno sin secretos conocidos
    :type redactor: Redactor or None
    :raises ValueError: Si ``level`` no es ``info`` ni ``debug``
    """

    def __init__(  # pylint: disable=too-many-arguments
        self, service, clock, stream=None, level=INFO_LEVEL, redactor=None
    ):
        if level not in LOG_LEVELS:
            raise ValueError(f"level must be one of {LOG_LEVELS}, got {level!r}")
        self._service = service
        self._clock = clock
        self._stream = stream
        self._level = level
        self._redactor = redactor or Redactor()
        self._lock = threading.Lock()

    @property
    def debug_enabled(self):
        """Indica si se escriben los eventos de debug.

        :rtype: bool
        """
        return self._level == DEBUG_LEVEL

    def emit(self, event, request_id, **fields):
        """Escribe un evento como una línea JSON, ya redactado.

        :param event: Nombre del evento (``request``, ``audit``...)
        :type event: str
        :param request_id: Id de la petición a la que pertenece
        :type request_id: str
        :param fields: Campos propios del evento
        :type fields: dict
        """
        record = {
            "ts": format_timestamp(self._clock.now()),
            "service": self._service,
            "event": event,
            "request_id": request_id,
        }
        record.update(fields)
        safe = self._redactor.redact(record)
        line = json.dumps(safe, ensure_ascii=False, default=str)
        stream = self._stream if self._stream is not None else sys.stdout
        with self._lock:
            stream.write(line + "\n")
            stream.flush()

    def debug(self, event, request_id, **fields):
        """Escribe un evento de debug con solo los campos de su lista blanca.

        En nivel ``info`` no hace nada.

        :param event: Nombre del evento (``startup``, ``agent_step``, ``model_call``)
        :type event: str
        :param request_id: Id de la petición, o ``"-"`` si no hay petición
        :type request_id: str
        :param fields: Campos propuestos; los que no están en la lista se descartan
        :type fields: dict
        """
        if self.debug_enabled:
            self.emit(event, request_id, **whitelisted_fields(event, fields))

    def bind(self, request_id, client=None):
        """Crea un log con el ``request_id`` y el cliente ya fijados.

        :param request_id: Id de la petición
        :type request_id: str
        :param client: Nombre del cliente identificado; ``None`` no agrega el campo
        :type client: str or None
        :return: Log de la petición
        :rtype: RequestLog
        """
        return RequestLog(self, request_id, client)


class RequestLog:
    """Log de una petición: cada evento lleva el mismo ``request_id``.

    Si se conoce el cliente, cada evento lleva también el campo ``client`` (solo el
    nombre, nunca la clave).

    :param logger: Log del proceso
    :type logger: EventLogger
    :param request_id: Id de la petición
    :type request_id: str
    :param client: Nombre del cliente, o ``None``
    :type client: str or None
    """

    def __init__(self, logger, request_id, client=None):
        self._logger = logger
        self.request_id = request_id
        self.client = client

    @property
    def debug_enabled(self):
        """Indica si el log del proceso escribe los eventos de debug.

        :rtype: bool
        """
        return self._logger.debug_enabled

    def emit(self, event, **fields):
        """Escribe un evento de esta petición.

        :param event: Nombre del evento
        :type event: str
        :param fields: Campos propios del evento
        :type fields: dict
        """
        if self.client is not None:
            fields.setdefault("client", self.client)
        self._logger.emit(event, request_id=self.request_id, **fields)

    def debug(self, event, **fields):
        """Escribe un evento de debug de esta petición; en ``info`` no hace nada.

        :param event: Nombre del evento de debug
        :type event: str
        :param fields: Campos propuestos; los que no están en la lista se descartan
        :type fields: dict
        """
        if self.debug_enabled:
            self.emit(event, **whitelisted_fields(event, fields))


class NullLog:
    """Log que descarta los eventos; se usa cuando no se inyecta ninguno."""

    debug_enabled = False

    def emit(self, event, **fields):  # pylint: disable=unused-argument
        """No hace nada.

        :param event: Nombre del evento
        :type event: str
        :param fields: Campos propios del evento
        :type fields: dict
        """

    def debug(self, event, **fields):  # pylint: disable=unused-argument
        """No hace nada.

        :param event: Nombre del evento de debug
        :type event: str
        :param fields: Campos propuestos
        :type fields: dict
        """
