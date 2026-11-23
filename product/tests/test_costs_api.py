"""Pruebas de ``POST /ask`` con costos: tokens facturables, ventana y precios."""

import pytest
from conftest import LARGE_MODEL, SMALL_MODEL

from app.config import load_settings
from app.llm import Completion
from app.main import create_app

QUESTION = "¿Quién es EMP-0001?"


class ScriptedModel:  # pylint: disable=too-few-public-methods
    """Modelo que devuelve, en orden, las respuestas que se le dan.

    :param completions: Respuestas que devuelve una por llamada
    :type completions: list[app.llm.Completion]
    """

    def __init__(self, completions):
        self._completions = list(completions)

    def complete(self, messages):  # pylint: disable=unused-argument
        """Devuelve la siguiente respuesta del guion."""
        return self._completions.pop(0)


def test_cached_calls_are_counted_and_only_billable_tokens_cost(make_costed_client):
    script = [
        Completion(
            text='{"tool": "get_employee", "args": {"employee_id": "EMP-0001"}}',
            input_tokens=100,
            output_tokens=10,
            cached=True,
        ),
        Completion(text='{"answer": "Ana López"}', input_tokens=7, output_tokens=3),
    ]
    client = make_costed_client(
        lambda settings: {
            SMALL_MODEL: ScriptedModel(script),
            LARGE_MODEL: ScriptedModel([]),
        }
    )
    body = client.post("/ask", json={"question": QUESTION}).json()
    assert (body["steps"], body["tools_used"]) == (2, ["get_employee"])
    assert (body["input_tokens"], body["output_tokens"]) == (107, 13)
    assert body["cached_calls"] == 1
    # Solo la segunda llamada cuesta: (7 * 1 + 3 * 2) / 1 000 000 con el modelo chico.
    assert body["cost_usd"] == pytest.approx(0.000013, abs=1e-12)


def test_a_zero_history_window_never_cuts_the_current_tool_loop(make_costed_client):
    client = make_costed_client(HISTORY_WINDOW="0")
    history = [
        {"role": "user", "content": "Hola"},
        {"role": "assistant", "content": "Hola, ¿en qué te ayudo?"},
    ]
    response = client.post("/ask", json={"question": QUESTION, "history": history})
    body = response.json()
    assert response.status_code == 200
    assert (body["steps"], body["tools_used"]) == (2, ["get_employee"])
    assert "Ana López" in body["answer"]


def test_a_configured_model_without_a_price_prevents_start(cost_env):
    # Puede fallar al leer la configuración o al armar la app: lo que importa es que
    # el proceso no arranca y el error nombra al modelo sin precio.
    with pytest.raises(ValueError, match="@cf/unknown/model"):
        settings = load_settings({**cost_env, "MODEL_LARGE": "@cf/unknown/model"})
        create_app(settings=settings)
