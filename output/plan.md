# Plan: sesión 5, modo debug sin fugas (spec/05-debug.md)

Parte del producto de las sesiones 1 a 4. Agrega `LOG_LEVEL` (`info` o `debug`), eventos de debug con
lista blanca de campos, un redactor central por el que pasa todo evento, loggers de `httpx` y `httpcore`
fijos en `WARNING` y una regla de compliance: `debug` prohibido en producción. Decisión en
`product/doc/adr/0014-debug-mode-with-central-redactor.md` (aceptado).

Decisión de la persona al aprobar el plan: el redactor no tiene ninguna excepción por valor
`set`/`unset`. El evento `startup` informa los secretos en un campo `credentials`, una lista de textos
como `["API_KEYS=set", "CF_API_TOKEN=unset", "LANGSMITH_API_KEY=unset"]`.

## Reparto del trabajo (en este orden)

1. **qa-unit** escribe primero las pruebas (en rojo), incluida la prueba canario.
2. **observability** implementa los puntos 1 a 6 y documenta `LOG_LEVEL` en `product/README.md`.
3. **security** implementa el punto 7 y agrega la regla a `product/doc/compliance-checklist.md`.
4. Después, como siempre: qa-style, costs, qa-e2e, deploy (sin cambios de alcance para ellos).

## Archivos a tocar

| Agente | Archivo | Cambio |
| --- | --- | --- |
| observability | `product/app/config.py` | `LOG_LEVEL` (`info` por omisión, `debug`; otro valor es `ConfigError`, sin mayúsculas/minúsculas). `Settings` gana `log_level` y `langsmith_api_key` (con `repr=False`), para que el redactor conozca los tres secretos. `HIDE_INPUTS`/`HIDE_OUTPUTS` no dependen de `log_level`. |
| observability | `product/app/events.py` | `Redactor(secrets)` (reglas del punto 4, sin excepciones por valor; la regla por nombre mira solo claves de diccionario, nunca el contenido de un texto); `EventLogger(..., level, redactor)` pasa todo evento por el redactor antes de `json.dumps`; método `debug(event, **fields)` en `EventLogger`, `RequestLog` y `NullLog` que no hace nada en `info`; `DEBUG_EVENT_FIELDS` (lista blanca por evento: `startup` con `environment`, `model_provider`, `log_level`, `credentials`; `agent_step`; `model_call`) que descarta cualquier campo no listado; `stack_frames(error)` que da `"archivo:línea:función"` con el nombre corto del archivo; `quiet_third_party_loggers()` que fija `httpx` y `httpcore` en `WARNING`. |
| observability | `product/app/middleware.py` | En el evento `error` del `500`, con `debug`, agrega `frames=stack_frames(error)`. Nunca `str(error)` ni locales. |
| observability | `product/app/main.py` | `create_app` arma el `Redactor` con las claves de `parse_api_keys`, `cf_api_token` y `langsmith_api_key`; llama `quiet_third_party_loggers()`; emite `startup` (con `request_id="-"`) en `debug`, con `credentials` = lista fija en este orden: `"API_KEYS=set\|unset"`, `"CF_API_TOKEN=set\|unset"`, `"LANGSMITH_API_KEY=set\|unset"`; pasa `clock` al `Agent`; el manejador del `502` agrega `frames` en `debug`. |
| observability | `product/app/agent.py` | Recibe `clock`. Emite `agent_step` (`step`, `tools` del paso, `latency_ms`) y `model_call` (`model`, `status` `ok`/`error`, `latency_ms`, `input_tokens`, `output_tokens`, `cached`) con `log.debug`. Si el modelo lanza `ModelUnavailableError`, emite `model_call` con `status="error"` y relanza. Latencias con `clock.monotonic()`. |
| observability | `product/app/gateway.py` | Sin cambios previstos: `model_call` se mide en el agente para cubrir también el modelo simulado. Solo se toca si hace falta exponer `name`. |
| observability | `product/README.md` | Fila `LOG_LEVEL` en la tabla de variables y un apartado corto "Modo debug" (qué agrega, `credentials` en `startup`, qué nunca sale, prohibido en producción). |
| security | `product/app/compliance.py` | Nueva regla `_check_log_level`: con `ENVIRONMENT=production` y `log_level == "debug"`, `ConfigError("production: LOG_LEVEL must not be debug")`. |
| security | `product/doc/compliance-checklist.md` | Fila nueva en "Reglas de arranque con `ENVIRONMENT=production`" con dónde está y su prueba; fila en "todo entorno" para el redactor y los loggers de terceros. |
| qa-unit | `product/tests/features/debug.feature`, `product/tests/test_debug_steps.py` | Escenarios Gherkin (abajo). |
| qa-unit | `product/tests/test_redactor.py`, `product/tests/test_debug_canary.py` | Pruebas unitarias y canario (abajo). |
| qa-unit | `product/tests/test_config.py`, `product/tests/test_compliance.py`, `product/tests/test_events.py` | Casos nuevos de `LOG_LEVEL`, regla de producción y `debug()`. |
| architect | `product/doc/adr/0014-debug-mode-with-central-redactor.md`, `product/doc/architecture.md` | Hecho en esta sesión; ADR 0014 aceptado con la decisión de `credentials`. |

## Módulos

- `__init__.py`: marca el paquete.
- `clock.py`: reloj inyectado (`now` y `monotonic`) para hora y latencias.
- `request_id.py`: acepta o genera el `X-Request-ID`.
- `config.py`: `Settings` desde el entorno; ahora también `LOG_LEVEL` y la clave de LangSmith oculta.
- `auth.py`: identifica al cliente por `X-API-Key` y valida `API_KEYS`.
- `rate_limit.py`: límite de peticiones por cliente en memoria.
- `compliance.py`: reglas de arranque en producción; ahora también "sin `debug`".
- `events.py`: log JSON por evento, redactor central sin excepciones, nivel `debug`, lista blanca y frames.
- `middleware.py`: id, latencia, `500` con evento `error` (con `frames` en `debug`), métricas.
- `metrics.py`: métricas del proceso en memoria.
- `tracing.py`: trazas opcionales en LangSmith; sin cambios.
- `router.py`: elige modelo por regla y recorta el historial.
- `pricing.py`: tabla de precios y costo por respuesta.
- `completion.py`: `Completion` y `ModelUnavailableError`.
- `llm.py`: interfaz `LanguageModel`, modelo simulado y `build_models`.
- `gateway.py`: modelo real por Cloudflare AI Gateway con `httpx`.
- `directory.py`: herramientas de solo lectura sobre los empleados.
- `agent.py`: bucle con tope; ahora emite `agent_step` y `model_call` en `debug`.
- `main.py`: `create_app`, rutas, `502` del modelo y evento `startup` (con `credentials`) en `debug`.
- `static/index.html`: página web del chat.

## Flujo de una pregunta (con `LOG_LEVEL=debug`)

1. Al arrancar, `load_settings` valida `LOG_LEVEL`; `check_production` rechaza `debug` en producción.
2. `create_app` arma el `Redactor` con los secretos conocidos, silencia `httpx`/`httpcore` y emite
   `startup` con `environment`, `model_provider`, `log_level` y `credentials`, una lista de textos
   `NOMBRE=set` o `NOMBRE=unset` por cada secreto. El redactor lo deja pasar porque ningún nombre de
   campo coincide con sus reglas, no por una excepción.
3. La página manda `POST /ask` con `X-API-Key`; el middleware fija `request_id` y toma `t0`.
4. `guard` valida la clave (`401`) y el límite (`429`); solo el nombre del cliente sigue adelante.
5. `main.py` enruta y crea un `Agent` con log, traza, `clock` y `Billing`.
6. Por cada llamada al modelo, el agente mide y emite `model_call`; por cada paso, `agent_step`.
7. Al terminar, `audit` y `agent_run` como en la sesión 2.
8. Si el modelo falla, `model_call` con `status="error"` y el manejador responde `502` con `error` y
   `frames`; cualquier otra excepción da `500` con `error` y `frames`.
9. El middleware emite `request`. Cada evento pasa por el redactor antes de escribirse.

## Pruebas

**Gherkin (`debug.feature`)**
- Con `LOG_LEVEL=info` el log de una pregunta tiene exactamente los eventos de la sesión 2.
- Con `LOG_LEVEL=debug` aparecen `startup`, `agent_step` y `model_call` con sus campos y nada más.
- `startup` trae `credentials` con `API_KEYS=set`, `CF_API_TOKEN=unset` y `LANGSMITH_API_KEY=unset`
  (o `set`, según el entorno), en ese orden, y nunca el valor de un secreto.
- Un `500` forzado y un `502` del modelo dejan `error` con `frames` y sin mensaje de la excepción.
- `LOG_LEVEL=verbose` impide arrancar; `ENVIRONMENT=production` con `LOG_LEVEL=debug` impide arrancar y
  el mensaje no contiene ninguna clave.

**Unitarias**
- Redactor: campo por nombre (`authorization`, `api_key`, `api-key`, `token`, `secret`, `password`,
  `cookie`, sin distinguir mayúsculas) en diccionario anidado y en lista; `input_tokens` y
  `output_tokens` intactos; secreto conocido dentro de un texto; `Bearer abc` pasa a
  `Bearer [REDACTED]`; un secreto vacío no reemplaza nada; un evento sin nada que tapar sale igual.
- Redactor sin excepciones: `{"api_key": "set"}` y `{"CF_API_TOKEN": "unset"}` salen `[REDACTED]`.
- Redactor y `credentials`: `{"credentials": ["API_KEYS=set", "CF_API_TOKEN=unset",
  "LANGSMITH_API_KEY=unset"]}` sale igual (la regla por nombre no se aplica al contenido de un texto).
- Lista blanca: `debug("model_call", headers=...)` descarta `headers`; `debug("startup", API_KEYS="set")`
  descarta `API_KEYS`.
- `stack_frames`: formato `archivo:línea:función`, sin ruta absoluta ni mensaje.
- `httpx` y `httpcore` quedan en `WARNING` tras `create_app` con `debug`.
- `debug` no cambia `hide_inputs`/`hide_outputs` ni `Tracer.from_settings`.
- `repr(settings)` no muestra `langsmith_api_key`.
- Latencias de `agent_step` y `model_call` con reloj falso (valores exactos).
- **Canario**: `API_KEYS=acme:canary-api-key-0001`, `CF_API_TOKEN=canary-cf-token-0001`,
  `LANGSMITH_API_KEY=canary-langsmith-0001`, `LOG_LEVEL=debug`. Corre: una pregunta buena, una clave
  inválida (`canary-wrong-key-0001`), un `500` forzado y un `502` del gateway real con
  `httpx.MockTransport` (así viaja el `Authorization: Bearer canary-cf-token-0001`). Captura el
  `log_stream` y además `caplog` y `capsys` en nivel `DEBUG`. Ningún canario, ningún `Bearer ` seguido
  de algo distinto de `[REDACTED]`, ni el texto de la pregunta. El `startup` del canario trae las tres
  entradas de `credentials` en `set`.
- Se corre `uv run python -m verification unit`, `contract` y `qa`; cobertura de 80 % o más.

## Riesgos

- **El redactor tapa `startup`**: resuelto por la persona sin excepción en el redactor (ADR 0014). Los
  secretos no son nombres de campo de `startup`: van como textos `NOMBRE=set|unset` dentro de
  `credentials`, que no coincide con ninguna regla por nombre. Prueba dedicada.
- **La regla por nombre mira dentro de los textos**: `"API_KEYS=set"` contiene `api_key` sin distinguir
  mayúsculas. Si la regla se aplicara al contenido, taparía `credentials`. Se evita aplicando la regla por
  nombre solo a claves de diccionario; prueba de `credentials` intacto.
- **Un secreto que sea `set`, `unset` o un nombre de variable**: la regla por valor lo reemplazaría
  dentro de `credentials` y el `startup` saldría con `[REDACTED]`. Es aceptable (falla hacia tapar, nunca
  hacia filtrar); `parse_api_keys` ya exige un largo mínimo de clave.
- **Alguien agrega `API_KEYS="set"` como campo de `startup`**: la lista blanca lo descarta y, si pasara,
  el redactor lo taparía. Prueba de lista blanca.
- **El log de `info` cambia sin querer**: el redactor no debe tocar los campos de la sesión 2. Prueba de
  igualdad exacta del log en `info` contra el de la sesión 2.
- **Fuga por terceros**: `httpx`/`httpcore` en `DEBUG` imprimen encabezados. Se fijan en `WARNING` en
  `create_app`, en cualquier nivel; el canario captura también el logging estándar.
- **Fuga por excepción**: el mensaje o los locales pueden llevar URL, token o pregunta. Solo se registran
  `error_type` y `frames`, con el nombre corto del archivo (la ruta absoluta revela usuario y máquina).
- **Volcar objetos**: la tentación de registrar `settings`, `request.headers` o la respuesta `httpx`. La
  lista blanca de `debug()` lo descarta; qa-style lo revisa.
- **Secreto corto o vacío**: un secreto vacío reemplazaría todo; se ignoran los vacíos y se reemplazan
  de más largo a más corto.
- **El texto de la pregunta en `audit.args`**: si la pregunta del canario es igual a un argumento de
  herramienta, saldría en el log. La pregunta del canario debe ser más larga que cualquier argumento.
- **Mensaje de compliance con claves**: el `ConfigError` del punto 7 es un texto fijo, sin valores.
- **Orden de agentes**: observability y security tocan módulos distintos; security depende de
  `Settings.log_level`, así que va después de observability.

## Resumen

- qa-unit escribe primero las pruebas: redactor, lista blanca, frames, `LOG_LEVEL`, regla de producción y el canario.
- observability toca `config.py`, `events.py`, `middleware.py`, `main.py` y `agent.py`, y documenta `LOG_LEVEL` en el README.
- security agrega `_check_log_level` en `compliance.py` y su fila en `compliance-checklist.md`.
- Todo evento pasa por un redactor central sin excepciones; los eventos de debug van con lista blanca y `httpx`/`httpcore` se quedan en `WARNING`.
- `startup` informa los secretos en `credentials` (`["API_KEYS=set", ...]`), decisión aprobada por la persona (ADR 0014 aceptado).
