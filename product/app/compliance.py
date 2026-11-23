"""Compliance como código: reglas que se revisan solas al arrancar en producción.

Ver ``doc/compliance-checklist.md``. Los mensajes nunca muestran una clave.
"""

from app.auth import parse_api_keys
from app.config import (
    DEBUG_LOG_LEVEL,
    PRODUCTION_ENVIRONMENT,
    SUPPORTED_ENVIRONMENTS,
    ConfigError,
)

FAKE_PROVIDER = "fake"
MIN_API_KEY_LENGTH = 16


def check_production(settings):
    """Impide arrancar en producción con una configuración insegura.

    Con ``ENVIRONMENT=production`` exige: un modelo que no sea el simulado, al menos
    una clave en ``API_KEYS``, claves de 16 caracteres o más, ``LOG_LEVEL`` distinto
    de ``debug`` y, si las trazas están encendidas, ``HIDE_INPUTS`` y
    ``HIDE_OUTPUTS`` en ``true``. En ``development`` no aplica ninguna regla.

    :param settings: Configuración validada
    :type settings: app.config.Settings
    :raises app.config.ConfigError: Si se rompe alguna regla, si ``API_KEYS`` está
        mal formada o si ``ENVIRONMENT`` es desconocido
    """
    if settings.environment not in SUPPORTED_ENVIRONMENTS:
        raise ConfigError(
            f"ENVIRONMENT must be one of {SUPPORTED_ENVIRONMENTS}, "
            f"got {settings.environment!r}"
        )
    if settings.environment != PRODUCTION_ENVIRONMENT:
        return
    if settings.model_provider == FAKE_PROVIDER:
        raise ConfigError("production: MODEL_PROVIDER must not be fake")
    _check_api_keys(settings.api_keys)
    _check_log_level(settings)
    _check_tracing(settings)


def _check_log_level(settings):
    """Prohíbe el modo debug en producción.

    El mensaje es fijo: nunca incluye un valor de la configuración.

    :param settings: Configuración validada
    :type settings: app.config.Settings
    :raises app.config.ConfigError: Si ``LOG_LEVEL`` vale ``debug``
    """
    if settings.log_level == DEBUG_LOG_LEVEL:
        raise ConfigError("production: LOG_LEVEL must not be debug")


def _check_api_keys(raw):
    """Exige al menos un cliente y claves de 16 caracteres o más.

    :param raw: Valor de ``API_KEYS``
    :type raw: str
    :raises app.config.ConfigError: Si no hay claves o alguna es corta; el mensaje
        dice el número de la entrada y el largo de la clave, nunca su valor
    """
    keys = parse_api_keys(raw)
    if not keys:
        raise ConfigError("production: API_KEYS must not be empty")
    for number, key in enumerate(keys.values(), start=1):
        if len(key) < MIN_API_KEY_LENGTH:
            raise ConfigError(
                f"production: API_KEYS entry {number} has a key of {len(key)} "
                f"characters; the minimum is {MIN_API_KEY_LENGTH}"
            )


def _check_tracing(settings):
    """Con las trazas pedidas, exige que no se manden entradas ni salidas.

    :param settings: Configuración validada
    :type settings: app.config.Settings
    :raises app.config.ConfigError: Si ``LANGSMITH_TRACING=true`` y ``HIDE_INPUTS``
        o ``HIDE_OUTPUTS`` no valen ``true``
    """
    if settings.langsmith_tracing and not (
        settings.hide_inputs and settings.hide_outputs
    ):
        raise ConfigError(
            "production: with LANGSMITH_TRACING=true, HIDE_INPUTS and HIDE_OUTPUTS "
            "must be true"
        )
