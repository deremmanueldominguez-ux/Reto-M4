"""Palancas 1 y 2: enrutador por regla y ventana de historial."""

from dataclasses import dataclass

from app.directory import normalize_text

# Palabras clave ya normalizadas (minúsculas y sin tildes), en orden de prioridad.
ROUTER_KEYWORDS = ("compara", "resume", "explica", "por que", "analiza", "todos")
REASON_ROUTING_OFF = "routing_off"
REASON_LONG_QUESTION = "long_question"
REASON_KEYWORD = "keyword:{keyword}"
REASON_SHORT_QUESTION = "short_question"


@dataclass(frozen=True)
class Route:
    """Modelo elegido para una pregunta y el motivo.

    :param model: Nombre del modelo elegido
    :type model: str
    :param reason: Motivo: ``routing_off``, ``long_question``,
        ``keyword:<palabra>`` o ``short_question``
    :type reason: str
    """

    model: str
    reason: str


def route(question, settings):
    """Elige el modelo de una pregunta con una regla en código, no con otro modelo.

    Va a ``MODEL_LARGE`` si el enrutamiento está apagado, si la pregunta pasa de
    ``ROUTER_MAX_CHARS`` caracteres o si contiene una palabra clave (sin distinguir
    mayúsculas ni tildes); si no, a ``MODEL_SMALL``.

    :param question: Pregunta de la persona
    :type question: str
    :param settings: Configuración validada
    :type settings: app.config.Settings
    :return: Modelo y motivo
    :rtype: Route
    """
    if not settings.routing:
        return Route(settings.model_large, REASON_ROUTING_OFF)
    if len(question) > settings.router_max_chars:
        return Route(settings.model_large, REASON_LONG_QUESTION)
    normalized = normalize_text(question)
    for keyword in ROUTER_KEYWORDS:
        if keyword in normalized:
            return Route(settings.model_large, REASON_KEYWORD.format(keyword=keyword))
    return Route(settings.model_small, REASON_SHORT_QUESTION)


def apply_window(history, window):
    """Devuelve solo los últimos ``window`` mensajes del historial.

    Con ``0`` devuelve una lista vacía (``history[-0:]`` devolvería todo). No
    modifica la lista original.

    :param history: Turnos previos con ``role`` y ``content``
    :type history: list[dict]
    :param window: Mensajes que se conservan
    :type window: int
    :return: Copia con los últimos mensajes
    :rtype: list[dict]
    """
    if window <= 0:
        return []
    return list(history[-window:])
