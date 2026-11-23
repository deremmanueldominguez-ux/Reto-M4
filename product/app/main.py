"""API web sin estado del HR Assistant, con observabilidad.

Se arranca con ``uvicorn app.main:app --no-access-log`` desde la carpeta
``product/``.
"""

import os
from pathlib import Path
from typing import List, Literal

from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field, field_validator

from app.agent import Agent, Billing
from app.auth import ApiKeyAuth, parse_api_keys
from app.clock import SystemClock
from app.compliance import check_production
from app.config import load_settings
from app.directory import EmployeeDirectory
from app.events import EventLogger, Redactor, quiet_third_party_loggers
from app.llm import ModelUnavailableError, build_models
from app.metrics import Metrics
from app.middleware import error_fields, install_observability
from app.pricing import PriceTable
from app.rate_limit import RateLimiter
from app.router import route
from app.tracing import Tracer

STATIC_DIR = Path(__file__).resolve().parent / "static"
COST_DECIMALS = 8
MODEL_UNAVAILABLE_STATUS = 502
MODEL_UNAVAILABLE_DETAIL = "model unavailable"
NO_REQUEST_ID = "-"
SET = "set"
UNSET = "unset"


class HistoryTurn(BaseModel):
    """Turno previo de la conversación enviado por el cliente.

    :param role: Quién habló: ``user`` o ``assistant``
    :type role: str
    :param content: Texto del turno
    :type content: str
    """

    role: Literal["user", "assistant"]
    content: str


class AskResponse(BaseModel):
    """Respuesta de ``POST /ask``.

    :param answer: Respuesta en español
    :type answer: str
    :param steps: Llamadas al modelo
    :type steps: int
    :param tools_used: Herramientas usadas, en orden
    :type tools_used: list[str]
    :param input_tokens: Tokens de entrada sumados
    :type input_tokens: int
    :param output_tokens: Tokens de salida sumados
    :type output_tokens: int
    :param request_id: Id de la petición, para pasarlo a soporte
    :type request_id: str
    :param model: Modelo que eligió el enrutador
    :type model: str
    :param route: Motivo del enrutador
    :type route: str
    :param cached_calls: Llamadas que respondió la caché del gateway
    :type cached_calls: int
    :param cost_usd: Costo de la respuesta en USD, redondeado a 8 decimales
    :type cost_usd: float
    """

    answer: str
    steps: int
    tools_used: List[str]
    input_tokens: int
    output_tokens: int
    request_id: str
    model: str
    route: str
    cached_calls: int
    cost_usd: float


def build_ask_request(max_question_chars):
    """Crea el modelo de entrada de ``POST /ask`` con el largo configurado.

    :param max_question_chars: Largo máximo de la pregunta
    :type max_question_chars: int
    :return: Clase Pydantic que valida el cuerpo
    :rtype: type[pydantic.BaseModel]
    """

    class AskRequest(BaseModel):
        """Cuerpo de ``POST /ask``.

        :param question: Pregunta de la persona
        :type question: str
        :param history: Turnos previos; opcional
        :type history: list[HistoryTurn]
        """

        question: str = Field(max_length=max_question_chars)
        history: List[HistoryTurn] = Field(default_factory=list)

        @field_validator("question")
        @classmethod
        def question_is_not_blank(cls, value):
            """Rechaza preguntas vacías y quita espacios de los extremos.

            :param value: Pregunta recibida
            :type value: str
            :return: Pregunta sin espacios en los extremos
            :rtype: str
            :raises ValueError: Si la pregunta queda vacía
            """
            stripped = value.strip()
            if not stripped:
                raise ValueError("question must not be empty")
            return stripped

    return AskRequest


def create_app(  # pylint: disable=too-many-arguments
    settings=None,
    model=None,
    directory=None,
    *,
    models=None,
    prices=None,
    clock=None,
    log_stream=None,
    tracer=None,
):
    """Crea la aplicación FastAPI con sus dependencias.

    Las dependencias que no se pasan se construyen a partir de ``os.environ``.

    :param settings: Configuración validada
    :type settings: app.config.Settings or None
    :param model: Un solo modelo que se usa para ``MODEL_SMALL`` y ``MODEL_LARGE``
        (compatibilidad con las sesiones 1 y 2)
    :type model: app.llm.LanguageModel or None
    :param directory: Directorio de empleados
    :type directory: app.directory.EmployeeDirectory or None
    :param models: Modelos por nombre; ``None`` los arma con ``build_models``
    :type models: dict[str, app.llm.LanguageModel] or None
    :param prices: Tabla de precios; ``None`` la carga de ``PRICES_PATH``
    :type prices: app.pricing.PriceTable or None
    :param clock: Reloj; ``None`` usa el del sistema
    :type clock: app.clock.Clock or None
    :param log_stream: Flujo del log JSON; ``None`` usa la salida estándar
    :type log_stream: io.TextIOBase or None
    :param tracer: Trazador; ``None`` lo arma según la configuración
    :type tracer: app.tracing.Tracer or None
    :return: Aplicación lista para servir
    :rtype: fastapi.FastAPI
    :raises app.config.ConfigError: Si la configuración del entorno es inválida,
        ``API_KEYS`` está mal formada, se rompe una regla de compliance de
        producción o un modelo configurado no tiene precio
    """
    settings = settings or load_settings(os.environ)
    api_keys = parse_api_keys(settings.api_keys)
    auth = ApiKeyAuth(api_keys)
    check_production(settings)
    prices = prices or PriceTable(settings.prices_path)
    prices.require((settings.model_small, settings.model_large))
    directory = directory or EmployeeDirectory(settings.employees_path)
    models = models or _models(settings, model, directory)
    tracer = tracer or Tracer.from_settings(settings)
    clock = clock or SystemClock()
    logger = _build_logger(settings, api_keys, clock, log_stream)
    metrics = Metrics()

    def make_agent(request_id, client, chosen):
        """Crea un ``Agent`` nuevo con el modelo enrutado.

        :param request_id: Id de la petición
        :type request_id: str
        :param client: Nombre del cliente identificado
        :type client: str
        :param chosen: Modelo y motivo del enrutador
        :type chosen: app.router.Route
        :rtype: app.agent.Agent
        """
        return Agent(
            model=models[chosen.model],
            directory=directory,
            max_steps=settings.agent_max_steps,
            log=logger.bind(request_id, client=client),
            trace=tracer.bind(request_id, client=client),
            history_window=settings.history_window,
            billing=Billing(model=chosen.model, route=chosen.reason, prices=prices),
            clock=clock,
        )

    application = FastAPI(title="HR Assistant")
    install_observability(application, clock, logger, metrics)
    _add_error_handlers(application, logger)
    guard = _build_guard(auth, RateLimiter(settings.rate_limit_per_minute, clock))
    _add_routes(application, settings, make_agent, metrics, guard)
    return application


def _build_logger(settings, api_keys, clock, log_stream):
    """Arma el log JSON con su redactor y emite ``startup`` en ``debug``.

    El redactor conoce las claves de ``API_KEYS``, ``CF_API_TOKEN`` y
    ``LANGSMITH_API_KEY``. Los loggers de ``httpx`` y ``httpcore`` quedan en
    ``WARNING`` en cualquier nivel.

    :param settings: Configuración validada
    :type settings: app.config.Settings
    :param api_keys: Claves por cliente ya validadas
    :type api_keys: dict[str, str]
    :param clock: Reloj inyectado
    :type clock: app.clock.Clock
    :param log_stream: Flujo del log JSON; ``None`` usa la salida estándar
    :type log_stream: io.TextIOBase or None
    :return: Log del proceso
    :rtype: app.events.EventLogger
    """
    quiet_third_party_loggers()
    secrets = [*api_keys.values(), settings.cf_api_token, settings.langsmith_api_key]
    logger = EventLogger(
        service=settings.service_name,
        clock=clock,
        stream=log_stream,
        level=settings.log_level,
        redactor=Redactor(secrets),
    )
    _log_startup(logger, settings, api_keys)
    return logger


def _set_or_unset(value):
    """Dice si un secreto está definido, sin mostrarlo.

    :param value: Valor del secreto
    :type value: object
    :return: ``set`` o ``unset``
    :rtype: str
    """
    return SET if value else UNSET


def _log_startup(logger, settings, api_keys):
    """Emite ``startup`` (solo en ``debug``) con el entorno y los secretos.

    De cada secreto solo sale ``NOMBRE=set`` o ``NOMBRE=unset`` en ``credentials``,
    en orden fijo; nunca su valor.

    :param logger: Log JSON del proceso
    :type logger: app.events.EventLogger
    :param settings: Configuración validada
    :type settings: app.config.Settings
    :param api_keys: Claves por cliente ya validadas
    :type api_keys: dict[str, str]
    """
    credentials = [
        f"API_KEYS={_set_or_unset(api_keys)}",
        f"CF_API_TOKEN={_set_or_unset(settings.cf_api_token)}",
        f"LANGSMITH_API_KEY={_set_or_unset(settings.langsmith_api_key)}",
    ]
    logger.debug(
        "startup",
        NO_REQUEST_ID,
        environment=settings.environment,
        model_provider=settings.model_provider,
        log_level=settings.log_level,
        credentials=credentials,
    )


def _build_guard(auth, limiter):
    """Crea la dependencia que protege ``/ask`` y ``/metrics``.

    Primero exige la clave (``401``) y después aplica el límite del cliente
    (``429``). Va como dependencia de ruta, dentro del middleware de observabilidad,
    para que los rechazos también lleven ``X-Request-ID`` y el evento ``request``.

    :param auth: Identificación por clave
    :type auth: app.auth.ApiKeyAuth
    :param limiter: Límite de peticiones por cliente
    :type limiter: app.rate_limit.RateLimiter
    :return: Dependencia de FastAPI que devuelve el nombre del cliente
    :rtype: collections.abc.Callable
    """

    def guard(request: Request):
        """Identifica al cliente y aplica su límite.

        :param request: Petición en curso
        :type request: fastapi.Request
        :return: Nombre del cliente
        :rtype: str
        :raises fastapi.HTTPException: ``401`` sin clave válida, ``429`` si se pasó
        """
        client = auth.require_client(request)
        limiter.enforce(client)
        return client

    return guard


def _models(settings, model, directory):
    """Arma los modelos por nombre.

    :param settings: Configuración validada
    :type settings: app.config.Settings
    :param model: Modelo único inyectado, o ``None``
    :type model: app.llm.LanguageModel or None
    :param directory: Directorio de empleados
    :type directory: app.directory.EmployeeDirectory
    :return: Modelos por nombre
    :rtype: dict[str, app.llm.LanguageModel]
    """
    if model is not None:
        return {settings.model_small: model, settings.model_large: model}
    return build_models(settings, directory)


def _add_error_handlers(application, logger):
    """Convierte una falla del proveedor en ``502`` con el id de la petición.

    El evento ``error`` lleva el tipo de la excepción y, en ``debug``, los frames del
    stack trace; nunca su mensaje.

    :param application: Aplicación donde se registra
    :type application: fastapi.FastAPI
    :param logger: Log JSON del proceso
    :type logger: app.events.EventLogger
    """

    @application.exception_handler(ModelUnavailableError)
    async def model_unavailable(request, error):
        """Responde ``502 {"detail": "model unavailable", "request_id"}``."""
        request_id = request.state.request_id
        client = getattr(request.state, "client", None)
        logger.bind(request_id, client=client).emit(
            "error", **error_fields(logger, error)
        )
        return JSONResponse(
            {"detail": MODEL_UNAVAILABLE_DETAIL, "request_id": request_id},
            status_code=MODEL_UNAVAILABLE_STATUS,
        )


def _add_routes(application, settings, make_agent, metrics, guard):
    """Registra las rutas de la aplicación.

    ``GET /``, ``GET /health`` y ``/docs`` quedan abiertos; ``POST /ask`` y
    ``GET /metrics`` pasan por ``guard`` (clave y límite).

    :param application: Aplicación donde se registran
    :type application: fastapi.FastAPI
    :param settings: Configuración validada
    :type settings: app.config.Settings
    :param make_agent: Crea un ``Agent`` nuevo para un ``request_id``, un cliente y
        una ruta
    :type make_agent: collections.abc.Callable
    :param metrics: Métricas del proceso
    :type metrics: app.metrics.Metrics
    :param guard: Dependencia que exige clave y aplica el límite
    :type guard: collections.abc.Callable
    """
    ask_request = build_ask_request(settings.max_question_chars)
    page = (STATIC_DIR / "index.html").read_text(encoding="utf-8")

    @application.get("/", response_class=HTMLResponse)
    def home():
        """Sirve la página web."""
        return HTMLResponse(page)

    @application.get("/health")
    def health():
        """Informa que el proceso está vivo y su id."""
        return {"status": "ok", "pid": os.getpid()}

    @application.get("/metrics", dependencies=[Depends(guard)])
    def metrics_snapshot():
        """Devuelve las métricas de este proceso."""
        return metrics.snapshot(pid=os.getpid(), slo_p95_ms=settings.slo_p95_ms)

    @application.post("/ask", response_model=AskResponse)
    def ask(body: ask_request, request: Request, client: str = Depends(guard)):
        """Enruta la pregunta y responde con un agente nuevo por petición."""
        request_id = request.state.request_id
        history = [turn.model_dump() for turn in body.history]
        chosen = route(body.question, settings)
        agent = make_agent(request_id, client, chosen)
        result = agent.run(body.question, history=history)
        metrics.add_tokens(
            input_tokens=result.input_tokens, output_tokens=result.output_tokens
        )
        metrics.add_cost(result.cost_usd)
        return AskResponse(
            answer=result.answer,
            steps=result.steps,
            tools_used=list(result.tools_used),
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            request_id=request_id,
            model=chosen.model,
            route=chosen.reason,
            cached_calls=result.cached_calls,
            cost_usd=round(result.cost_usd, COST_DECIMALS),
        )


app = create_app()
