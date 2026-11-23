"""Pruebas de la tabla de precios en USD por millón de tokens."""

import pytest
from conftest import LARGE_MODEL, SMALL_MODEL

from app.config import ConfigError
from app.pricing import PriceTable


def test_cost_uses_the_input_and_output_price_of_each_model(prices_file):
    prices = PriceTable(prices_file)
    # small: 1 USD y 2 USD por millón; large: 10 USD y 20 USD por millón.
    assert prices.cost(SMALL_MODEL, input_tokens=1000, output_tokens=500) == (
        pytest.approx(0.002)
    )
    assert prices.cost(LARGE_MODEL, input_tokens=1000, output_tokens=500) == (
        pytest.approx(0.02)
    )
    assert prices.cost(SMALL_MODEL, input_tokens=0, output_tokens=0) == 0


def test_missing_prices_file_prevents_start(tmp_path):
    with pytest.raises(ConfigError):
        PriceTable(tmp_path / "missing_prices.json")
