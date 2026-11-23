# ADR 0014: Modo debug con lista blanca y redactor central

Estado: aceptado

## Contexto

Para entender un fallo sin reproducirlo hace falta más detalle que el log de la sesión 2
(pasos del agente, llamadas al modelo, stack trace). Ese detalle no puede mostrar nunca una
credencial ni el texto de una pregunta o respuesta, y las librerías de terceros (`httpx`,
`httpcore`) imprimen encabezados en su nivel `DEBUG`. El evento `startup` debe decir si cada
secreto está definido; con los nombres de variable como campos, la regla por nombre del
redactor los taparía.

## Decisión

- `LOG_LEVEL` vale `info` (por omisión) o `debug`; otro valor es `ConfigError`. Con
  `ENVIRONMENT=production`, `debug` impide arrancar (`app/compliance.py`).
- `EventLogger.debug(event, **fields)` solo escribe en `debug` y solo los campos de la lista
  blanca de cada evento (`startup`, `agent_step`, `model_call`); el resto se descarta. El
  evento `error` agrega `frames` (`"archivo:línea:función"`, nombre corto del archivo), nunca
  el mensaje ni las variables locales.
- Todo evento, en `info` y en `debug`, pasa por un `Redactor` antes de `json.dumps`: tapa por
  nombre de campo (salvo `input_tokens` y `output_tokens`), por valor de secreto conocido
  (claves de `API_KEYS`, `CF_API_TOKEN`, `LANGSMITH_API_KEY`) y por `Bearer <algo>`, en
  diccionarios y listas anidados. Los secretos vacíos se ignoran. La regla por nombre se aplica
  solo a claves de diccionario, no al contenido de los textos.
- El redactor no tiene ninguna excepción por valor (`set`/`unset` se tapan como cualquier otro
  valor de un campo sensible). Decisión de la persona al aprobar el plan.
- `startup` informa los secretos en un campo `credentials`: una lista de textos en orden fijo,
  por ejemplo `["API_KEYS=set", "CF_API_TOKEN=unset", "LANGSMITH_API_KEY=unset"]`.
- `model_call` se mide en el agente, no en `gateway.py`, para cubrir también el modelo simulado.
- `create_app` fija los loggers `httpx` y `httpcore` en `WARNING` en cualquier nivel.
- `debug` no toca `HIDE_INPUTS` ni `HIDE_OUTPUTS`.

## Consecuencias

- Un solo punto de salida protege también los eventos de las sesiones 2 a 4; en `info` el
  log no cambia porque ningún campo existente coincide con las reglas.
- El redactor queda sin casos especiales: más simple de probar y sin un hueco que se pueda
  explotar poniendo `"set"` en un campo sensible.
- `credentials` es texto, no un objeto: quien lea el log lo interpreta por convención
  `NOMBRE=set|unset`. Si un secreto coincidiera con `set`, `unset` o un nombre de variable, la
  regla por valor lo taparía dentro de `credentials`: falla hacia tapar, nunca hacia filtrar.
- `Settings` guarda la clave de LangSmith con `repr=False`, solo para que el redactor la conozca.
- Un campo nuevo en un evento de debug exige actualizar la lista blanca: es intencional.
- La prueba canario (secretos únicos en un flujo bueno, `401`, `500` y `502`) es la defensa de
  regresión; captura también el logging estándar.
- En producción se depura solo con el `request_id`.
