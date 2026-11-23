"""Prueba canario del modo debug: ningún secreto ni pregunta llega a ningún log.

Los secretos tienen valores únicos (canarios). Se corren una pregunta que responde
bien, una clave inválida, un ``500`` forzado y un ``502`` del gateway real con
``httpx.MockTransport`` (por ahí viaja ``Authorization: Bearer <token>``). Se revisa
todo lo capturado: el log JSON, el logging estándar (``caplog``) y la consola
(``capsys``), en nivel ``DEBUG``.
"""

import io
import json
import logging
import re

import httpx
from conftest import CF_ENV, FailingModel, FakeClock, gateway_reply
from fastapi.testclient import TestClient

CANARY_API_KEY = "canary-api-key-0001"
CANARY_CF_TOKEN = "canary-cf-token-0001"
CANARY_LANGSMITH = "canary-langsmith-0001"
CANARY_WRONG_KEY = "canary-wrong-key-0001"
CANARIES = (CANARY_API_KEY, CANARY_CF_TOKEN, CANARY_LANGSMITH, CANARY_WRONG_KEY)
# Las preguntas son más largas que cualquier argumento de herramienta.
GOOD_QUESTION = "¿Quién es EMP-0004 y desde cuándo trabaja en la empresa?"
FAILING_QUESTION = "Pregunta canario que fuerza un error interno del asistente"
GATEWAY_QUESTION = "Pregunta canario que hace fallar al gateway con un 502"
QUESTIONS = (GOOD_QUESTION, FAILING_QUESTION, GATEWAY_QUESTION)
GOOD_ANSWER = "Jorge Díaz es Líder técnico en Tecnología desde 2022."
LEAKED_BEARER = re.compile(r"Bearer (?!\[REDACTED\])")
THIRD_PARTY_LOGGERS = ("httpx", "httpcore")


def _canary_env(cost_env):
    """Variables con secretos canario y ``LOG_LEVEL=debug``.

    :rtype: dict
    """
    return {
        **cost_env,
        **CF_ENV,
        "MODEL_PROVIDER": "gateway",
        "SERVICE_NAME": "hr-canary",
        "API_KEYS": f"acme:{CANARY_API_KEY}",
        "CF_API_TOKEN": CANARY_CF_TOKEN,
        "LANGSMITH_API_KEY": CANARY_LANGSMITH,
        "LOG_LEVEL": "debug",
    }


def _gateway_handler(seen_authorizations):
    """Red simulada del gateway: pide una herramienta, responde o falla con ``502``.

    El ``502`` devuelve el token en su cuerpo, como haría un proxy descuidado.

    :param seen_authorizations: Lista donde se guarda cada ``Authorization``
    :type seen_authorizations: list[str]
    :rtype: collections.abc.Callable
    """
    # pylint: disable=import-outside-toplevel
    from app.llm import TOOL_RESULT_PREFIX

    def handler(request):
        seen_authorizations.append(request.headers.get("Authorization"))
        last = json.loads(request.content)["messages"][-1]["content"]
        if GATEWAY_QUESTION in last:
            return httpx.Response(502, text=f"bad gateway for Bearer {CANARY_CF_TOKEN}")
        if last.startswith(TOOL_RESULT_PREFIX):
            return gateway_reply(json.dumps({"answer": GOOD_ANSWER}))
        reply = {"tool": "get_employee", "args": {"employee_id": "EMP-0004"}}
        return gateway_reply(json.dumps(reply))

    return handler


def _start(settings, models, directory, stream):
    """Arranca una app con el log en ``stream`` y un cliente HTTP sin clave fija.

    :rtype: fastapi.testclient.TestClient
    """
    # pylint: disable=import-outside-toplevel
    from app.main import create_app

    app = create_app(
        settings=settings,
        models=models,
        directory=directory,
        clock=FakeClock(),
        log_stream=stream,
    )
    return TestClient(app, raise_server_exceptions=False)


def test_no_canary_bearer_or_question_reaches_any_log_in_debug(
    cost_env, directory, caplog, capsys
):
    # pylint: disable=too-many-locals,import-outside-toplevel
    from app.config import load_settings
    from app.gateway import GatewayModel

    caplog.set_level(logging.DEBUG)
    for name in THIRD_PARTY_LOGGERS:
        caplog.set_level(logging.DEBUG, logger=name)
    settings = load_settings(_canary_env(cost_env))
    names = (settings.model_small, settings.model_large)
    seen_authorizations = []
    transport = httpx.MockTransport(_gateway_handler(seen_authorizations))
    http_client = httpx.Client(transport=transport)
    gateway_models = {
        name: GatewayModel(name, settings, http_client) for name in names
    }
    failing_models = {name: FailingModel() for name in names}
    stream = io.StringIO()
    gateway_app = _start(settings, gateway_models, directory, stream)
    failing_app = _start(settings, failing_models, directory, stream)
    good_key = {"X-API-Key": CANARY_API_KEY}
    wrong_key = {
        "X-API-Key": CANARY_WRONG_KEY,
        "Authorization": f"Bearer {CANARY_WRONG_KEY}",
    }

    statuses = [
        gateway_app.post(
            "/ask", json={"question": GOOD_QUESTION}, headers=good_key
        ).status_code,
        gateway_app.post(
            "/ask", json={"question": GOOD_QUESTION}, headers=wrong_key
        ).status_code,
        failing_app.post(
            "/ask", json={"question": FAILING_QUESTION}, headers=good_key
        ).status_code,
        gateway_app.post(
            "/ask", json={"question": GATEWAY_QUESTION}, headers=good_key
        ).status_code,
    ]

    assert statuses == [200, 401, 500, 502]
    assert f"Bearer {CANARY_CF_TOKEN}" in seen_authorizations
    log = stream.getvalue()
    events = [json.loads(line) for line in log.splitlines() if line.strip()]
    names_seen = {event["event"] for event in events}
    assert {"startup", "agent_step", "model_call", "error"} <= names_seen
    assert all(event["frames"] for event in events if event["event"] == "error")
    console = capsys.readouterr()
    captured = "\n".join([log, caplog.text, console.out, console.err])
    for canary in CANARIES:
        assert canary not in captured, canary
    assert not LEAKED_BEARER.search(captured)
    for question in QUESTIONS:
        assert question not in captured, question
    assert GOOD_ANSWER not in captured


def test_httpx_and_httpcore_stay_at_warning_even_in_debug(make_debug_app, caplog):
    for name in THIRD_PARTY_LOGGERS:
        caplog.set_level(logging.DEBUG, logger=name)

    make_debug_app(log_level="debug")

    for name in THIRD_PARTY_LOGGERS:
        assert logging.getLogger(name).level == logging.WARNING
