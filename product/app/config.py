"""Configuración del HR Assistant leída de variables de entorno."""

import math
from dataclasses import dataclass, field
from pathlib import Path

PRODUCT_ROOT = Path(__file__).resolve().parent.parent
GATEWAY_PROVIDER = "gateway"
SUPPORTED_PROVIDERS = ("fake", GATEWAY_PROVIDER)
DEFAULT_MODEL_PROVIDER = "fake"
DEFAULT_AGENT_MAX_STEPS = 3
DEFAULT_MAX_QUESTION_CHARS = 2000
DEFAULT_EMPLOYEES_PATH = "data/employees.json"
DEFAULT_SERVICE_NAME = "hr-assistant"
DEFAULT_SLO_P95_MS = 2000
BOOLEAN_VALUES = {"true": True, "false": False}
DEFAULT_CF_GATEWAY_ID = "default"
DEFAULT_MODEL_SMALL = "@cf/meta/llama-3.1-8b-instruct-fast"
DEFAULT_MODEL_LARGE = "@cf/meta/llama-3.3-70b-instruct-fp8-fast"
DEFAULT_ROUTER_MAX_CHARS = 80
DEFAULT_HISTORY_WINDOW = 6
DEFAULT_MODEL_MAX_TOKENS = 300
DEFAULT_MODEL_TEMPERATURE = 0.0
DEFAULT_CACHE_TTL_SECONDS = 0
DEFAULT_PRICES_PATH = "data/model_prices.json"
CF_REQUIRED_VARIABLES = ("CF_ACCOUNT_ID", "CF_GATEWAY_ID", "CF_API_TOKEN")
DEVELOPMENT_ENVIRONMENT = "development"
PRODUCTION_ENVIRONMENT = "production"
SUPPORTED_ENVIRONMENTS = (DEVELOPMENT_ENVIRONMENT, PRODUCTION_ENVIRONMENT)
DEFAULT_RATE_LIMIT_PER_MINUTE = 30
INFO_LOG_LEVEL = "info"
DEBUG_LOG_LEVEL = "debug"
SUPPORTED_LOG_LEVELS = (INFO_LOG_LEVEL, DEBUG_LOG_LEVEL)


class ConfigError(ValueError):
    """Error de configuración que impide arrancar la aplicación."""


@dataclass(frozen=True)
class Settings:  # pylint: disable=too-many-instance-attributes
    """Configuración inmutable de la aplicación.

    :param model_provider: Proveedor del modelo: ``fake`` o ``gateway``
    :type model_provider: str
    :param agent_max_steps: Tope de vueltas del bucle del agente
    :type agent_max_steps: int
    :param max_question_chars: Largo máximo de la pregunta
    :type max_question_chars: int
    :param employees_path: Ruta absoluta del archivo de empleados
    :type employees_path: pathlib.Path
    :param service_name: Campo ``service`` del log
    :type service_name: str
    :param slo_p95_ms: Meta de latencia p95 en milisegundos
    :type slo_p95_ms: int
    :param langsmith_tracing: Si se pidió encender las trazas
    :type langsmith_tracing: bool
    :param hide_inputs: No mandar entradas a LangSmith
    :type hide_inputs: bool
    :param hide_outputs: No mandar salidas a LangSmith
    :type hide_outputs: bool
    :param tracing_enabled: Trazas pedidas y con ``LANGSMITH_API_KEY`` presente
    :type tracing_enabled: bool
    :param cf_account_id: Id de la cuenta de Cloudflare
    :type cf_account_id: str
    :param cf_gateway_id: Id del AI Gateway
    :type cf_gateway_id: str
    :param cf_api_token: Token de Cloudflare; secreto, nunca sale en ``repr``
    :type cf_api_token: str
    :param model_small: Nombre del modelo barato
    :type model_small: str
    :param model_large: Nombre del modelo capaz
    :type model_large: str
    :param routing: Si el enrutador elige el modelo por pregunta
    :type routing: bool
    :param router_max_chars: Preguntas más largas van al modelo capaz
    :type router_max_chars: int
    :param history_window: Mensajes de historial que se mandan al modelo
    :type history_window: int
    :param model_max_tokens: Tope de tokens de salida por llamada
    :type model_max_tokens: int
    :param model_temperature: Temperatura del modelo
    :type model_temperature: float
    :param cache_ttl_seconds: Segundos de caché del gateway; 0 la apaga
    :type cache_ttl_seconds: int
    :param prices_path: Ruta absoluta de la tabla de precios
    :type prices_path: pathlib.Path
    :param environment: ``development`` o ``production``; con ``production`` se
        aplican las reglas de compliance
    :type environment: str
    :param api_keys: Texto crudo de ``API_KEYS``; secreto, nunca sale en ``repr``
    :type api_keys: str
    :param rate_limit_per_minute: Peticiones por cliente por minuto
    :type rate_limit_per_minute: int
    :param log_level: Nivel del log: ``info`` o ``debug``
    :type log_level: str
    :param langsmith_api_key: Clave de LangSmith; secreto, nunca sale en ``repr``.
        Solo se guarda para que el redactor del log la conozca
    :type langsmith_api_key: str
    """

    model_provider: str
    agent_max_steps: int
    max_question_chars: int
    employees_path: Path
    service_name: str = DEFAULT_SERVICE_NAME
    slo_p95_ms: int = DEFAULT_SLO_P95_MS
    langsmith_tracing: bool = False
    hide_inputs: bool = True
    hide_outputs: bool = True
    tracing_enabled: bool = False
    cf_account_id: str = ""
    cf_gateway_id: str = DEFAULT_CF_GATEWAY_ID
    cf_api_token: str = field(default="", repr=False)
    model_small: str = DEFAULT_MODEL_SMALL
    model_large: str = DEFAULT_MODEL_LARGE
    routing: bool = True
    router_max_chars: int = DEFAULT_ROUTER_MAX_CHARS
    history_window: int = DEFAULT_HISTORY_WINDOW
    model_max_tokens: int = DEFAULT_MODEL_MAX_TOKENS
    model_temperature: float = DEFAULT_MODEL_TEMPERATURE
    cache_ttl_seconds: int = DEFAULT_CACHE_TTL_SECONDS
    prices_path: Path = PRODUCT_ROOT / DEFAULT_PRICES_PATH
    environment: str = DEVELOPMENT_ENVIRONMENT
    api_keys: str = field(default="", repr=False)
    rate_limit_per_minute: int = DEFAULT_RATE_LIMIT_PER_MINUTE
    log_level: str = INFO_LOG_LEVEL
    langsmith_api_key: str = field(default="", repr=False)


def _positive_int(env, name, default):
    """Lee un entero mayor o igual a 1.

    :param env: Variables de entorno
    :type env: collections.abc.Mapping
    :param name: Nombre de la variable
    :type name: str
    :param default: Valor por omisión
    :type default: int
    :return: Valor leído
    :rtype: int
    :raises ConfigError: Si el valor no es un entero mayor o igual a 1
    """
    raw = env.get(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        value = int(raw.strip())
    except ValueError as error:
        raise ConfigError(f"{name} must be an integer >= 1, got {raw!r}") from error
    if value < 1:
        raise ConfigError(f"{name} must be an integer >= 1, got {raw!r}")
    return value


def _non_negative_int(env, name, default):
    """Lee un entero mayor o igual a 0.

    :param env: Variables de entorno
    :type env: collections.abc.Mapping
    :param name: Nombre de la variable
    :type name: str
    :param default: Valor por omisión
    :type default: int
    :return: Valor leído
    :rtype: int
    :raises ConfigError: Si el valor no es un entero mayor o igual a 0
    """
    raw = env.get(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        value = int(raw.strip())
    except ValueError as error:
        raise ConfigError(f"{name} must be an integer >= 0, got {raw!r}") from error
    if value < 0:
        raise ConfigError(f"{name} must be an integer >= 0, got {raw!r}")
    return value


def _non_negative_float(env, name, default):
    """Lee un número finito mayor o igual a 0.

    :param env: Variables de entorno
    :type env: collections.abc.Mapping
    :param name: Nombre de la variable
    :type name: str
    :param default: Valor por omisión
    :type default: float
    :return: Valor leído
    :rtype: float
    :raises ConfigError: Si el valor no es un número finito mayor o igual a 0
    """
    raw = env.get(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        value = float(raw.strip())
    except ValueError as error:
        raise ConfigError(f"{name} must be a number >= 0, got {raw!r}") from error
    if not math.isfinite(value) or value < 0:
        raise ConfigError(f"{name} must be a number >= 0, got {raw!r}")
    return value


def _text(env, name, default):
    """Lee un texto; sin definir o vacío usa el valor por omisión.

    :param env: Variables de entorno
    :type env: collections.abc.Mapping
    :param name: Nombre de la variable
    :type name: str
    :param default: Valor por omisión
    :type default: str
    :return: Texto sin espacios en los extremos
    :rtype: str
    """
    return (env.get(name) or "").strip() or default


def _boolean(env, name, default):
    """Lee ``true`` o ``false`` sin distinguir mayúsculas.

    :param env: Variables de entorno
    :type env: collections.abc.Mapping
    :param name: Nombre de la variable
    :type name: str
    :param default: Valor por omisión si no está definida o está vacía
    :type default: bool
    :return: Valor leído
    :rtype: bool
    :raises ConfigError: Si el valor no es ``true`` ni ``false``
    """
    raw = env.get(name)
    if raw is None or raw.strip() == "":
        return default
    value = BOOLEAN_VALUES.get(raw.strip().lower())
    if value is None:
        raise ConfigError(f"{name} must be true or false, got {raw!r}")
    return value


def _service_name(env):
    """Lee el nombre del servicio; definido pero vacío impide arrancar.

    :param env: Variables de entorno
    :type env: collections.abc.Mapping
    :return: Nombre del servicio
    :rtype: str
    :raises ConfigError: Si el valor está vacío
    """
    raw = env.get("SERVICE_NAME")
    if raw is None:
        return DEFAULT_SERVICE_NAME
    if raw.strip() == "":
        raise ConfigError("SERVICE_NAME must not be empty")
    return raw.strip()


def _langsmith_key(env):
    """Lee la clave de LangSmith sin mostrarla.

    :param env: Variables de entorno
    :type env: collections.abc.Mapping
    :return: Clave sin espacios en los extremos; vacía si no está definida
    :rtype: str
    """
    return (env.get("LANGSMITH_API_KEY") or "").strip()


def _log_level(env):
    """Lee el nivel del log sin distinguir mayúsculas.

    :param env: Variables de entorno
    :type env: collections.abc.Mapping
    :return: ``info`` o ``debug``
    :rtype: str
    :raises ConfigError: Si el valor no es uno de los conocidos
    """
    value = _text(env, "LOG_LEVEL", INFO_LOG_LEVEL).lower()
    if value not in SUPPORTED_LOG_LEVELS:
        raise ConfigError(
            f"LOG_LEVEL must be one of {SUPPORTED_LOG_LEVELS}, got {value!r}"
        )
    return value


def _product_path(env, name, default):
    """Resuelve una ruta; las relativas se toman desde ``product/``.

    :param env: Variables de entorno
    :type env: collections.abc.Mapping
    :param name: Nombre de la variable
    :type name: str
    :param default: Ruta por omisión, relativa a ``product/``
    :type default: str
    :return: Ruta absoluta
    :rtype: pathlib.Path
    """
    path = Path(env.get(name) or default)
    if not path.is_absolute():
        path = PRODUCT_ROOT / path
    return path


def _employees_path(env):
    """Resuelve la ruta de los datos; las relativas se toman desde ``product/``.

    :param env: Variables de entorno
    :type env: collections.abc.Mapping
    :return: Ruta absoluta existente
    :rtype: pathlib.Path
    :raises ConfigError: Si el archivo no existe
    """
    path = _product_path(env, "EMPLOYEES_PATH", DEFAULT_EMPLOYEES_PATH)
    if not path.is_file():
        raise ConfigError(f"EMPLOYEES_PATH does not point to a file: {path}")
    return path


def _cloudflare(env, provider):
    """Lee la cuenta, el gateway y el token de Cloudflare.

    Con ``gateway`` las tres son obligatorias. El token nunca va en los mensajes de
    error.

    :param env: Variables de entorno
    :type env: collections.abc.Mapping
    :param provider: Proveedor del modelo ya validado
    :type provider: str
    :return: Campos ``cf_account_id``, ``cf_gateway_id`` y ``cf_api_token``
    :rtype: dict
    :raises ConfigError: Si el proveedor es ``gateway`` y falta alguna variable
    """
    raw_gateway = env.get("CF_GATEWAY_ID")
    values = {
        "CF_ACCOUNT_ID": (env.get("CF_ACCOUNT_ID") or "").strip(),
        "CF_GATEWAY_ID": (
            DEFAULT_CF_GATEWAY_ID if raw_gateway is None else raw_gateway.strip()
        ),
        "CF_API_TOKEN": (env.get("CF_API_TOKEN") or "").strip(),
    }
    if provider == GATEWAY_PROVIDER:
        for name in CF_REQUIRED_VARIABLES:
            if not values[name]:
                raise ConfigError(f"{name} is required when MODEL_PROVIDER=gateway")
    return {
        "cf_account_id": values["CF_ACCOUNT_ID"],
        "cf_gateway_id": values["CF_GATEWAY_ID"] or DEFAULT_CF_GATEWAY_ID,
        "cf_api_token": values["CF_API_TOKEN"],
    }


def _cost_levers(env):
    """Lee los modelos, las cuatro palancas de costo y la tabla de precios.

    :param env: Variables de entorno
    :type env: collections.abc.Mapping
    :return: Campos de ``Settings`` de la sesión de costos
    :rtype: dict
    :raises ConfigError: Si algún valor es inválido
    """
    return {
        "model_small": _text(env, "MODEL_SMALL", DEFAULT_MODEL_SMALL),
        "model_large": _text(env, "MODEL_LARGE", DEFAULT_MODEL_LARGE),
        "routing": _boolean(env, "ROUTING", True),
        "router_max_chars": _positive_int(
            env, "ROUTER_MAX_CHARS", DEFAULT_ROUTER_MAX_CHARS
        ),
        "history_window": _non_negative_int(
            env, "HISTORY_WINDOW", DEFAULT_HISTORY_WINDOW
        ),
        "model_max_tokens": _positive_int(
            env, "MODEL_MAX_TOKENS", DEFAULT_MODEL_MAX_TOKENS
        ),
        "model_temperature": _non_negative_float(
            env, "MODEL_TEMPERATURE", DEFAULT_MODEL_TEMPERATURE
        ),
        "cache_ttl_seconds": _non_negative_int(
            env, "CACHE_TTL_SECONDS", DEFAULT_CACHE_TTL_SECONDS
        ),
        "prices_path": _product_path(env, "PRICES_PATH", DEFAULT_PRICES_PATH),
    }


def _environment(env):
    """Lee el entorno de despliegue; un valor desconocido impide arrancar.

    :param env: Variables de entorno
    :type env: collections.abc.Mapping
    :return: ``development`` o ``production``
    :rtype: str
    :raises ConfigError: Si el valor no es uno de los conocidos
    """
    value = _text(env, "ENVIRONMENT", DEVELOPMENT_ENVIRONMENT).lower()
    if value not in SUPPORTED_ENVIRONMENTS:
        raise ConfigError(
            f"ENVIRONMENT must be one of {SUPPORTED_ENVIRONMENTS}, got {value!r}"
        )
    return value


def _production(env):
    """Lee el entorno, las claves de los clientes y el límite de peticiones.

    ``API_KEYS`` se guarda tal cual: la valida ``app.auth.parse_api_keys`` al crear
    la aplicación, y nunca va en un mensaje de error.

    :param env: Variables de entorno
    :type env: collections.abc.Mapping
    :return: Campos de ``Settings`` de la sesión de producción
    :rtype: dict
    :raises ConfigError: Si ``ENVIRONMENT`` o ``RATE_LIMIT_PER_MINUTE`` son inválidos
    """
    return {
        "environment": _environment(env),
        "api_keys": env.get("API_KEYS") or "",
        "rate_limit_per_minute": _positive_int(
            env, "RATE_LIMIT_PER_MINUTE", DEFAULT_RATE_LIMIT_PER_MINUTE
        ),
    }


def load_settings(env):
    """Construye la configuración a partir de las variables de entorno.

    :param env: Variables de entorno (por ejemplo ``os.environ``)
    :type env: collections.abc.Mapping
    :return: Configuración validada
    :rtype: Settings
    :raises ConfigError: Si algún valor es inválido
    """
    provider = (env.get("MODEL_PROVIDER") or DEFAULT_MODEL_PROVIDER).strip()
    if provider not in SUPPORTED_PROVIDERS:
        raise ConfigError(
            f"MODEL_PROVIDER must be one of {SUPPORTED_PROVIDERS}, got {provider!r}"
        )
    tracing = _boolean(env, "LANGSMITH_TRACING", False)
    langsmith_api_key = _langsmith_key(env)
    return Settings(
        model_provider=provider,
        agent_max_steps=_positive_int(
            env, "AGENT_MAX_STEPS", DEFAULT_AGENT_MAX_STEPS
        ),
        max_question_chars=_positive_int(
            env, "MAX_QUESTION_CHARS", DEFAULT_MAX_QUESTION_CHARS
        ),
        employees_path=_employees_path(env),
        service_name=_service_name(env),
        slo_p95_ms=_positive_int(env, "SLO_P95_MS", DEFAULT_SLO_P95_MS),
        langsmith_tracing=tracing,
        hide_inputs=_boolean(env, "HIDE_INPUTS", True),
        hide_outputs=_boolean(env, "HIDE_OUTPUTS", True),
        tracing_enabled=tracing and bool(langsmith_api_key),
        **_cloudflare(env, provider),
        **_cost_levers(env),
        **_production(env),
        log_level=_log_level(env),
        langsmith_api_key=langsmith_api_key,
    )
