"""Pruebas del redactor central por el que pasa todo evento antes de escribirse.

Interfaz esperada: ``Redactor(secrets).redact(value)`` devuelve una copia de
``value`` (diccionario, lista o texto) con lo sensible reemplazado por
``"[REDACTED]"``.
"""

REDACTED = "[REDACTED]"


def _redactor(secrets=()):
    """Crea un redactor; se importa aquí para no romper la recolección.

    :param secrets: Secretos conocidos
    :type secrets: collections.abc.Iterable[str]
    :rtype: app.events.Redactor
    """
    # pylint: disable=import-outside-toplevel
    from app.events import Redactor

    return Redactor(secrets)


def test_sensitive_field_names_are_redacted_at_any_depth():
    record = {
        "Authorization": "Bearer abc",
        "outer": {
            "api_key": "a",
            "X-Api-Key": "b",
            "items": [{"refresh_token": "c"}, {"client_Secret": "d"}],
        },
        "password": "e",
        "Cookie": "f",
        "keep": "ok",
    }

    assert _redactor().redact(record) == {
        "Authorization": REDACTED,
        "outer": {
            "api_key": REDACTED,
            "X-Api-Key": REDACTED,
            "items": [{"refresh_token": REDACTED}, {"client_Secret": REDACTED}],
        },
        "password": REDACTED,
        "Cookie": REDACTED,
        "keep": "ok",
    }


def test_token_counters_are_kept_but_other_token_fields_are_not():
    record = {"input_tokens": 12, "output_tokens": 3, "cf_api_token": "x"}

    assert _redactor().redact(record) == {
        "input_tokens": 12,
        "output_tokens": 3,
        "cf_api_token": REDACTED,
    }


def test_known_secrets_are_replaced_inside_text_in_dicts_and_lists():
    redactor = _redactor(["canary-one-0001", "canary-two-0002"])
    record = {
        "note": "url?key=canary-one-0001&page=2",
        "nested": {"items": ["before canary-two-0002 after", 3, None]},
    }

    assert redactor.redact(record) == {
        "note": f"url?key={REDACTED}&page=2",
        "nested": {"items": [f"before {REDACTED} after", 3, None]},
    }


def test_the_longest_secret_is_replaced_first():
    redactor = _redactor(["abc123", "abc123-longer"])

    assert redactor.redact("value abc123-longer end") == f"value {REDACTED} end"


def test_any_bearer_value_is_replaced_and_stays_replaced():
    redactor = _redactor()
    text = "upstream said Bearer eyJhbGciOi.payload-1 was rejected"

    once = redactor.redact(text)

    assert once == f"upstream said Bearer {REDACTED} was rejected"
    assert redactor.redact(once) == once


def test_an_event_with_nothing_to_hide_is_unchanged_even_with_empty_secrets():
    record = {
        "event": "agent_run",
        "steps": 2,
        "tools": ["get_employee"],
        "input_tokens": 40,
        "output_tokens": 9,
        "cost_usd": 0.0001,
        "cached": False,
    }

    assert _redactor(["", "unrelated-secret"]).redact(record) == record


def test_set_or_unset_under_a_sensitive_name_is_still_redacted():
    redactor = _redactor(["real-key-value-0001"])
    record = {
        "API_KEYS": "set",
        "CF_API_TOKEN": "unset",
        "credentials": ["API_KEYS=set", "CF_API_TOKEN=unset"],
    }

    assert redactor.redact(record) == {
        "API_KEYS": REDACTED,
        "CF_API_TOKEN": REDACTED,
        "credentials": ["API_KEYS=set", "CF_API_TOKEN=unset"],
    }
