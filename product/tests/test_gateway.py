"""Pruebas del cliente de Workers AI por AI Gateway, sin red (MockTransport)."""

import json

import httpx
import pytest
from conftest import CF_ENV, SMALL_MODEL, gateway_reply

from app.config import load_settings
from app.gateway import GatewayModel
from app.llm import ModelUnavailableError

GATEWAY_URL = (
    "https://gateway.ai.cloudflare.com/v1/acct-123/gw-test"
    "/workers-ai/v1/chat/completions"
)
MESSAGES = [{"role": "user", "content": "¿Quién es EMP-0001?"}]


def _model(cost_env, handler, **overrides):
    """Arma un ``GatewayModel`` cuya red es ``handler``.

    :rtype: app.gateway.GatewayModel
    """
    env = {**cost_env, **CF_ENV, "MODEL_PROVIDER": "gateway", **overrides}
    client = httpx.Client(transport=httpx.MockTransport(handler))
    return GatewayModel(SMALL_MODEL, load_settings(env), client)


def test_gateway_sends_the_exact_request_and_reads_the_usage(cost_env):
    seen = []

    def handler(request):
        seen.append(request)
        return gateway_reply('{"answer": "Hola"}', 21, 4)

    model = _model(cost_env, handler, MODEL_MAX_TOKENS="120", MODEL_TEMPERATURE="0")
    completion = model.complete(MESSAGES)

    request = seen[0]
    assert (request.method, str(request.url)) == ("POST", GATEWAY_URL)
    assert request.headers["Authorization"] == "Bearer cf-secret-token-xyz"
    assert "cf-aig-cache-ttl" not in request.headers
    assert json.loads(request.content) == {
        "model": SMALL_MODEL,
        "messages": MESSAGES,
        "max_tokens": 120,
        "temperature": 0,
    }
    assert (completion.text, completion.input_tokens, completion.output_tokens) == (
        '{"answer": "Hola"}',
        21,
        4,
    )
    assert completion.cached is False


def test_cache_header_is_sent_with_a_ttl_and_a_hit_marks_the_call_cached(cost_env):
    seen = []

    def handler(request):
        seen.append(request)
        return gateway_reply('{"answer": "Hola"}', cache_status="HIT")

    completion = _model(cost_env, handler, CACHE_TTL_SECONDS="300").complete(MESSAGES)
    assert seen[0].headers["cf-aig-cache-ttl"] == "300"
    assert completion.cached is True


def _timeout(request):
    raise httpx.ReadTimeout("gateway too slow", request=request)


@pytest.mark.parametrize(
    "handler",
    [
        _timeout,
        lambda request: httpx.Response(401, json={"error": "bad token"}),
        lambda request: httpx.Response(500, text="internal"),
        lambda request: httpx.Response(200, text="not json at all"),
        lambda request: httpx.Response(
            200, json={"choices": [{"message": {"content": "{}"}}]}
        ),
    ],
    ids=["timeout", "4xx", "5xx", "invalid_json", "missing_usage"],
)
def test_any_gateway_failure_is_model_unavailable_without_the_token(cost_env, handler):
    model = _model(cost_env, handler)
    with pytest.raises(ModelUnavailableError) as error:
        model.complete(MESSAGES)
    assert CF_ENV["CF_API_TOKEN"] not in str(error.value)
