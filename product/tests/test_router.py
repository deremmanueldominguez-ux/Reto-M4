"""Pruebas del enrutador por regla y de la ventana de historial."""

import pytest
from conftest import LARGE_MODEL, SMALL_MODEL

from app.config import load_settings
from app.router import apply_window, route


@pytest.fixture
def settings(cost_env):
    """Configuración con ``ROUTER_MAX_CHARS=80`` y los modelos de prueba."""
    return load_settings({**cost_env, "ROUTER_MAX_CHARS": "80"})


@pytest.mark.parametrize(
    ("question", "keyword"),
    [
        ("Compara Ventas con Finanzas", "compara"),
        ("RESUME el área de Tecnología", "resume"),
        ("Explica quién es EMP-0002", "explica"),
        ("¿Por qué EMP-0003 está de baja?", "por que"),
        ("Por que EMP-0003 esta de baja", "por que"),
        ("Analiza Ventas", "analiza"),
        ("Lista a todos", "todos"),
    ],
)
def test_keywords_send_the_question_to_the_large_model(settings, question, keyword):
    chosen = route(question, settings)
    assert (chosen.model, chosen.reason) == (LARGE_MODEL, f"keyword:{keyword}")


def test_a_question_of_exactly_the_limit_stays_on_the_small_model(settings):
    at_limit = route("x" * 80, settings)
    over_limit = route("x" * 81, settings)
    assert (at_limit.model, at_limit.reason) == (SMALL_MODEL, "short_question")
    assert (over_limit.model, over_limit.reason) == (LARGE_MODEL, "long_question")


def test_routing_off_always_uses_the_large_model(cost_env):
    settings = load_settings({**cost_env, "ROUTING": "false"})
    chosen = route("¿Quién es EMP-0001?", settings)
    assert (chosen.model, chosen.reason) == (LARGE_MODEL, "routing_off")


@pytest.mark.parametrize(
    ("size", "window", "kept"),
    [(4, 0, []), (3, 6, [0, 1, 2]), (10, 6, [4, 5, 6, 7, 8, 9])],
)
def test_history_window_keeps_only_the_last_messages(size, window, kept):
    history = [{"role": "user", "content": str(index)} for index in range(size)]
    windowed = apply_window(history, window)
    assert [int(turn["content"]) for turn in windowed] == kept
    assert len(history) == size
