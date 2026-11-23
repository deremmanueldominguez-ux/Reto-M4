"""Pruebas de la configuración leída de variables de entorno."""

import pytest

from app.config import ConfigError, load_settings


def test_defaults_are_used_when_nothing_is_set():
    settings = load_settings({})
    assert settings.model_provider == "fake"
    assert settings.agent_max_steps == 3
    assert settings.max_question_chars == 2000
    assert settings.employees_path.parts[-2:] == ("data", "employees.json")


def test_non_positive_or_non_numeric_limits_prevent_start(employees_file):
    base = {"EMPLOYEES_PATH": str(employees_file)}
    for variable in ("AGENT_MAX_STEPS", "MAX_QUESTION_CHARS"):
        for value in ("0", "-1", "abc"):
            with pytest.raises(ConfigError, match=variable):
                load_settings({**base, variable: value})


def test_unknown_model_provider_prevents_start(employees_file):
    env = {"EMPLOYEES_PATH": str(employees_file), "MODEL_PROVIDER": "magic"}
    with pytest.raises(ConfigError, match="MODEL_PROVIDER"):
        load_settings(env)


def test_observability_defaults_are_safe_and_tracing_needs_the_key():
    settings = load_settings({"LANGSMITH_TRACING": "true"})
    assert settings.service_name == "hr-assistant"
    assert settings.slo_p95_ms == 2000
    assert settings.langsmith_tracing is True
    assert (settings.hide_inputs, settings.hide_outputs) == (True, True)
    assert settings.tracing_enabled is False

    secret = "lsv2-test-secret-key"
    traced = load_settings({"LANGSMITH_TRACING": "TRUE", "LANGSMITH_API_KEY": secret})
    assert traced.tracing_enabled is True
    assert secret not in repr(traced)
    assert load_settings({"LANGSMITH_API_KEY": secret}).tracing_enabled is False


def test_invalid_observability_values_prevent_start(employees_file):
    base = {"EMPLOYEES_PATH": str(employees_file)}
    invalid = {
        "SLO_P95_MS": "0",
        "LANGSMITH_TRACING": "quizas",
        "HIDE_INPUTS": "si",
        "SERVICE_NAME": "",
    }
    for variable, value in invalid.items():
        with pytest.raises(ConfigError, match=variable):
            load_settings({**base, variable: value})


def test_missing_employees_file_prevents_start(tmp_path):
    env = {"EMPLOYEES_PATH": str(tmp_path / "missing.json")}
    with pytest.raises(ConfigError, match="EMPLOYEES_PATH"):
        load_settings(env)


# Sesión 3: costos.

CF_VARIABLES = ("CF_ACCOUNT_ID", "CF_GATEWAY_ID", "CF_API_TOKEN")


def test_cost_lever_defaults_match_the_specification():
    settings = load_settings({})
    assert settings.model_small == "@cf/meta/llama-3.1-8b-instruct-fast"
    assert settings.model_large == "@cf/meta/llama-3.3-70b-instruct-fp8-fast"
    assert settings.routing is True
    assert settings.router_max_chars == 80
    assert settings.history_window == 6
    assert settings.model_max_tokens == 300
    assert settings.model_temperature == 0.0
    assert settings.cache_ttl_seconds == 0
    assert settings.cf_gateway_id == "default"
    assert settings.prices_path.parts[-2:] == ("data", "model_prices.json")


@pytest.mark.parametrize("missing", CF_VARIABLES)
def test_gateway_provider_without_any_cloudflare_variable_prevents_start(missing):
    env = {
        "MODEL_PROVIDER": "gateway",
        "CF_ACCOUNT_ID": "acct-123",
        "CF_GATEWAY_ID": "gw-test",
        "CF_API_TOKEN": "cf-secret-token-xyz",
        missing: "",
    }
    with pytest.raises(ConfigError, match=missing):
        load_settings(env)


@pytest.mark.parametrize(
    ("variable", "value"),
    [
        ("ROUTING", "maybe"),
        ("ROUTER_MAX_CHARS", "abc"),
        ("HISTORY_WINDOW", "-1"),
        ("MODEL_MAX_TOKENS", "0"),
        ("MODEL_TEMPERATURE", "hot"),
        ("CACHE_TTL_SECONDS", "-5"),
    ],
)
def test_invalid_cost_lever_values_prevent_start(variable, value):
    with pytest.raises(ConfigError, match=variable):
        load_settings({variable: value})


def test_the_cloudflare_token_never_appears_in_the_settings_repr():
    secret = "cf-secret-token-xyz"
    settings = load_settings(
        {
            "MODEL_PROVIDER": "gateway",
            "CF_ACCOUNT_ID": "acct-123",
            "CF_API_TOKEN": secret,
        }
    )
    assert settings.cf_api_token == secret
    assert settings.cf_gateway_id == "default"
    assert secret not in repr(settings)


# Sesión 5: ``LOG_LEVEL``.


def test_log_level_defaults_to_info_and_ignores_case():
    assert load_settings({}).log_level == "info"
    assert load_settings({"LOG_LEVEL": "DEBUG"}).log_level == "debug"
    assert load_settings({"LOG_LEVEL": "Info"}).log_level == "info"


def test_unknown_log_level_prevents_start():
    for value in ("verbose", "warning"):
        with pytest.raises(ConfigError, match="LOG_LEVEL"):
            load_settings({"LOG_LEVEL": value})


def test_debug_does_not_change_langsmith_and_hides_its_key_in_the_repr():
    secret = "canary-langsmith-0001"
    base = {"LANGSMITH_TRACING": "true", "LANGSMITH_API_KEY": secret}
    info = load_settings({**base, "LOG_LEVEL": "info"})
    debug = load_settings({**base, "LOG_LEVEL": "debug"})

    assert (debug.hide_inputs, debug.hide_outputs) == (True, True)
    assert (debug.hide_inputs, debug.hide_outputs, debug.tracing_enabled) == (
        info.hide_inputs,
        info.hide_outputs,
        info.tracing_enabled,
    )
    assert debug.langsmith_api_key == secret
    assert secret not in repr(debug)
