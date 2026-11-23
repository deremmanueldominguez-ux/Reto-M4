"""Pasos de los escenarios de ``features/observability.feature``.

La app se arma con un reloj falso y el log se captura en memoria, así cada escenario
puede leer los eventos JSON que produjo su petición.
"""

import uuid

from pytest_bdd import given, parsers, scenarios, then, when

scenarios("features/observability.feature")

QUESTION = "¿Quién es EMP-0004?"
# Debe coincidir con ``FailingModel.SECRET`` de ``conftest.py``.
FAILURE_SECRET = "secret-failure-details"


@given("the observed HR assistant is running", target_fixture="observed")
def observed_assistant(make_observed_app):
    """El asistente con reloj falso y log capturado."""
    return make_observed_app()


@given(
    "the observed HR assistant is running with a failing model",
    target_fixture="observed",
)
def observed_assistant_with_failing_model(make_observed_app):
    """El asistente con un modelo que siempre lanza una excepción."""
    return make_observed_app(failing=True)


@given(
    parsers.parse(
        "the observed HR assistant is running with a model that takes {delay:d} ms "
        "and an SLO of {slo:d} ms"
    ),
    target_fixture="observed",
)
def observed_assistant_with_slow_model(make_observed_app, delay, slo):
    """El asistente con un modelo que tarda ``delay`` ms por llamada."""
    return make_observed_app(model_delay_ms=delay, slo_p95_ms=slo)


@when("I check the health without a request id", target_fixture="response")
def check_health(observed):
    """Pide ``/health`` sin encabezado ``X-Request-ID``."""
    return observed.client.get("/health")


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
    parsers.parse('I send an empty question with request id "{request_id}"'),
    target_fixture="response",
)
def ask_empty_with_request_id(observed, request_id):
    """Envía una pregunta vacía con un ``X-Request-ID`` propio."""
    return observed.client.post(
        "/ask", json={"question": ""}, headers={"X-Request-ID": request_id}
    )


@when(parsers.parse('I ask "{question}" twice'), target_fixture="responses")
def ask_twice(observed, question):
    """Envía la misma pregunta en dos peticiones."""
    return [observed.client.post("/ask", json={"question": question}) for _ in "ab"]


@when("I request the metrics", target_fixture="metrics")
def request_metrics(observed, responses):
    """Pide ``/metrics`` después de que las preguntas respondieron bien."""
    assert [response.status_code for response in responses] == [200, 200]
    response = observed.client.get("/metrics")
    assert response.status_code == 200
    return response.json()


@then(parsers.parse("the response status is {status:d}"))
def response_status_is(response, status):
    """Comprueba el código HTTP."""
    assert response.status_code == status


@then("the response carries a generated UUID request id")
def response_has_generated_uuid(response):
    """El id generado es un UUID versión 4."""
    assert uuid.UUID(response.headers["X-Request-ID"]).version == 4


@then(parsers.parse('the response header request id is "{request_id}"'))
def header_request_id_is(response, request_id):
    """Comprueba el encabezado ``X-Request-ID``."""
    assert response.headers["X-Request-ID"] == request_id


@then(parsers.parse('the response body request id is "{request_id}"'))
def body_request_id_is(response, request_id):
    """Comprueba el campo ``request_id`` del cuerpo, sin perder los de la sesión 1."""
    body = response.json()
    assert body["request_id"] == request_id
    assert body["tools_used"] == ["get_employee"]


@then(
    parsers.parse(
        'the log has one "audit" event for tool "{tool}" with request id "{request_id}"'
    )
)
def log_has_one_audit(observed, tool, request_id):
    """Un ``audit`` por herramienta, con sus argumentos."""
    audits = observed.events("audit")
    assert len(audits) == 1
    audit = audits[0]
    assert audit["request_id"] == request_id
    assert audit["service"] == "hr-test"
    assert (audit["action"], audit["tool"]) == ("tool_call", tool)
    assert audit["args"] == {"employee_id": "EMP-0004"}


@then(parsers.parse('the log has one "agent_run" event with request id "{request_id}"'))
def log_has_one_agent_run(observed, request_id):
    """El ``agent_run`` lleva conteos, no texto."""
    runs = observed.events("agent_run")
    assert len(runs) == 1
    run = runs[0]
    assert run["request_id"] == request_id
    assert run["question_chars"] == len(QUESTION)
    assert run["history_messages"] == 0
    assert (run["steps"], run["tools"], run["stopped"]) == (
        2,
        ["get_employee"],
        "answer",
    )
    assert run["input_tokens"] > 0 and run["output_tokens"] > 0


@then(
    parsers.parse(
        'the log has a "request" event for "{method}" "{path}" with status '
        '{status:d} and request id "{request_id}"'
    )
)
def log_has_request_event(observed, method, path, status, request_id):
    """El evento ``request`` cierra cada petición con su latencia."""
    requests = [
        event
        for event in observed.events("request")
        if event["request_id"] == request_id
    ]
    assert len(requests) == 1
    event = requests[0]
    assert (event["method"], event["path"], event["status"]) == (method, path, status)
    assert isinstance(event["latency_ms"], (int, float))
    assert event["ts"].endswith("Z")


@then("no log line contains the question, the answer or the employee data")
def log_has_no_text(observed, response):
    """Privacidad: el log no guarda la pregunta, la respuesta ni los datos."""
    log = observed.raw_log()
    assert QUESTION not in log
    assert response.json()["answer"] not in log
    assert "Jorge Díaz" not in log


@then(
    parsers.parse(
        'the response body is the internal error for request id "{request_id}"'
    )
)
def body_is_internal_error(response, request_id):
    """El ``500`` no da detalles y lleva el id para soporte."""
    assert response.json() == {"detail": "internal error", "request_id": request_id}
    assert response.headers["X-Request-ID"] == request_id


@then(
    parsers.parse(
        'the log has an "error" event of type "{error_type}" with request id '
        '"{request_id}"'
    )
)
def log_has_error_event(observed, error_type, request_id):
    """El evento ``error`` guarda solo el tipo de la excepción."""
    errors = observed.events("error")
    assert len(errors) == 1
    assert errors[0]["error_type"] == error_type
    assert errors[0]["request_id"] == request_id


@then("no log line contains the failure message")
def log_has_no_failure_message(observed, response):
    """Ni el mensaje de la excepción ni la respuesta la exponen."""
    assert FAILURE_SECRET not in observed.raw_log()
    assert FAILURE_SECRET not in response.text


@then(parsers.parse("the metrics count at least {count:d} requests and no errors"))
def metrics_count_requests(metrics, count):
    """Cuenta las peticiones del proceso."""
    assert metrics["requests"] >= count
    assert metrics["error_rate"] == 0.0


@then("the metrics report input and output tokens above zero")
def metrics_report_tokens(metrics):
    """Suma los tokens de las corridas del agente."""
    assert metrics["tokens"]["input"] > 0
    assert metrics["tokens"]["output"] > 0


@then(parsers.parse("the metrics p95 latency is {p95:d} ms"))
def metrics_p95_is(metrics, p95):
    """La latencia sale del reloj falso: dos llamadas al modelo por pregunta."""
    assert float(metrics["latency_ms"]["p95"]) == float(p95)


@then(parsers.parse("the metrics say the SLO met is {met}"))
def metrics_slo_met_is(metrics, met):
    """``met`` compara el p95 con ``SLO_P95_MS``."""
    assert metrics["slo"] == {"p95_ms_target": 2000, "met": met == "true"}
