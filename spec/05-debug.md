# Sesión 5 · Debug sin fugas: más detalle, cero secretos

Parte del producto de las sesiones 1 a 4 y le agrega un modo `debug` para entender un fallo sin reproducirlo,
sin que el log muestre nunca una credencial ni el texto de una pregunta o respuesta.

## Lo que debe hacer

1. **Nivel de log.** La variable `LOG_LEVEL` vale `info` (por omisión) o `debug`; cualquier otro valor es
   `ConfigError`. En `info` el log es exactamente el de la sesión 2.
2. **Eventos de debug.** Con `LOG_LEVEL=debug` se agregan, con los mismos campos comunes (`ts`, `service`,
   `event`, `request_id`):
   - `startup` (con `request_id` igual a `"-"`): `environment`, `model_provider`, `log_level` y, para cada
     secreto (`API_KEYS`, `CF_API_TOKEN`, `LANGSMITH_API_KEY`), solo `"set"` o `"unset"`. Nunca el valor.
   - `agent_step`: uno por cada paso del agente, con `step`, `tools` (solo los nombres) y `latency_ms`.
   - `model_call`: uno por cada llamada al modelo, con `model`, `status`, `latency_ms`, `input_tokens`,
     `output_tokens` y `cached`.
   - En el evento `error` se agrega `frames`: la lista de `"archivo:línea:función"` del stack trace. Nunca el
     mensaje de la excepción ni las variables locales.
3. **Lista blanca.** Los eventos llevan solo los campos que pide esta especificación. Está prohibido volcar
   objetos completos: encabezados de la petición, el entorno, la configuración, ni la petición o respuesta HTTP
   del gateway.
4. **Redactor central.** Todo evento, en `info` y en `debug`, pasa por un redactor antes de escribirse:
   - Un campo cuyo nombre contenga `authorization`, `api_key`, `api-key`, `token` (salvo los contadores
     `input_tokens` y `output_tokens`), `secret`, `password` o `cookie` vale `"[REDACTED]"`, también dentro de
     diccionarios y listas anidados.
   - Cualquier aparición de un secreto conocido (cada clave de `API_KEYS`, `CF_API_TOKEN` y
     `LANGSMITH_API_KEY`), aunque esté dentro de un texto, se reemplaza por `"[REDACTED]"`.
   - Cualquier texto `Bearer <algo>` se reemplaza por `Bearer [REDACTED]`.
5. **Librerías de terceros.** Los loggers de `httpx` y `httpcore` se quedan en `WARNING` aunque el producto esté
   en `debug`, porque en su nivel `DEBUG` imprimen encabezados.
6. **LangSmith no cambia.** `debug` no modifica `HIDE_INPUTS` ni `HIDE_OUTPUTS`.
7. **Compliance.** Con `ENVIRONMENT=production`, `LOG_LEVEL=debug` impide arrancar (`ConfigError`, sin mostrar
   ninguna clave en el mensaje). En producción se depura con el `request_id`; el detalle, en local o staging.

## Configuración nueva

| Variable | Por omisión | Para qué |
| --- | --- | --- |
| `LOG_LEVEL` | `info` | `info` o `debug`; `debug` está prohibido en producción |

## Reglas

- La hora y la latencia, con el reloj inyectado.
- `product/README.md` documenta `LOG_LEVEL`, y `doc/` agrega un ADR del modo debug.
- `doc/compliance-checklist.md` agrega la regla del punto 7.
- Todo lo de las sesiones 1 a 4 sigue funcionando.

## Cómo se comprueba

- **Prueba canario.** Con secretos de valores únicos (por ejemplo `canary-api-key-0001`, `canary-cf-token-0001`,
  `canary-langsmith-0001`) y `LOG_LEVEL=debug`, se corren: una pregunta que responde bien, una clave inválida, un
  `500` forzado y un `502` del modelo. En todo el log capturado no aparece ningún canario, ni `Bearer ` seguido
  de algo distinto de `[REDACTED]`, ni el texto de la pregunta.
- El redactor tapa un secreto en un diccionario anidado, en una lista y dentro de un texto.
- `ENVIRONMENT=production` con `LOG_LEVEL=debug` da `ConfigError` y el mensaje no contiene ninguna clave.
- `uv run python -m verification unit`, `contract` y `qa`, con cobertura de 80 % o más.
- `qa-style` revisa lo que un script no ve y escribe `output/qa-review.md`.
