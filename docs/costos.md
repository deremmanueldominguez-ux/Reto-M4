# Análisis de costos y optimizaciones

Las cuatro optimizaciones aplicadas bajaron el costo por respuesta de US$0.000145 a
US$0.000020 (86 % menos) sin bajar la calidad, que se mantuvo en 100 % en el set de
evaluación.

## De dónde sale el costo

El único costo variable es el modelo de lenguaje: Cloudflare Workers AI cobra por millón de
tokens de entrada y de salida. El servicio de Render corre en el plan gratuito, y el
directorio de empleados es un archivo local.

Precios usados (`product/data/model_prices.json`, tomados de la
[página de precios de Workers AI](https://developers.cloudflare.com/workers-ai/platform/pricing/)
el 2026-11-04):

| Modelo | Papel | Entrada (USD por millón) | Salida (USD por millón) |
| --- | --- | --- | --- |
| `@cf/meta/llama-3.1-8b-instruct-fast` | Pequeño, por omisión | 0.045 | 0.384 |
| `@cf/meta/llama-3.3-70b-instruct-fp8-fast` | Grande, para preguntas complejas | 0.293 | 2.253 |

El modelo grande cuesta unas 6.5 veces más por token de entrada y 5.9 veces más por token de
salida.

Cada respuesta calcula su propio costo:

```text
cost_usd = (tokens_entrada * precio_entrada + tokens_salida * precio_salida) / 1 000 000
```

con el precio del modelo que eligió el enrutador. Las llamadas que responde la caché del
gateway no se cobran. El costo viaja en la respuesta (`cost_usd`), en el evento `agent_run`
del log y acumulado en `GET /metrics`.

## Optimizaciones aplicadas

| Palanca | Qué hace | Variable (valor por omisión) | Por qué ahorra |
| --- | --- | --- | --- |
| Enrutamiento por regla | Manda al modelo grande solo las preguntas de más de 80 caracteres o con «compara», «resume», «explica», «por qué», «analiza» o «todos»; el resto va al pequeño | `ROUTING` (`true`), `ROUTER_MAX_CHARS` (`80`) | La mayoría de las preguntas son búsquedas simples que el modelo pequeño resuelve |
| Ventana de historial | Al modelo solo se mandan los últimos mensajes del historial | `HISTORY_WINDOW` (`6`) | Los tokens de entrada no crecen con la conversación |
| Tope de salida | Limita los tokens que genera el modelo | `MODEL_MAX_TOKENS` (`300`) | La salida es la parte cara; acota el peor caso |
| Caché de AI Gateway | Una llamada idéntica reciente se responde sin pasar por el modelo | `CACHE_TTL_SECONDS` (`0`, apagada) | Preguntas repetidas no cuestan |

Además, el bucle del agente tiene un tope de 3 llamadas al modelo por pregunta
(`AGENT_MAX_STEPS`), que acota el costo máximo de cualquier respuesta.

La regla de enrutamiento está en código, no en otro modelo: decidir el modelo no cuesta
tokens y siempre da el mismo resultado para la misma pregunta.

## Resultados medidos

La compuerta `evaluate` corre el set de evaluación (`verification/eval_set.json`, 8
preguntas) dos veces y solo pasa si la calidad no baja y el costo sí baja:

| Variante | Calidad | Costo total (8 preguntas) | Costo por respuesta | Tokens de entrada |
| --- | --- | --- | --- | --- |
| Línea base (sin enrutamiento ni ventana) | 100 % | US$0.001163 | US$0.000145 | 2507 |
| Con las palancas | 100 % | US$0.000160 | US$0.000020 | 1937 |
| Diferencia | igual | **86 % menos** | **86 % menos** | 23 % menos |

Proyección con esos números:

| Volumen | Línea base | Con las palancas |
| --- | --- | --- |
| 10 000 preguntas | US$1.45 | US$0.20 |
| 1 000 000 de preguntas | US$145 | US$20 |

## Límites del análisis

- La evaluación usa el modelo simulado con el precio real de cada modelo, para medir sin red
  ni cuota. Los tokens del modelo real varían según lo que responda, así que el costo real
  puede diferir.
- La caché está apagada por omisión, así que no entra en la medición. Encenderla
  (`CACHE_TTL_SECONDS` mayor que 0) solo puede bajar más el costo.
- Los precios de Workers AI cambian: hay que revisarlos antes de proyectar un presupuesto.

## Cómo verificarlo

```bash
uv run python -m verification evaluate
```

En producción, `GET /metrics` muestra el costo acumulado del proceso y el panel de
Cloudflare AI Gateway muestra el costo y los tokens de cada llamada.
