"""Pruebas de ``API_KEYS`` y de la identificación del cliente por su clave."""

import pytest

from app.auth import ApiKeyAuth, parse_api_keys
from app.config import ConfigError

ALPHA_KEY = "alpha-key-0000000001"
BETA_KEY = "beta-key-00000000002"


def test_each_configured_key_identifies_its_client():
    auth = ApiKeyAuth(parse_api_keys(f" acme : {ALPHA_KEY} , globex:{BETA_KEY} "))

    assert auth.identify(ALPHA_KEY) == "acme"
    assert auth.identify(BETA_KEY) == "globex"


def test_empty_api_keys_identify_nobody():
    auth = ApiKeyAuth(parse_api_keys(""))

    assert auth.identify(ALPHA_KEY) is None


@pytest.mark.parametrize("key", ["wrong-key-9999999999", None, ""])
def test_wrong_missing_or_empty_key_identifies_nobody(key):
    auth = ApiKeyAuth(parse_api_keys(f"acme:{ALPHA_KEY}"))

    assert auth.identify(key) is None


@pytest.mark.parametrize(
    ("raw", "entry_number", "entry_length", "hidden_secret"),
    [
        # Sin dos puntos.
        (f"acme:{ALPHA_KEY},nocolon-secret-77", 2, 17, "nocolon-secret-77"),
        # Cliente vacío.
        (":empty-client-secret", 1, 20, "empty-client-secret"),
        # Clave vacía: tampoco se muestra la clave buena de la otra entrada.
        (f"acme:{ALPHA_KEY},globex:", 2, 7, ALPHA_KEY),
        # Cliente repetido.
        (f"acme:{ALPHA_KEY},acme:{BETA_KEY}", 2, 25, BETA_KEY),
    ],
    ids=["missing_colon", "empty_client", "empty_key", "repeated_client"],
)
def test_malformed_entry_reports_its_number_and_length_but_never_the_key(
    raw, entry_number, entry_length, hidden_secret
):
    with pytest.raises(ConfigError) as error:
        parse_api_keys(raw)

    message = str(error.value)
    assert str(entry_number) in message
    assert str(entry_length) in message
    assert hidden_secret not in message
