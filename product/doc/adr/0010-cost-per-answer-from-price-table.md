# ADR 0010: Costo por respuesta con tabla de precios local

Estado: propuesto

## Contexto

Cada palanca se mide: hace falta saber cuánto cuesta cada respuesta, también con el
modelo simulado, sin red y sin gastar cuota. Las llamadas que sirve la caché del gateway
no se cobran.

## Decisión

`app/pricing.py` carga `PRICES_PATH` (`data/model_prices.json`, USD por millón de
tokens) una sola vez al arrancar; si `MODEL_SMALL` o `MODEL_LARGE` no tienen precio, el
proceso no arranca. El agente suma aparte los tokens facturables (los de llamadas no
cacheadas) y `cached_calls`. `cost_usd = (entrada * precio_entrada + salida *
precio_salida) / 1 000 000` con el precio del nombre del modelo enrutado, también para
los simulados. `POST /ask` responde `model`, `route`, `cached_calls` y `cost_usd`;
`Metrics` acumula `cost_usd` sin redondear y `/metrics` lo expone. Solo se redondea al
responder, a 8 decimales.

## Consecuencias

- La línea base y las palancas se comparan con la misma fórmula, sin red.
- Los precios cambian: se actualiza el JSON, no el código.
- El costo de `/metrics` es de este proceso (como en ADR 0006), no del servicio entero.
