"""Pasos de los escenarios de ``features/debug.feature``.

Cada escenario arma la app con ``make_debug_app`` (reloj falso y log en memoria). El
gateway que falla es el ``GatewayModel`` real con ``httpx.MockTransport``: no usa red.
"""

import re

import httpx
import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from conftest import ACME_KEY, CF_ENV, GLOBEX_KEY, TEST_API_KEY

scenarios("features/debug.feature")

QUESTION = "¿Quién es EMP-0004?"
COMMON_FIELDS = {"ts", "service", "event", "request_id"}
# ``client`` lo agrega el log de la petición desde la sesión 4.
REQUEST_FIELDS = COMMON_FIELDS | {"client"}
SESSION_2_FIELDS = {
    "audit": {"action", "tool", "args"},
    "agent_run": {
        "question_chars",
        "history_messages",
        "steps",
        "tools",
        "input_tokens",
        "output_tokens",
        "stopped",
        "model",
        "route",
        "cached_calls",
        "cost_usd",
    },
    "request": {"method", "path", "status", "latency_ms"},
}
DEBUG_FIELDS = {
    "agent_step": {"step", "tools", "latency_ms"},
    "model_call": {
        "model",
        "status",
        "latency_ms",
        "input_tokens",
        "output_tokens",
        "cached",
    },
}
STARTUP_FIELDS = COMMON_FIELDS | {
    "environment",
    "model_provider",
    "log_level",
    "credentials",
}
# ``archivo.py:línea:función``, con el nombre corto del archivo (sin carpetas).
FRAME_PATTERN = re.compile(r"^[^/\\:]+\.py:\d+:[^:\s]+$")
# Textos que nunca deben llegar al log cuando algo falla.
FAILURE_TEXTS = (
    "secret-failure-details",  # ``FailingModel.SECRET`` de ``conftest.py``
    "upstream failure",  # cuerpo de la respuesta del gateway
    "gateway returned status",  # mensaje de ``ModelUnavailableError``
)
GATEWAY_FAILURE_STATUS = 502


def _failing_gateway_models(settings):
    """Modelos del gateway real cuya red responde siempre ``502``.

    :param settings: Configuración validada
    :type settings: app.config.Settings
    :return: Modelos por nombre
    :rtype: dict[str, app.gateway.GatewayModel]
    """
    # pylint: disable=import-outside-toplevel
    from app.gateway import GatewayModel

    def handler(request):  # pylint: disable=unused-argument
        return httpx.Response(GATEWAY_FAILURE_STATUS, text="upstream failure")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    names = (settings.model_small, settings.model_large)
    return {name: GatewayModel(name, settings, client) for name in names}


@given(
    parsers.parse('the HR assistant is running with log level "{level}"'),
    target_fixture="observed",
)
def assistant_with_level(make_debug_app, level):
    """El asistente con el ``LOG_LEVEL`` del escenario."""
    return make_debug_app(log_level=level)


@given(
    parsers.parse(
        'the HR assistant is running with log level "{level}" and a model that '
        "takes {delay:d} ms"
    ),
    target_fixture="observed",
)
def assistant_with_slow_model(make_debug_app, level, delay):
    """El asistente con un modelo que tarda ``delay`` ms en el reloj falso."""
    return make_debug_app(log_level=level, model_delay_ms=delay)


@given(
    parsers.parse(
        'the HR assistant is running with log level "{level}" and a failing model'
    ),
    target_fixture="observed",
)
def assistant_with_failing_model(make_debug_app, level):
    """El asistente con un modelo que lanza ``RuntimeError`` (da ``500``)."""
    return make_debug_app(log_level=level, failing=True)


@given(
    parsers.parse(
        'the HR assistant is running with log level "{level}" and a gateway that fails'
    ),
    target_fixture="observed",
)
def assistant_with_failing_gateway(make_debug_app, level):
    """El asistente con el gateway real respondiendo ``502`` (da ``502``)."""
    return make_debug_app(
        log_level=level,
        models_factory=_failing_gateway_models,
        **{**CF_ENV, "MODEL_PROVIDER": "gateway"},
    )


@given("a production environment that follows every rule", target_fixture="env")
def production_environment(production_env):
    """Variables de producción que cumplen todas las reglas de la sesión 4."""
    return dict(production_env)


@when(
    parsers.parse('I ask "{question}" with request id "{request_id}"'),
    target_fixture="response",
)
def ask_with_request_id(observed, question, request_id):
    """Envía una pregunta con un ``X-Request-ID`` propio."""
    return observed.client.post(
        "/ask", json={"question": question}, headers={"X-Request-ID": request_id}
    )


@when(
    parsers.parse('the assistant starts with LOG_LEVEL "{level}"'),
    target_fixture="start_error",
)
def start_with_log_level(make_debug_app, level):
    """Intenta arrancar con un nivel de log desconocido."""
    # pylint: disable=import-outside-toplevel
    from app.config import ConfigError

    with pytest.raises(ConfigError) as error:
        make_debug_app(log_level=level)
    return error.value


@when(
    parsers.parse('the assistant starts in production with LOG_LEVEL "{level}"'),
    target_fixture="start_error",
)
def start_production_with_log_level(start_assistant, env, level):
    """Intenta arrancar en producción con el nivel de log dado."""
    # pylint: disable=import-outside-toplevel
    from app.config import ConfigError

    with pytest.raises(ConfigError) as error:
        start_assistant({**env, "LOG_LEVEL": level})
    return error.value


@then(parsers.parse("the response status is {status:d}"))
def response_status_is(response, status):
    """Comprueba el código HTTP."""
    assert response.status_code == status


@then(
    'the log has only the "audit", "agent_run" and "request" events with their '
    "session 2 fields"
)
def log_is_the_session_2_log(observed):
    """En ``info`` no hay eventos nuevos ni campos nuevos."""
    events = observed.events()
    assert [event["event"] for event in events] == ["audit", "agent_run", "request"]
    for event in events:
        assert set(event) == REQUEST_FIELDS | SESSION_2_FIELDS[event["event"]]
    assert events[0]["args"] == {"employee_id": "EMP-0004"}


@then("the log is identical to the log of an assistant without LOG_LEVEL")
def log_matches_the_default(observed, make_debug_app):
    """``info`` es el valor por omisión: el log sale idéntico, línea por línea."""
    default = make_debug_app(log_level=None)
    default.client.post(
        "/ask", json={"question": QUESTION}, headers={"X-Request-ID": "req-info-1"}
    )
    assert observed.raw_log() == default.raw_log()


@then(
    parsers.parse('the log has {count:d} "agent_step" events that took {ms:d} ms each')
)
def agent_steps_are_logged(observed, count, ms):
    """Un ``agent_step`` por paso, numerado, con sus herramientas y su latencia."""
    steps = observed.events("agent_step")
    assert len(steps) == count
    assert [step["step"] for step in steps] == list(range(1, count + 1))
    assert [step["tools"] for step in steps] == [["get_employee"], []]
    assert [float(step["latency_ms"]) for step in steps] == [float(ms)] * count
    assert {step["request_id"] for step in steps} == {"req-debug-1"}


@then(
    parsers.parse(
        'the log has {count:d} "model_call" events with status "{status}" that took '
        "{ms:d} ms each"
    )
)
def model_calls_are_logged(observed, count, status, ms):
    """Un ``model_call`` por llamada al modelo, con tokens y caché."""
    calls = observed.events("model_call")
    assert len(calls) == count
    for call in calls:
        assert call["status"] == status
        assert float(call["latency_ms"]) == float(ms)
        assert call["input_tokens"] > 0 and call["output_tokens"] > 0
        assert call["cached"] is False
        assert isinstance(call["model"], str) and call["model"]


@then("every debug event carries only its whitelisted fields")
def debug_events_are_whitelisted(observed):
    """Cada evento de debug lleva sus campos y nada más."""
    for name, fields in DEBUG_FIELDS.items():
        events = observed.events(name)
        assert events, f"no {name} event"
        for event in events:
            assert fields <= set(event)
            assert set(event) <= REQUEST_FIELDS | fields


@then("no log line contains the question, the answer or the employee data")
def log_has_no_text(observed, response):
    """Más detalle no significa más datos: ni pregunta, ni respuesta, ni empleado."""
    log = observed.raw_log()
    assert QUESTION not in log
    assert response.json()["answer"] not in log
    assert "Jorge Díaz" not in log


@then(parsers.parse('the log has one "startup" event with request id "{request_id}"'))
def log_has_startup(observed, request_id):
    """El arranque deja un solo ``startup``, sin petición."""
    startups = observed.events("startup")
    assert len(startups) == 1
    assert startups[0]["request_id"] == request_id
    assert set(startups[0]) == STARTUP_FIELDS


@then("the startup event describes the environment, the provider and the log level")
def startup_describes_the_process(observed):
    """``startup`` dice dónde y cómo arrancó el proceso."""
    startup = observed.events("startup")[0]
    assert (
        startup["environment"],
        startup["model_provider"],
        startup["log_level"],
    ) == ("development", "fake", "debug")


@then(
    parsers.parse(
        'the startup credentials are "{api_keys}", "{cf_token}" and "{langsmith}"'
    )
)
def startup_credentials_are(observed, api_keys, cf_token, langsmith):
    """Cada secreto aparece solo como ``set`` o ``unset``."""
    startup = observed.events("startup")[0]
    assert startup["credentials"] == [api_keys, cf_token, langsmith]


@then("no log line contains the API key of the test client")
def log_has_no_api_key(observed):
    """El valor de ``API_KEYS`` nunca llega al log."""
    assert TEST_API_KEY not in observed.raw_log()


@then(
    parsers.parse(
        'the log has an "error" event of type "{error_type}" with stack frames'
    )
)
def error_has_frames(observed, error_type):
    """El ``error`` lleva el tipo y los frames, nunca el mensaje."""
    errors = observed.events("error")
    assert len(errors) == 1
    error = errors[0]
    assert error["error_type"] == error_type
    assert error["request_id"] == "req-fail-1"
    frames = error["frames"]
    assert frames, "the error event has no frames"
    for frame in frames:
        assert FRAME_PATTERN.match(frame), frame
    assert any(frame.endswith(":complete") for frame in frames)


@then("no log line contains the failure message")
def log_has_no_failure_message(observed, response):
    """Ni el mensaje de la excepción, ni el cuerpo del gateway, ni la pregunta."""
    log = observed.raw_log()
    for text in FAILURE_TEXTS:
        assert text not in log
        assert text not in response.text
    assert QUESTION not in log


@then("the start fails with a configuration error about LOG_LEVEL")
def start_error_names_log_level(start_error):
    """El error nombra la variable que hay que corregir."""
    assert "LOG_LEVEL" in str(start_error)


@then("the start fails with a configuration error that does not show any key")
def start_error_hides_keys(start_error):
    """La regla de producción se explica sin escribir ninguna clave."""
    message = str(start_error)
    assert "LOG_LEVEL" in message
    for secret in (ACME_KEY, GLOBEX_KEY, CF_ENV["CF_API_TOKEN"]):
        assert secret not in message
