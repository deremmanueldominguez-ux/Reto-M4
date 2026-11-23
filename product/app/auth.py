"""Acceso por clave: una clave por cliente en el encabezado ``X-API-Key``.

La clave nunca se escribe en el log, en la traza ni en un mensaje de error: los
errores de ``API_KEYS`` dicen el número de la entrada y su largo, y en la petición
solo se guarda el nombre del cliente.
"""

import hmac

from fastapi import HTTPException, Request

from app.config import ConfigError

API_KEY_HEADER = "X-API-Key"
ENTRY_SEPARATOR = ","
CLIENT_SEPARATOR = ":"
UNAUTHORIZED_STATUS = 401
UNAUTHORIZED_DETAIL = "invalid or missing API key"


def _entry_error(number, entry, problem):
    """Arma el error de una entrada de ``API_KEYS`` sin mostrar su valor.

    :param number: Número de la entrada, desde 1
    :type number: int
    :param entry: Entrada sin espacios en los extremos; solo se usa su largo
    :type entry: str
    :param problem: Qué falla, en pocas palabras
    :type problem: str
    :return: Error listo para lanzar
    :rtype: app.config.ConfigError
    """
    return ConfigError(
        f"API_KEYS entry {number} ({len(entry)} characters) {problem}; "
        "expected client:key"
    )


def parse_api_keys(raw):
    """Lee ``API_KEYS`` con la forma ``cliente:clave,cliente2:clave2``.

    Se quitan los espacios alrededor de cada entrada, cliente y clave. Un texto vacío
    da un diccionario vacío.

    :param raw: Valor de ``API_KEYS``
    :type raw: str or None
    :return: Clave por nombre de cliente, en el orden de ``API_KEYS``
    :rtype: dict[str, str]
    :raises app.config.ConfigError: Si una entrada no tiene ``:``, tiene el cliente o
        la clave vacíos, o repite un cliente o una clave; el mensaje dice el número de
        la entrada y su largo, nunca su valor
    """
    keys = {}
    if not (raw or "").strip():
        return keys
    for number, part in enumerate(raw.split(ENTRY_SEPARATOR), start=1):
        entry = part.strip()
        client, separator, key = entry.partition(CLIENT_SEPARATOR)
        client, key = client.strip(), key.strip()
        if not separator:
            raise _entry_error(number, entry, "has no ':'")
        if not client:
            raise _entry_error(number, entry, "has an empty client")
        if not key:
            raise _entry_error(number, entry, "has an empty key")
        if client in keys:
            raise _entry_error(number, entry, "repeats a client")
        if key in keys.values():
            raise _entry_error(number, entry, "repeats the key of another client")
        keys[client] = key
    return keys


class ApiKeyAuth:
    """Identifica al cliente por su clave.

    :param keys: Clave por nombre de cliente (resultado de ``parse_api_keys``)
    :type keys: dict[str, str]
    """

    def __init__(self, keys):
        self._keys = tuple(
            (client, key.encode("utf-8")) for client, key in keys.items()
        )

    def __repr__(self):
        """Muestra cuántos clientes hay, nunca sus claves.

        :rtype: str
        """
        return f"ApiKeyAuth(clients={len(self._keys)})"

    def identify(self, key):
        """Devuelve el cliente dueño de la clave.

        Compara con ``hmac.compare_digest`` contra todas las claves, sin cortar en la
        primera que coincide, para no dar pistas por el tiempo de respuesta.

        :param key: Clave recibida; ``None`` o vacía si no llegó
        :type key: str or None
        :return: Nombre del cliente, o ``None`` si la clave no es válida
        :rtype: str or None
        """
        if not key:
            return None
        received = key.encode("utf-8")
        found = None
        for client, expected in self._keys:
            if hmac.compare_digest(received, expected):
                found = client
        return found

    def require_client(self, request: Request):
        """Dependencia de FastAPI: exige una clave válida en ``X-API-Key``.

        Guarda solo el nombre del cliente en ``request.state.client``.

        :param request: Petición en curso
        :type request: fastapi.Request
        :return: Nombre del cliente
        :rtype: str
        :raises fastapi.HTTPException: ``401`` si la clave falta o no es válida
        """
        client = self.identify(request.headers.get(API_KEY_HEADER))
        if client is None:
            raise HTTPException(
                status_code=UNAUTHORIZED_STATUS, detail=UNAUTHORIZED_DETAIL
            )
        request.state.client = client
        return client
