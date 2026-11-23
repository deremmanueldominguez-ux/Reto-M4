# ADR 0008: Modelo real por AI Gateway detrás de la misma interfaz

Estado: propuesto

## Contexto

Se agrega Cloudflare Workers AI a través de AI Gateway, pero el agente no debe cambiar
(ADR 0002), las pruebas no pueden usar la red y una falla del proveedor debe distinguirse
de un error interno. Además hay dos modelos (pequeño y grande) por proceso.

## Decisión

`app/gateway.py` define `GatewayModel(name, settings, http_client)`, que cumple
`complete(messages)` con `httpx` inyectado. Manda `model`, `messages`, `max_tokens`
(`MODEL_MAX_TOKENS`) y `temperature`; lee `usage.prompt_tokens` y
`usage.completion_tokens`; manda `cf-aig-cache-ttl` solo si `CACHE_TTL_SECONDS > 0` y
marca `Completion.cached` si la respuesta trae `cf-aig-cache-status: HIT`. Cualquier
falla (red, tiempo de espera, `4xx/5xx`, cuerpo inválido) lanza `ModelUnavailableError`,
que `main.py` convierte en `502 {"detail": "model unavailable", "request_id"}`.
`build_models()` devuelve un modelo por nombre (`MODEL_SMALL`, `MODEL_LARGE`); con
`fake` son dos `FakeModel` con ese nombre. Con `gateway`, faltar un `CF_*` impide
arrancar; el token se guarda con `repr=False` y nunca se registra.

## Consecuencias

- El agente sigue sin saber qué proveedor usa; las pruebas inyectan `httpx.MockTransport`.
- El `502` deja claro en métricas y logs que falló el proveedor, no el producto.
- El conteo de tokens real viene del proveedor; el simulado sigue contando palabras.
