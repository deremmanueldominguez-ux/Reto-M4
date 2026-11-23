# ADR 0006: Métricas en memoria de cada proceso

Estado: propuesto

## Contexto

`GET /metrics` debe informar peticiones, tasa de error, latencia p50/p95, tokens y si se
cumple `SLO_P95_MS`. La API es sin estado (ADR 0001) y no hay base de datos ni servicio
de métricas.

## Decisión

Cada proceso lleva un objeto `Metrics` en memoria, protegido con un candado, y lo expone
con su `pid`. Cuenta todas las peticiones terminadas; `error_rate` son las `5xx` entre
el total; los percentiles se calculan por rango más cercano sobre las últimas 1000
latencias; `met` es `p95 < SLO_P95_MS`. Sin datos: percentiles `0`, `error_rate` `0.0`.

## Consecuencias

- Es estado operativo, no de negocio: no cambia ninguna respuesta de `/ask`, así que el
  ADR 0001 sigue vigente.
- Cada copia reporta solo lo suyo; ver el total exige sumar copias por fuera.
- Los datos se pierden al reiniciar y la memoria queda acotada por la ventana.
- Si se necesita agregación o historia, se cambia a un exportador sin tocar el agente.
