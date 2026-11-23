"""Middleware HTTP de observabilidad: id, latencia, errores y métricas."""

from fastapi.responses import JSONResponse

from app.events import stack_frames
from app.request_id import REQUEST_ID_HEADER, resolve_request_id

INTERNAL_ERROR_STATUS = 500
INTERNAL_ERROR_DETAIL = "internal error"
LATENCY_DECIMALS = 1
MILLIS_PER_SECOND = 1000


def error_fields(logger, error):
    """Campos del evento ``error``: el tipo y, en ``debug``, los frames.

    Nunca lleva el mensaje de la excepción ni sus variables locales.

    :param logger: Log JSON del proceso
    :type logger: app.events.EventLogger
    :param error: Excepción capturada
    :type error: BaseException
    :return: ``error_type`` y, con ``debug``, ``frames``
    :rtype: dict
    """
    fields = {"error_type": type(error).__name__}
    if logger.debug_enabled:
        fields["frames"] = stack_frames(error)
    return fields


def _request_log(logger, request):
    """Log de la petición ligado a su id y, si ya se identificó, a su cliente.

    La dependencia de clave deja en ``request.state.client`` solo el nombre del
    cliente, nunca la clave.

    :param logger: Log JSON del proceso
    :type logger: app.events.EventLogger
    :param request: Petición en curso
    :type request: starlette.requests.Request
    :return: Log de la petición
    :rtype: app.events.RequestLog
    """
    client = getattr(request.state, "client", None)
    return logger.bind(request.state.request_id, client=client)


def install_observability(application, clock, logger, metrics):
    """Instala el middleware que observa cada petición.

    Fija el id de la petición en ``request.state.request_id``, mide la latencia con
    ``clock.monotonic()``, convierte cualquier excepción en un ``500`` con el id y
    el evento ``error`` (el tipo y, en ``debug``, los frames), emite ``request``
    (con ``client`` si la petición se identificó con su clave), registra en
    ``metrics`` y pone ``X-Request-ID`` en toda respuesta.

    :param application: Aplicación donde se instala
    :type application: fastapi.FastAPI
    :param clock: Reloj inyectado
    :type clock: app.clock.Clock
    :param logger: Log JSON del proceso
    :type logger: app.events.EventLogger
    :param metrics: Métricas del proceso
    :type metrics: app.metrics.Metrics
    """

    @application.middleware("http")
    async def observe(request, call_next):
        """Observa una petición de principio a fin."""
        request_id = resolve_request_id(request.headers.get(REQUEST_ID_HEADER))
        request.state.request_id = request_id
        started = clock.monotonic()
        try:
            response = await call_next(request)
        except Exception as error:  # pylint: disable=broad-exception-caught
            _request_log(logger, request).emit("error", **error_fields(logger, error))
            response = JSONResponse(
                {"detail": INTERNAL_ERROR_DETAIL, "request_id": request_id},
                status_code=INTERNAL_ERROR_STATUS,
            )
        elapsed = (clock.monotonic() - started) * MILLIS_PER_SECOND
        latency_ms = round(elapsed, LATENCY_DECIMALS)
        response.headers[REQUEST_ID_HEADER] = request_id
        _request_log(logger, request).emit(
            "request",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            latency_ms=latency_ms,
        )
        metrics.record_request(status=response.status_code, latency_ms=latency_ms)
        return response
