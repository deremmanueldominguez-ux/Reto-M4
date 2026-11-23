"""Pasos de los escenarios de ``features/costs.feature``.

Los precios de prueba (``conftest.py``) son números redondos para que el costo esperado
se pueda calcular a mano. El gateway se simula con ``httpx.MockTransport``: sin red.
"""

import httpx
import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from conftest import CF_ENV, LARGE_MODEL, SMALL_MODEL, gateway_reply

scenarios("features/costs.feature")

PRICES = {SMALL_MODEL: (1.0, 2.0), LARGE_MODEL: (10.0, 20.0)}
COST_DECIMALS = 8


def _history(count):
    """Arma ``count`` turnos alternados de usuario y asistente.

    :param count: Número de mensajes
    :type count: int
    :rtype: list[dict]
    """
    roles = ("user", "assistant")
    return [
        {"role": roles[index % 2], "content": f"Mensaje anterior número {index}"}
        for index in range(count)
    ]


def _gateway_models(handler):
    """Devuelve una fábrica de modelos del gateway que usan ``handler`` como red.

    :param handler: Función que recibe ``httpx.Request`` y devuelve la respuesta
    :type handler: collections.abc.Callable
    :rtype: collections.abc.Callable
    """
    # pylint: disable=import-outside-toplevel
    from app.gateway import GatewayModel

    def factory(settings):
        client = httpx.Client(transport=httpx.MockTransport(handler))
        return {
            name: GatewayModel(name, settings, client)
            for name in (settings.model_small, settings.model_large)
        }

    return factory


@given("the costed HR assistant is running", target_fixture="client")
def costed_assistant(make_costed_client):
    """El asistente con los dos modelos simulados y precios de prueba."""
    return make_costed_client()


@given("the costed HR assistant is running with routing off", target_fixture="client")
def costed_assistant_without_routing(make_costed_client):
    """El asistente con ``ROUTING=false``."""
    return make_costed_client(ROUTING="false")


@given(
    "one costed HR assistant with a history window of 6 and another of 1000",
    target_fixture="clients",
)
def costed_assistants_with_windows(make_costed_client):
    """Dos asistentes que solo cambian en ``HISTORY_WINDOW``."""
    return {
        "windowed": make_costed_client(HISTORY_WINDOW="6"),
        "full": make_costed_client(HISTORY_WINDOW="1000"),
    }


@given(
    "the HR assistant is running on a gateway that answers from its cache",
    target_fixture="client",
)
def gateway_assistant_with_cache(make_costed_client):
    """El gateway responde con ``cf-aig-cache-status: HIT``."""

    def handler(request):  # pylint: disable=unused-argument
        return gateway_reply('{"answer": "Hola, soy tu asistente."}', 40, 8, "HIT")

    return make_costed_client(
        _gateway_models(handler),
        MODEL_PROVIDER="gateway",
        CACHE_TTL_SECONDS="60",
        **CF_ENV,
    )


@given("the HR assistant is running on a gateway that fails", target_fixture="client")
def gateway_assistant_that_fails(make_costed_client):
    """El gateway responde ``503`` a toda llamada."""

    def handler(request):  # pylint: disable=unused-argument
        return httpx.Response(503, text="upstream down")

    return make_costed_client(
        _gateway_models(handler), MODEL_PROVIDER="gateway", **CF_ENV
    )


@when(parsers.parse('I ask "{question}"'), target_fixture="response")
def ask(client, question):
    """Envía una pregunta sin historial."""
    return client.post("/ask", json={"question": question})


@when(
    parsers.parse('I ask with request id "{request_id}" the question "{question}"'),
    target_fixture="response",
)
def ask_with_request_id(client, request_id, question):
    """Envía una pregunta con un ``X-Request-ID`` propio."""
    return client.post(
        "/ask", json={"question": question}, headers={"X-Request-ID": request_id}
    )


@when(
    parsers.parse('both are asked "{question}" with {count:d} history messages'),
    target_fixture="responses",
)
def ask_both_with_history(clients, question, count):
    """Envía la misma pregunta y el mismo historial a los dos asistentes."""
    body = {"question": question, "history": _history(count)}
    responses = {
        name: client.post("/ask", json=body) for name, client in clients.items()
    }
    assert {name: r.status_code for name, r in responses.items()} == {
        "windowed": 200,
        "full": 200,
    }
    return {name: r.json() for name, r in responses.items()}


@when(
    parsers.parse('I ask two questions "{first}" and "{second}"'),
    target_fixture="answers",
)
def ask_two_questions(client, first, second):
    """Envía dos preguntas al mismo proceso."""
    responses = [client.post("/ask", json={"question": q}) for q in (first, second)]
    assert [response.status_code for response in responses] == [200, 200]
    return [response.json() for response in responses]


@then(parsers.parse("the response status is {status:d}"))
def response_status_is(response, status):
    """Comprueba el código HTTP."""
    assert response.status_code == status


@then(parsers.parse('the answer used the model "{model}" with route "{route}"'))
def answer_used_model(response, model, route):
    """La respuesta dice qué modelo usó y por qué, sin perder los campos previos."""
    body = response.json()
    assert (body["model"], body["route"]) == (model, route)
    assert body["cached_calls"] == 0
    assert body["request_id"]


@then(parsers.parse('the cost is the price of "{model}" for the reported tokens'))
def cost_matches_price(response, model):
    """``cost_usd`` sale de la tabla de precios, en USD por millón de tokens."""
    body = response.json()
    input_price, output_price = PRICES[model]
    expected = (
        body["input_tokens"] * input_price + body["output_tokens"] * output_price
    ) / 1_000_000
    assert body["cost_usd"] > 0
    assert body["cost_usd"] == round(expected, COST_DECIMALS)


@then("the windowed assistant used fewer input tokens")
def windowed_uses_fewer_tokens(responses):
    """Mandar menos historial cuesta menos."""
    assert responses["windowed"]["input_tokens"] < responses["full"]["input_tokens"]
    assert responses["windowed"]["cost_usd"] < responses["full"]["cost_usd"]


@then("both assistants gave the same answer")
def both_answers_are_equal(responses):
    """La ventana no cambia la respuesta."""
    assert responses["windowed"]["answer"] == responses["full"]["answer"]
    assert responses["windowed"]["tools_used"] == ["get_employee"]


@then("the metrics cost is the sum of both answer costs")
def metrics_cost_is_the_sum(client, answers):
    """``/metrics`` acumula el costo de las respuestas de este proceso."""
    metrics = client.get("/metrics").json()
    expected = sum(answer["cost_usd"] for answer in answers)
    assert metrics["cost_usd"] == pytest.approx(expected, abs=1e-8)
    assert metrics["cost_usd"] > 0


@then(parsers.parse("the answer reports {count:d} cached call and a cost of 0"))
def answer_reports_cached_call(response, count):
    """La llamada cacheada se cuenta y no se cobra."""
    body = response.json()
    assert body["cached_calls"] == count
    assert body["cost_usd"] == 0
    assert body["model"] == SMALL_MODEL


@then(
    parsers.parse(
        'the response body is model unavailable for request id "{request_id}"'
    )
)
def body_is_model_unavailable(response, request_id):
    """El ``502`` no da detalles del proveedor ni del token."""
    assert response.json() == {"detail": "model unavailable", "request_id": request_id}
    assert response.headers["X-Request-ID"] == request_id
    assert CF_ENV["CF_API_TOKEN"] not in response.text
