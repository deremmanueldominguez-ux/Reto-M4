"""Tabla de precios por modelo, en USD por millón de tokens."""

import json
import math

from app.config import ConfigError

TOKENS_PER_PRICE_UNIT = 1_000_000
PRICE_KINDS = ("input", "output")


def _price(path, model, entry, kind):
    """Valida un precio de la tabla.

    :param path: Ruta del archivo, para el mensaje de error
    :type path: pathlib.Path
    :param model: Nombre del modelo
    :type model: str
    :param entry: Precios del modelo
    :type entry: dict
    :param kind: ``input`` o ``output``
    :type kind: str
    :return: Precio en USD por millón de tokens
    :rtype: float
    :raises ConfigError: Si el precio falta, no es número o es negativo
    """
    value = entry.get(kind) if isinstance(entry, dict) else None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ConfigError(f"{path}: price {kind!r} of {model!r} must be a number")
    if not math.isfinite(value) or value < 0:
        raise ConfigError(f"{path}: price {kind!r} of {model!r} must be >= 0")
    return float(value)


class PriceTable:
    """Precios de entrada y salida de cada modelo, cargados una vez al arrancar.

    :param path: Ruta del JSON con la clave ``models``
    :type path: pathlib.Path or str
    :raises app.config.ConfigError: Si el archivo no existe o no es válido
    """

    def __init__(self, path):
        try:
            with open(path, encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, ValueError) as error:
            raise ConfigError(f"PRICES_PATH could not be read: {path}") from error
        models = data.get("models") if isinstance(data, dict) else None
        if not isinstance(models, dict):
            raise ConfigError(f"PRICES_PATH has no 'models' object: {path}")
        self._prices = {
            name: tuple(_price(path, name, entry, kind) for kind in PRICE_KINDS)
            for name, entry in models.items()
        }
        self._path = path

    def require(self, models):
        """Comprueba que cada modelo configurado tenga precio.

        :param models: Nombres de los modelos
        :type models: collections.abc.Iterable[str]
        :raises app.config.ConfigError: Si algún modelo no tiene precio
        """
        for name in models:
            if name not in self._prices:
                raise ConfigError(f"model {name!r} has no price in {self._path}")

    def cost(self, model, input_tokens, output_tokens):
        """Calcula el costo de unos tokens, sin redondear.

        :param model: Nombre del modelo
        :type model: str
        :param input_tokens: Tokens de entrada facturables
        :type input_tokens: int
        :param output_tokens: Tokens de salida facturables
        :type output_tokens: int
        :return: Costo en USD
        :rtype: float
        :raises app.config.ConfigError: Si el modelo no tiene precio
        """
        self.require((model,))
        input_price, output_price = self._prices[model]
        total = input_tokens * input_price + output_tokens * output_price
        return total / TOKENS_PER_PRICE_UNIT
