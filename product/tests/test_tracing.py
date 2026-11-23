"""Pruebas de las trazas opcionales en LangSmith, sin red y sin la librería real."""

import importlib
import sys


def lookup(employee_id):
    """Herramienta de ejemplo que se envuelve."""
    return {"id": employee_id}


def test_disabled_tracer_returns_the_same_function_and_never_imports_langsmith(
    monkeypatch,
):
    monkeypatch.delitem(sys.modules, "langsmith", raising=False)
    monkeypatch.delitem(sys.modules, "app.tracing", raising=False)
    tracing = importlib.import_module("app.tracing")

    tracer = tracing.Tracer(enabled=False)
    wrapped = tracer.wrap(lookup, name="get_employee", run_type="tool", request_id="r")

    assert wrapped is lookup
    assert "langsmith" not in sys.modules


def test_enabled_tracer_sends_the_request_id_and_hides_the_configured_data():
    clients = []
    decorations = []

    def client_factory(**options):
        clients.append(options)
        return "fake-client"

    def traceable(**options):
        decorations.append(options)
        return lambda function: function

    # pylint: disable=import-outside-toplevel
    from app.tracing import Tracer

    tracer = Tracer(
        enabled=True,
        hide_inputs=True,
        hide_outputs=False,
        traceable=traceable,
        client_factory=client_factory,
    )
    wrapped = tracer.wrap(
        lookup, name="get_employee", run_type="tool", request_id="trace-42"
    )

    assert wrapped("EMP-0001") == {"id": "EMP-0001"}
    assert clients == [{"hide_inputs": True, "hide_outputs": False}]
    assert len(decorations) == 1
    options = decorations[0]
    assert (options["name"], options["run_type"]) == ("get_employee", "tool")
    assert options["metadata"] == {"request_id": "trace-42"}
    assert options["client"] == "fake-client"


# Sesión 4: el nombre del cliente va en los metadatos; la clave nunca llega al trazador.


def test_bound_trace_metadata_names_the_client_and_the_request_id():
    decorations = []

    def traceable(**options):
        decorations.append(options)
        return lambda function: function

    # pylint: disable=import-outside-toplevel
    from app.tracing import Tracer

    tracer = Tracer(
        enabled=True, traceable=traceable, client_factory=lambda **_: "fake-client"
    )
    trace = tracer.bind("trace-7", client="acme")
    wrapped = trace(lookup, name="get_employee", run_type="tool")

    assert wrapped("EMP-0001") == {"id": "EMP-0001"}
    assert decorations[0]["metadata"] == {"request_id": "trace-7", "client": "acme"}
