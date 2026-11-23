"""Pasos de los escenarios de ``features/security.feature``.

Las claves de ``conftest.py`` son textos de ejemplo. El límite de peticiones usa el
reloj falso, así los escenarios avanzan un minuto sin esperar.
"""

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from conftest import ACME_KEY, GLOBEX_KEY

scenarios("features/security.feature")

CLIENT_KEYS = {"acme": ACME_KEY, "globex": GLOBEX_KEY}
INVALID_KEY_BODY = {"detail": "invalid or missing API key"}
RATE_LIMIT_BODY = {"detail": "rate limit exceeded"}
SHORT_KEY = "abcdefghijklmno"
# Cada fila del ejemplo de compliance se traduce a las variables que la rompen.
UNSAFE_SETTINGS = {
    ("MODEL_PROVIDER", "fake"): {"MODEL_PROVIDER": "fake"},
    ("API_KEYS", "(empty)"): {"API_KEYS": ""},
    ("API_KEYS", f"acme:{SHORT_KEY}"): {"API_KEYS": f"acme:{SHORT_KEY}"},
    ("LANGSMITH_TRACING", "true and inputs shown"): {
        "LANGSMITH_TRACING": "true",
        "HIDE_INPUTS": "false",
    },
}


@given("the secure HR assistant is running", target_fixture="secure")
def secure_assistant(make_secure_app):
    """El asistente con los clientes ``acme`` y ``globex``."""
    return make_secure_app()


@given(
    parsers.parse(
        "the secure HR assistant is running with a limit of {limit:d} requests "
        "per minute"
    ),
    target_fixture="secure",
)
def secure_assistant_with_limit(make_secure_app, limit):
    """El asistente con ``RATE_LIMIT_PER_MINUTE`` bajo para el escenario."""
    return make_secure_app(rate_limit=limit)


@given("a production environment that follows every rule", target_fixture="env")
def production_environment(production_env):
    """Variables de producción que cumplen todas las reglas."""
    return dict(production_env)


@when(parsers.parse('client "{client}" asks "{question}"'), target_fixture="response")
def client_asks(secure, client, question):
    """Envía una pregunta con la clave del cliente."""
    return secure.client.post(
        "/ask", json={"question": question}, headers={"X-API-Key": CLIENT_KEYS[client]}
    )


@when(
    parsers.parse('client "{client}" asks "{question}" {times:d} times'),
    target_fixture="response",
)
def client_asks_many_times(secure, client, question, times):
    """Envía la misma pregunta varias veces; todas deben responder bien."""
    headers = {"X-API-Key": CLIENT_KEYS[client]}
    responses = [
        secure.client.post("/ask", json={"question": question}, headers=headers)
        for _ in range(times)
    ]
    assert [response.status_code for response in responses] == [200] * times
    return responses[-1]


@when(
    parsers.parse('someone asks "{question}" without a key'), target_fixture="response"
)
def ask_without_key(secure, question):
    """Envía una pregunta sin el encabezado ``X-API-Key``."""
    return secure.client.post("/ask", json={"question": question})


@when(
    parsers.parse('someone asks "{question}" with the wrong key "{key}"'),
    target_fixture="rejected",
)
def ask_with_wrong_key(secure, question, key):
    """Envía una pregunta con una clave que no existe."""
    response = secure.client.post(
        "/ask", json={"question": question}, headers={"X-API-Key": key}
    )
    assert response.status_code == 401
    return response


@when(
    parsers.parse('someone calls "{method}" "{path}" with the key "{key}"'),
    target_fixture="response",
)
def call_with_key(secure, method, path, key):
    """Llama una ruta protegida; ``none`` significa sin encabezado."""
    headers = {} if key == "none" else {"X-API-Key": key}
    body = {"question": "Hola"} if method == "POST" else None
    return secure.client.request(method, path, json=body, headers=headers)


@when(parsers.parse('someone opens "{path}" without a key'), target_fixture="response")
def open_without_key(secure, path):
    """Abre una ruta pública sin clave."""
    return secure.client.get(path)


@when(parsers.parse("{seconds:d} seconds pass"))
def seconds_pass(secure, seconds):
    """Avanza el reloj falso que usa el límite de peticiones."""
    secure.clock.advance(seconds)


@when(
    parsers.parse('the assistant starts with "{variable}" set to "{value}"'),
    target_fixture="start_error",
)
def start_with_unsafe_setting(start_assistant, env, variable, value):
    """Intenta arrancar con una sola regla de compliance rota."""
    # pylint: disable=import-outside-toplevel
    from app.config import ConfigError

    unsafe = {**env, **UNSAFE_SETTINGS[(variable, value)]}
    with pytest.raises(ConfigError) as error:
        start_assistant(unsafe)
    return error.value


@when("the assistant starts", target_fixture="started")
def start_safely(start_assistant, env):
    """Arranca con la configuración de producción correcta."""
    return start_assistant(env)


@then(parsers.parse("the response status is {status:d}"))
def response_status_is(response, status):
    """Comprueba el código HTTP."""
    assert response.status_code == status


@then("the response carries a request id")
def response_has_request_id(response):
    """También las respuestas rechazadas llevan ``X-Request-ID``."""
    assert response.headers["X-Request-ID"]


@then("the response body says the API key is invalid or missing")
def body_is_invalid_key(response):
    """El ``401`` es igual con clave equivocada o sin clave."""
    assert response.json() == INVALID_KEY_BODY


@then(parsers.parse('the response does not contain the key "{key}"'))
def response_hides_key(response, key):
    """El mensaje de error no repite la clave recibida."""
    assert key not in response.text


@then("the response body says the rate limit was exceeded")
def body_is_rate_limited(response):
    """Cuerpo del ``429``."""
    assert response.json() == RATE_LIMIT_BODY


@then(parsers.parse("the response asks to retry after {seconds:d} seconds"))
def retry_after_is(response, seconds):
    """``Retry-After`` dice los segundos que faltan para liberar la ventana."""
    assert response.headers["Retry-After"] == str(seconds)


@then(
    parsers.parse(
        'the "request", "agent_run" and "audit" events name the client "{client}"'
    )
)
def events_name_the_client(secure, client):
    """La petición respondida queda ligada a su cliente en los tres eventos."""
    for name in ("agent_run", "audit"):
        events = secure.events(name)
        assert events, f"no {name} event"
        assert {event["client"] for event in events} == {client}
    answered = [event for event in secure.events("request") if event["status"] == 200]
    assert [event["client"] for event in answered] == [client]


@then(parsers.parse('no log line contains "{wrong_key}" or the key of "{client}"'))
def log_hides_keys(secure, rejected, wrong_key, client):
    """Ni la clave buena ni la equivocada llegan al log o a la respuesta."""
    log = secure.raw_log()
    assert wrong_key not in log
    assert CLIENT_KEYS[client] not in log
    assert wrong_key not in rejected.text


@then("the start fails with a configuration error that does not show any key")
def start_error_hides_keys(start_error):
    """El error explica la regla sin escribir ninguna clave."""
    message = str(start_error)
    assert message
    for key in (ACME_KEY, GLOBEX_KEY, SHORT_KEY):
        assert key not in message


@then(
    parsers.parse('client "{client}" can ask "{question}" and gets status {status:d}')
)
def started_assistant_answers(started, client, question, status):
    """El asistente de producción responde con clave."""
    response = started.post(
        "/ask", json={"question": question}, headers={"X-API-Key": CLIENT_KEYS[client]}
    )
    assert response.status_code == status
