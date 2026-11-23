"""Interfaz del modelo de lenguaje y modelo simulado determinista."""

import json
import re
from typing import Protocol

from app.completion import Completion, ModelUnavailableError
from app.directory import normalize_text
from app.gateway import GatewayModel, build_http_client

# ``ModelUnavailableError`` se reexporta: el resto del producto la importa de aquí.
__all__ = [
    "ANSWER_PREFIX",
    "TOOL_RESULT_PREFIX",
    "Completion",
    "FakeModel",
    "LanguageModel",
    "ModelUnavailableError",
    "build_model",
    "build_models",
    "count_words",
]

TOOL_RESULT_PREFIX = "Resultado de la herramienta: "
ANSWER_PREFIX = "Según el directorio: "
HELP_ANSWER = "Pregúntame por un empleado (EMP-0001) o un departamento."
EMPLOYEE_ID_PATTERN = re.compile(r"\bEMP-\d{4}\b", re.IGNORECASE)
WORD_PATTERN = re.compile(r"\w+")
MIN_NAME_PART_CHARS = 3
FAKE_MODEL_NAME = "fake"


class LanguageModel(Protocol):  # pylint: disable=too-few-public-methods
    """Protocolo que cumple cualquier proveedor de modelo."""

    def complete(self, messages):
        """Completa una conversación.

        :param messages: Mensajes con ``role`` y ``content``
        :type messages: list[dict]
        :return: Respuesta del modelo
        :rtype: Completion
        """


def count_words(text):
    """Cuenta palabras separadas por espacios.

    :param text: Texto a contar
    :type text: str
    :return: Número de palabras
    :rtype: int
    """
    return len(str(text).split())


class FakeModel:  # pylint: disable=too-few-public-methods
    """Modelo simulado con reglas fijas sobre el último mensaje.

    :param departments: Departamentos que existen en el directorio
    :type departments: collections.abc.Iterable[str]
    :param names: Nombres completos de los empleados; vacío desactiva la regla de
        nombre
    :type names: collections.abc.Iterable[str]
    :param name: Nombre del modelo simulado; con él se busca su precio
    :type name: str
    """

    def __init__(self, departments, names=(), name=FAKE_MODEL_NAME):
        self._departments = tuple(departments)
        self._names = tuple(names)
        self.name = name

    def complete(self, messages):
        """Decide la respuesta según las reglas de la especificación.

        :param messages: Mensajes con ``role`` y ``content``
        :type messages: list[dict]
        :return: Respuesta JSON con tokens contados por palabras
        :rtype: Completion
        """
        last = messages[-1]["content"] if messages else ""
        text = json.dumps(self._decide(last), ensure_ascii=False)
        input_tokens = sum(count_words(message["content"]) for message in messages)
        return Completion(
            text=text, input_tokens=input_tokens, output_tokens=count_words(text)
        )

    def _decide(self, last):
        """Aplica las cinco reglas en orden de prioridad.

        :param last: Contenido del último mensaje
        :type last: str
        :return: Objeto del protocolo (``tool``/``args`` o ``answer``)
        :rtype: dict
        """
        if last.startswith(TOOL_RESULT_PREFIX):
            result = last[len(TOOL_RESULT_PREFIX):]
            return {"answer": f"{ANSWER_PREFIX}{result}"}
        match = EMPLOYEE_ID_PATTERN.search(last)
        if match:
            employee_id = match.group(0).upper()
            return {"tool": "get_employee", "args": {"employee_id": employee_id}}
        department = self._find_department(last)
        if department:
            return {"tool": "search_by_department", "args": {"department": department}}
        name = self._find_name(last)
        if name:
            return {"tool": "search_by_name", "args": {"name": name}}
        return {"answer": HELP_ANSWER}

    def _find_name(self, text):
        """Busca un nombre completo o una parte de nombre mencionada en el texto.

        Compara palabras completas normalizadas e ignora las partes de menos de
        ``MIN_NAME_PART_CHARS`` letras para no confundir palabras comunes con nombres.

        :param text: Texto donde buscar
        :type text: str
        :return: Nombre completo o parte de nombre tal como está en los datos, o
            ``None``
        :rtype: str or None
        """
        words = WORD_PATTERN.findall(normalize_text(text))
        joined = " ".join(words)
        for full_name in self._names:
            wanted = " ".join(WORD_PATTERN.findall(normalize_text(full_name)))
            if wanted and re.search(r"\b" + re.escape(wanted) + r"\b", joined):
                return full_name
        parts = {}
        for full_name in self._names:
            for part in full_name.split():
                key = normalize_text(part)
                if len(key) >= MIN_NAME_PART_CHARS:
                    parts.setdefault(key, part)
        for word in words:
            if word in parts:
                return parts[word]
        return None

    def _find_department(self, text):
        """Busca un departamento conocido mencionado en el texto.

        :param text: Texto donde buscar
        :type text: str
        :return: Nombre del departamento o ``None``
        :rtype: str or None
        """
        normalized = normalize_text(text)
        for department in self._departments:
            pattern = r"\b" + re.escape(normalize_text(department)) + r"\b"
            if re.search(pattern, normalized):
                return department
        return None


def build_model(settings, directory):
    """Construye el modelo indicado por la configuración.

    :param settings: Configuración validada
    :type settings: app.config.Settings
    :param directory: Directorio de empleados (aporta departamentos y nombres)
    :type directory: app.directory.EmployeeDirectory
    :return: Modelo listo para usar
    :rtype: LanguageModel
    :raises ValueError: Si el proveedor no está soportado
    """
    if settings.model_provider == "fake":
        return FakeModel(directory.departments(), directory.names())
    raise ValueError(f"Unsupported MODEL_PROVIDER: {settings.model_provider}")


def build_models(settings, directory, http_client=None):
    """Construye un modelo por nombre: ``MODEL_SMALL`` y ``MODEL_LARGE``.

    Con ``fake`` son dos simulados que responden igual pero se llaman como cada
    modelo, para cobrarlos con su precio. Con ``gateway`` comparten un cliente HTTP.

    :param settings: Configuración validada
    :type settings: app.config.Settings
    :param directory: Directorio de empleados (aporta departamentos y nombres)
    :type directory: app.directory.EmployeeDirectory
    :param http_client: Cliente ``httpx`` para el gateway; ``None`` crea uno
    :type http_client: httpx.Client or None
    :return: Modelos por nombre
    :rtype: dict[str, LanguageModel]
    :raises ValueError: Si el proveedor no está soportado
    """
    names = (settings.model_small, settings.model_large)
    if settings.model_provider == "fake":
        return {
            name: FakeModel(directory.departments(), directory.names(), name=name)
            for name in names
        }
    if settings.model_provider == "gateway":
        client = http_client or build_http_client()
        return {name: GatewayModel(name, settings, client) for name in names}
    raise ValueError(f"Unsupported MODEL_PROVIDER: {settings.model_provider}")
