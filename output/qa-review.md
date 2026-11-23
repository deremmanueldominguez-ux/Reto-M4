APROBADO

Revisión de qa-style sobre spec/05-debug.md (modo debug sin fugas de credenciales).
`uv run python -m verification qa`: [OK] (pylint 10.00/10).

## Lo revisado y conforme

- Lista blanca (spec punto 3): `app/events.py` `DEBUG_EVENT_FIELDS` y `whitelisted_fields` dejan solo los campos de
  la especificación en `startup`, `agent_step` y `model_call`. Ningún evento recibe encabezados, `os.environ`,
  `Settings` ni la petición o respuesta de `httpx`: `gateway.py` no registra nada y sus mensajes de error llevan
  solo el tipo o el código de estado; `model_call` se emite desde `agent.py` con valores escalares.
- Redactor central (spec punto 4): `EventLogger.emit` es el único punto de escritura y siempre llama
  `Redactor.redact`; `RequestLog.emit/debug` y `EventLogger.debug` pasan por él. No hay `print` ni otros loggers
  en `app/`. Reglas por nombre (con la excepción de `input_tokens`/`output_tokens`), por secreto conocido y por
  `Bearer`, recursivas en diccionarios y listas. `main.py` arma el redactor con las claves de `API_KEYS`,
  `CF_API_TOKEN` y `LANGSMITH_API_KEY`.
- `frames`: `stack_frames` usa `traceback.extract_tb` y `PurePath(...).name`, así que no lleva mensaje, variables
  locales ni rutas absolutas. Se agrega en el `500` (middleware) y en el `502` (`main.py`) solo en `debug`.
- `startup`: usa el campo `credentials` con `NOMBRE=set|unset`, como decidió la persona; sin excepciones por
  valor en el redactor.
- Compliance (spec punto 7): `_check_log_level` en `compliance.py` lanza `ConfigError` con un mensaje fijo sin
  ningún valor de la configuración.
- `httpx` y `httpcore` quedan en `WARNING` (`quiet_third_party_loggers`), y `debug` no toca `HIDE_INPUTS` ni
  `HIDE_OUTPUTS`.
- Docstrings Sphinx en lo público, nombres claros, constantes en vez de valores fijos y manejo de errores
  correctos.
- README (sección «Modo debug» y tabla de variables con `LOG_LEVEL`), ADR 0014, `doc/architecture.md` y
  `doc/compliance-checklist.md` coinciden con el código. La prueba canario cubre los cuatro casos de la
  especificación y revisa también `caplog` y la consola.

## Observaciones menores (no bloquean)

- `product/README.md`, el párrafo «Con `ENVIRONMENT=production` el producto no arranca si...» no menciona
  `LOG_LEVEL=debug`, aunque la tabla de variables y la sección «Modo debug» sí lo dicen. Dueño: architect.
- `product/doc/compliance-checklist.md`, la fila de `repr(settings)` nombra solo `api_keys` y `cf_api_token`;
  `langsmith_api_key` también tiene `repr=False`. Dueño: architect.
