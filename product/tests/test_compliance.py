"""Pruebas de las reglas de compliance y de la configuración nueva de producción."""

import pytest
from conftest import ACME_KEY, CF_ENV, GLOBEX_KEY

from app.compliance import check_production
from app.config import ConfigError, load_settings


def test_development_does_not_apply_the_production_rules(employees_file):
    settings = load_settings(
        {
            "EMPLOYEES_PATH": str(employees_file),
            "MODEL_PROVIDER": "fake",
            "LANGSMITH_TRACING": "true",
            "HIDE_OUTPUTS": "false",
        }
    )

    check_production(settings)


def test_production_with_traces_on_requires_hidden_outputs(production_env):
    env = {**production_env, "LANGSMITH_TRACING": "true", "HIDE_OUTPUTS": "false"}

    with pytest.raises(ConfigError):
        check_production(load_settings(env))


def test_unknown_environment_prevents_start(production_env):
    env = {**production_env, "ENVIRONMENT": "prod"}

    with pytest.raises(ConfigError, match="ENVIRONMENT"):
        check_production(load_settings(env))


def test_production_settings_default_to_development_and_30_requests():
    settings = load_settings({})

    assert settings.environment == "development"
    assert settings.rate_limit_per_minute == 30


@pytest.mark.parametrize("value", ["0", "abc"])
def test_invalid_rate_limit_prevents_start(value):
    with pytest.raises(ConfigError, match="RATE_LIMIT_PER_MINUTE"):
        load_settings({"RATE_LIMIT_PER_MINUTE": value})


def test_the_api_keys_never_appear_in_the_settings_repr(production_env):
    settings = load_settings(production_env)

    assert ACME_KEY not in repr(settings)


# Sesión 5: ``LOG_LEVEL=debug`` está prohibido en producción.


def test_production_in_debug_prevents_start_without_showing_any_key(production_env):
    env = {**production_env, "LOG_LEVEL": "debug"}

    with pytest.raises(ConfigError, match="LOG_LEVEL") as error:
        check_production(load_settings(env))

    message = str(error.value)
    for secret in (ACME_KEY, GLOBEX_KEY, CF_ENV["CF_API_TOKEN"]):
        assert secret not in message


def test_debug_is_allowed_in_development(employees_file):
    settings = load_settings(
        {"EMPLOYEES_PATH": str(employees_file), "LOG_LEVEL": "debug"}
    )

    check_production(settings)

    assert settings.log_level == "debug"
