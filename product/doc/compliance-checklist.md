# Checklist de compliance

Las reglas se revisan solas: `create_app` (en `app/main.py`) llama
`parse_api_keys` y `check_production` antes de armar nada. Si una regla falla, lanza
`ConfigError` al importar `app.main` y uvicorn no arranca. Ningún mensaje de error
muestra una clave.

## Reglas de arranque con `ENVIRONMENT=production`

| Regla | Dónde está en el código | Cómo se comprueba |
| --- | --- | --- |
| `MODEL_PROVIDER` no puede ser `fake` | `app/compliance.py`, `check_production` | `tests/features/security.feature` («Production refuses to start», fila `MODEL_PROVIDER`); `verification/contract/test_contract_04.py::test_production_refuses_the_fake_model` |
| `API_KEYS` no puede estar vacía | `app/compliance.py`, `_check_api_keys` | `security.feature`, fila `API_KEYS (empty)` |
| Cada clave mide 16 caracteres o más | `app/compliance.py`, `_check_api_keys` (`MIN_API_KEY_LENGTH`) | `security.feature`, fila `acme:abcdefghijklmno` (15 caracteres); el error no muestra la clave |
| `LOG_LEVEL` no puede ser `debug`; el mensaje es fijo y no muestra claves | `app/compliance.py`, `_check_log_level` | `tests/test_compliance.py::test_production_in_debug_prevents_start_without_showing_any_key`; `tests/features/debug.feature`, «Production refuses to start in debug mode without showing any key» |
| Con trazas encendidas, `HIDE_INPUTS` y `HIDE_OUTPUTS` valen `true` | `app/compliance.py`, `_check_tracing` | `security.feature`, fila `LANGSMITH_TRACING`; `tests/test_compliance.py::test_production_with_traces_on_requires_hidden_outputs` |
| Con todo bien configurado, arranca | `app/compliance.py`, `check_production` | `security.feature`, «Production starts when every rule is followed» |
| `development` no aplica estas reglas | `app/compliance.py`, `check_production` | `tests/test_compliance.py::test_development_does_not_apply_the_production_rules` |

## Reglas que aplican en todo entorno

| Regla | Dónde está en el código | Cómo se comprueba |
| --- | --- | --- |
| `ENVIRONMENT` solo acepta `development` o `production` | `app/config.py`, `_environment`; `app/compliance.py`, `check_production` | `tests/test_compliance.py::test_unknown_environment_prevents_start` |
| `API_KEYS` mal formada impide arrancar; el error da número de entrada y largo, nunca el valor | `app/auth.py`, `parse_api_keys` y `_entry_error` | `tests/test_auth.py::test_malformed_entry_reports_its_number_and_length_but_never_the_key`; `test_contract_04.py::test_a_broken_api_keys_never_leaks_the_key` |
| `POST /ask` y `GET /metrics` exigen `X-API-Key`; sin ella o inválida, `401` | `app/auth.py`, `ApiKeyAuth.require_client`; `app/main.py`, `_build_guard` y `_add_routes` | `security.feature`, «A question without a key is rejected» y «A protected endpoint rejects a wrong or missing key» |
| `GET /`, `GET /health` y `/docs` no piden clave | `app/main.py`, `_add_routes` (sin `guard`) | `security.feature`, «The public pages do not ask for a key» |
| Las claves se comparan en tiempo constante | `app/auth.py`, `ApiKeyAuth.identify` (`hmac.compare_digest` contra todas) | Revisión de código; `tests/test_auth.py` |
| Límite de `RATE_LIMIT_PER_MINUTE` por cliente; `429` con `Retry-After` | `app/rate_limit.py`, `RateLimiter.check` y `enforce` | `tests/test_rate_limit.py`; `security.feature`, escenarios de límite |
| La clave nunca va en el log ni en la traza; solo el nombre del cliente | `app/auth.py` (guarda solo `request.state.client`); `app/events.py`, `RequestLog`; `app/tracing.py`, `wrap` | `security.feature`, «The log names the client and never writes a key»; `tests/test_tracing.py` |
| `repr(settings)` no muestra claves ni tokens | `app/config.py`, `Settings` (`api_keys`, `cf_api_token` y `langsmith_api_key` con `repr=False`) | `tests/test_compliance.py::test_the_api_keys_never_appear_in_the_settings_repr` |
| Todo evento del log pasa por el redactor central (campos sensibles, secretos conocidos y `Bearer`) | `app/events.py`, `Redactor` y `EventLogger`; `app/main.py`, arma el `Redactor` con `API_KEYS`, `CF_API_TOKEN` y `LANGSMITH_API_KEY` | `tests/features/debug.feature`, «The startup event says whether each secret is set and never its value» y escenarios de fallo; `tests/test_redactor.py`; `tests/test_events.py::test_every_emitted_event_goes_through_the_redactor_also_at_info`; `tests/test_debug_canary.py::test_no_canary_bearer_or_question_reaches_any_log_in_debug` |
| Los loggers `httpx` y `httpcore` quedan en `WARNING` en todo entorno (no imprimen `Authorization`) | `app/events.py`, `quiet_third_party_loggers` (`THIRD_PARTY_LOGGERS`); llamado desde `app/main.py` | `tests/test_debug_canary.py::test_httpx_and_httpcore_stay_at_warning_even_in_debug` |
| La página guarda la clave en `sessionStorage`, nunca en `localStorage` ni en el código | `app/static/index.html` | `tests/test_page.py` |

## Fuera de alcance (riesgos aceptados)

- **Fuerza bruta de claves**: un `401` no consume el límite de peticiones. Se mitiga
  con claves de 16 caracteres o más en producción.
- **Varias copias del servicio**: el límite vive en la memoria de cada proceso, así que
  con N copias el límite real es N veces mayor (ADR 0012). Render `free` corre una
  sola instancia.
