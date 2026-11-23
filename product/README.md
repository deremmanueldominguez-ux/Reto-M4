# HR Assistant

Asistente de Recursos Humanos: una API web sin estado (FastAPI) con un agente que
responde preguntas sobre el directorio de empleados usando herramientas
(`get_employee`, `search_by_department`, `search_by_name`) y una página web para
conversar con él.

Desde la sesión 2 cada petición se puede rastrear: tiene un id, deja eventos JSON en
la salida estándar, alimenta `GET /metrics` y, si se enciende, queda como traza en
LangSmith.

Desde la sesión 3 puede usar un modelo real (Cloudflare Workers AI a través de AI
Gateway) y cada respuesta dice qué modelo usó, por qué y cuánto costó. Hay cuatro
palancas de costo: enrutamiento por pregunta, ventana de historial, tope de salida y
caché del gateway.

Desde la sesión 4 está listo para publicarse: `POST /ask` y `GET /metrics` piden una
clave por cliente, hay un límite de peticiones por cliente y, con
`ENVIRONMENT=production`, el producto se niega a arrancar si la configuración no es
segura (ver `doc/compliance-checklist.md`).

## Requisitos previos

- Python 3.12.
- git.
- pip (viene con Python) o, si lo prefieres, uv (opcional).
- Chromium de Playwright, solo para las pruebas de punta a punta (`e2e/`).
- Docker, solo para construir la imagen del contenedor.

Cuentas opcionales:

- Cloudflare (Workers AI y AI Gateway), para usar el modelo real.
- LangSmith, para guardar trazas.
- Render y GitHub, para publicar.

Sin ninguna cuenta el producto funciona con el modelo simulado.

## Instalación

```bash
git clone https://github.com/deremmanueldominguez-ux/hr-assistant.git
cd hr-assistant
```

Crea y activa un entorno virtual.

En Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

En Linux o macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Instala las dependencias y, solo si vas a correr las pruebas `e2e`, el navegador de
Playwright (una sola vez):

```bash
pip install -r requirements.txt
python -m playwright install chromium
```

Con uv (opcional), en lugar de lo anterior: `uv venv`, activa `.venv` igual que
arriba y `uv pip install -r requirements.txt`.

## Cómo correrlo

Todos los comandos se corren desde la raíz del repositorio clonado (en el repositorio
de la fábrica, esa raíz es la carpeta `product/`).

Ejemplo mínimo, sin cuentas y con el modelo simulado. Primero define `API_KEYS` con
un cliente y una clave de ejemplo (elige tu propia clave y no la subas al
repositorio).

En PowerShell:

```powershell
$env:API_KEYS = "local:clave-de-ejemplo"
python -m uvicorn app.main:app --no-access-log
```

En bash:

```bash
export API_KEYS="local:clave-de-ejemplo"
python -m uvicorn app.main:app --no-access-log
```

Abre `http://127.0.0.1:8000/` y escribe `clave-de-ejemplo` en el campo «Clave de
acceso». Se recomienda `--no-access-log` para que la salida estándar tenga solo las
líneas JSON del producto.

Por omisión usa el modelo simulado (`MODEL_PROVIDER=fake`): no hace falta red ni
cuenta. Para el modelo real, copia `.env.example` a `.env`, pon
`MODEL_PROVIDER=gateway` y completa `CF_ACCOUNT_ID`, `CF_GATEWAY_ID` y `CF_API_TOKEN`
(el token es secreto: nunca lo subas al repositorio). El producto lee las variables
del entorno; para cargarlas desde el archivo, arranca con
`uvicorn app.main:app --no-access-log --env-file .env` (la opción `--env-file` usa
`python-dotenv`, que ya está en `requirements.txt`).

Para preguntar hace falta una clave: define `API_KEYS` en tu `.env` con la forma
`cliente:clave,cliente2:clave2` y escribe tu clave en el campo «Clave de acceso» de la
página. La página la guarda solo en `sessionStorage` (se borra al cerrar la pestaña) y
la manda en el encabezado `X-API-Key`. Sin `API_KEYS`, nadie puede preguntar.

## Rutas

| Ruta | Clave | Para qué |
| --- | --- | --- |
| `GET /` | no | Página web; muestra el id de cada respuesta |
| `GET /health` | no | `{"status": "ok", "pid": ...}` |
| `/docs` | no | Documentación interactiva de la API |
| `POST /ask` | sí | `{"question", "history"}` y responde `{answer, steps, tools_used, input_tokens, output_tokens, request_id, model, route, cached_calls, cost_usd}` |
| `GET /metrics` | sí | Métricas de este proceso: peticiones, tasa de error, p50/p95, tokens, `cost_usd` acumulado y SLO |

Si el gateway falla (red, tiempo de espera, `4xx/5xx` o cuerpo inválido), `POST /ask`
responde `502 {"detail": "model unavailable", "request_id": ...}`.

## Acceso y límite de peticiones

- Sin `X-API-Key` o con una clave que no está en `API_KEYS`: `401 {"detail": "invalid
  or missing API key"}`. La página muestra «Clave inválida».
- Más de `RATE_LIMIT_PER_MINUTE` peticiones de un mismo cliente en los últimos 60
  segundos: `429 {"detail": "rate limit exceeded"}` con `Retry-After` (segundos que
  faltan). La página muestra «Demasiadas preguntas; espera N segundos». El límite es
  por cliente y vive en la memoria del proceso.
- El nombre del cliente queda en el log (`client` en `request`, `agent_run`, `audit` y
  `error`) y en los metadatos de la traza. La clave nunca se escribe en el log, en la
  traza ni en un mensaje de error: si `API_KEYS` está mal formada, el error dice el
  número de la entrada y su largo, no su valor.
- Las claves se comparan con `hmac.compare_digest`.

## Variables de entorno

| Variable | Por omisión | Para qué |
| --- | --- | --- |
| `MODEL_PROVIDER` | `fake` | `fake` (simulado, sin red) o `gateway` (Workers AI por AI Gateway) |
| `AGENT_MAX_STEPS` | `3` | Tope de llamadas al modelo por pregunta |
| `MAX_QUESTION_CHARS` | `2000` | Largo máximo de la pregunta |
| `EMPLOYEES_PATH` | `data/employees.json` | Archivo de empleados (relativo a la raíz del repositorio) |
| `SERVICE_NAME` | `hr-assistant` | Campo `service` del log |
| `SLO_P95_MS` | `2000` | Meta de latencia p95 en milisegundos |
| `LANGSMITH_TRACING` | `false` | Enciende las trazas (requiere `LANGSMITH_API_KEY`) |
| `LANGSMITH_API_KEY` | sin valor | Clave de LangSmith; se lee del entorno y nunca se registra |
| `HIDE_INPUTS` / `HIDE_OUTPUTS` | `true` | No mandar a LangSmith preguntas ni respuestas |
| `CF_ACCOUNT_ID` | sin valor | Cuenta de Cloudflare (obligatoria con `gateway`) |
| `CF_GATEWAY_ID` | `default` | Id del AI Gateway (obligatorio con `gateway`) |
| `CF_API_TOKEN` | sin valor | Token de Cloudflare; secreto, nunca se registra |
| `MODEL_SMALL` | `@cf/meta/llama-3.1-8b-instruct-fast` | Modelo barato |
| `MODEL_LARGE` | `@cf/meta/llama-3.3-70b-instruct-fp8-fast` | Modelo capaz |
| `ROUTING` | `true` | Enrutamiento por pregunta |
| `ROUTER_MAX_CHARS` | `80` | Preguntas más largas van al modelo capaz |
| `HISTORY_WINDOW` | `6` | Mensajes de historial que se mandan al modelo (0: ninguno) |
| `MODEL_MAX_TOKENS` | `300` | Tope de tokens de salida por llamada |
| `MODEL_TEMPERATURE` | `0` | Temperatura; con 0 las evaluaciones son repetibles |
| `CACHE_TTL_SECONDS` | `0` | Caché del gateway en segundos (0: apagada) |
| `PRICES_PATH` | `data/model_prices.json` | Precios por modelo en USD por millón de tokens |
| `ENVIRONMENT` | `development` | `development` o `production`; con `production` se aplican las reglas de compliance |
| `API_KEYS` | vacía | Clientes y claves, `cliente:clave,cliente2:clave2`; secreto, nunca se registra |
| `RATE_LIMIT_PER_MINUTE` | `30` | Peticiones por cliente por minuto |
| `LOG_LEVEL` | `info` | `info` o `debug` (sin distinguir mayúsculas); `debug` está prohibido en producción |

Un valor inválido (por ejemplo `SLO_P95_MS=0` o `LANGSMITH_TRACING=quizas`) impide
arrancar. Sin `LANGSMITH_API_KEY` el producto funciona igual y no intenta conectarse.
Con `MODEL_PROVIDER=gateway`, faltar cualquiera de las variables `CF_*` impide arrancar;
también lo impide que `MODEL_SMALL` o `MODEL_LARGE` no tengan precio en `PRICES_PATH`.
Un `API_KEYS` mal formado (entrada sin `:`, cliente o clave vacíos, cliente o clave
repetidos), un `ENVIRONMENT` desconocido, `RATE_LIMIT_PER_MINUTE` menor que 1 o un
`LOG_LEVEL` distinto de `info` y `debug` también impiden arrancar.

Con `ENVIRONMENT=production` el producto no arranca si `MODEL_PROVIDER=fake`, si
`API_KEYS` está vacía o alguna clave tiene menos de 16 caracteres, si
`LOG_LEVEL=debug`, o si `LANGSMITH_TRACING=true` y `HIDE_INPUTS` o `HIDE_OUTPUTS` no
valen `true`. El detalle está en `doc/compliance-checklist.md`.

## Palancas de costo

1. **Enrutamiento**: una regla en código manda a `MODEL_LARGE` las preguntas de más de
   `ROUTER_MAX_CHARS` caracteres o con «compara», «resume», «explica», «por qué»,
   «analiza» o «todos» (sin distinguir mayúsculas ni tildes); el resto va a
   `MODEL_SMALL`. `route` dice el motivo: `routing_off`, `long_question`,
   `keyword:<palabra>` o `short_question`.
2. **Ventana de historial**: solo se mandan los últimos `HISTORY_WINDOW` mensajes del
   historial; la pregunta y las herramientas del turno actual siempre van.
3. **Tope de salida**: `MODEL_MAX_TOKENS` en cada llamada.
4. **Caché del gateway**: con `CACHE_TTL_SECONDS` mayor que 0 se manda
   `cf-aig-cache-ttl`; si el gateway responde `cf-aig-cache-status: HIT`, la llamada
   cuenta en `cached_calls` y no cuesta.

`cost_usd = (entrada * precio_entrada + salida * precio_salida) / 1 000 000` con el
precio del modelo enrutado. Los dos modelos simulados se llaman como `MODEL_SMALL` y
`MODEL_LARGE`: responden igual pero se cobran con su precio, así las palancas se miden
sin red y sin gastar cuota.

## Cómo rastrear una petición

1. La persona copia el id que muestra la página ("Id de la petición: ...") o el
   encabezado `X-Request-ID` de la respuesta. El cliente puede mandar su propio
   `X-Request-ID` (1 a 128 caracteres de `A-Z a-z 0-9 . _ : -`); si no, se genera un
   UUID.
2. Se buscan en el log las líneas con ese `request_id`: `request` (método, ruta,
   estado y latencia), `agent_run` (conteos, sin texto), `audit` (cada herramienta y
   sus argumentos) y, si algo falló, `error` (el tipo de la excepción y, con
   `LOG_LEVEL=debug`, sus `frames`; nunca el mensaje).
3. `GET /metrics` muestra cómo va el proceso frente al SLO.

## Modo debug

Con `LOG_LEVEL=debug` (solo en local o staging) el log explica un fallo paso a paso sin
reproducirlo. Con `info` (por omisión) el log es exactamente el de la sesión 2. En
`debug` se agregan, con los mismos campos comunes (`ts`, `service`, `event`,
`request_id`):

- `startup`, al arrancar, con `request_id` igual a `"-"`: `environment`,
  `model_provider`, `log_level` y `credentials`, una lista en orden fijo como
  `["API_KEYS=set", "CF_API_TOKEN=unset", "LANGSMITH_API_KEY=unset"]`. De cada secreto
  solo se dice `set` o `unset`, nunca su valor.
- `agent_step`, uno por paso del agente: `step` (desde 1), `tools` (solo los nombres)
  y `latency_ms`.
- `model_call`, uno por llamada al modelo: `model`, `status` (`ok` o `error`),
  `latency_ms`, `input_tokens`, `output_tokens` y `cached`.
- En el evento `error` (del `500` y del `502`), `frames`: la lista de
  `"archivo.py:línea:función"` del stack trace, con el nombre corto del archivo.

Lo que nunca sale, en ningún nivel:

- Los eventos de debug llevan solo los campos de su lista blanca: nunca encabezados,
  entorno, configuración ni la petición o respuesta HTTP del gateway.
- Ni el mensaje de una excepción ni sus variables locales, ni el texto de una pregunta
  o una respuesta.
- Todo evento pasa por un redactor antes de escribirse: un campo cuyo nombre contenga
  `authorization`, `api_key`, `api-key`, `token` (salvo `input_tokens` y
  `output_tokens`), `secret`, `password` o `cookie` vale `"[REDACTED]"`, también en
  diccionarios y listas anidados; cada clave de `API_KEYS`, `CF_API_TOKEN` y
  `LANGSMITH_API_KEY` se reemplaza por `"[REDACTED]"` aunque esté dentro de un texto,
  y `Bearer <algo>` pasa a `Bearer [REDACTED]`.
- Los loggers de `httpx` y `httpcore` quedan en `WARNING` aunque el producto esté en
  `debug`, porque en su nivel `DEBUG` imprimen encabezados.

`debug` no cambia `HIDE_INPUTS` ni `HIDE_OUTPUTS`. Con `ENVIRONMENT=production`,
`LOG_LEVEL=debug` impide arrancar: en producción se depura con el `request_id`.

## Pruebas

Desde la raíz del repositorio clonado, con el entorno virtual activo. Son los mismos
comandos que corre el pipeline de CI (`.github/workflows/ci.yml`).

Estilo y análisis estático (pylint con 88 columnas):

```bash
python -m pylint app tests scripts/smoke.py --max-line-length=88 --fail-under=10 \
  --disable=missing-function-docstring,redefined-outer-name,too-few-public-methods
```

En PowerShell, cambia la `\` del final de la primera línea por un acento grave
(`` ` ``) o escribe todo en una sola línea.

Pruebas unitarias y de comportamiento con cobertura de 80 % o más (sin red):

```bash
python -m pytest tests -q --cov=app --cov-fail-under=80
```

Pruebas de punta a punta con Playwright (`e2e/`: enviar una pregunta y ver su
`request_id`, error en español con pregunta vacía, la conversación se mantiene en
pantalla). Necesitan el Chromium de Playwright (ver «Instalación») y el producto
corriendo con el modelo simulado en otra terminal. Las pruebas leen la clave de
`E2E_API_KEY`, que debe estar en `API_KEYS`; el límite de peticiones se sube como en
el CI para que no las corte.

Terminal 1, en bash (arranca el producto):

```bash
export MODEL_PROVIDER=fake RATE_LIMIT_PER_MINUTE=1000
export API_KEYS="e2e:clave-de-ejemplo"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --no-access-log
```

Terminal 2, en bash (corre las pruebas):

```bash
export E2E_API_KEY="clave-de-ejemplo"
python -m pytest e2e -q --base-url http://127.0.0.1:8000
```

En PowerShell las variables se definen con `$env:NOMBRE = "valor"` (por ejemplo
`$env:E2E_API_KEY = "clave-de-ejemplo"`) y los comandos `python` son los mismos.

En el repositorio de la fábrica existen además las compuertas
`uv run python -m verification <paso>` (`unit`, `contract`, `qa`, `e2e` y
`evaluate`); no forman parte de este repositorio.

## Contenedor y publicación

### Imagen en local

`Dockerfile` usa `python:3.12-slim`, instala `requirements.txt`, copia solo `app/` y
`data/`, y corre como el usuario sin privilegios `appuser`. Arranca con
`uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}` (8000 si no hay `PORT`).
`.dockerignore` deja fuera `.env`, `tests/`, `e2e/` y los cachés.

Desde la raíz del repositorio clonado:

```bash
docker build -t hr-assistant .
docker run --rm -p 8000:8000 --env-file .env hr-assistant
```

Las variables (entre ellas `API_KEYS`) se pasan con `--env-file .env`, no escritas en
el comando, para que ninguna clave quede en el historial de la terminal. Abre
`http://127.0.0.1:8000/`.

### Pipeline de CI

`.github/workflows/ci.yml` corre en cada push y en cada pull request. Tiene cuatro
trabajos encadenados con `needs`, que se ven por separado en la pestaña Actions de
GitHub; si uno falla, los siguientes no corren:

1. `style`: pylint sobre `app`, `tests` y `scripts/smoke.py` con 88 columnas.
2. `unit` (`needs: style`): pruebas unitarias y BDD con cobertura de 80 % o más.
3. `e2e` (`needs: unit`): arranca el producto con el modelo simulado y corre Playwright
   (`e2e/`). La clave es un texto de ejemplo que solo existe en esa corrida.
4. `docker` (`needs: e2e`): `docker build` de la imagen y comprueba que la imagen
   responde en `/health`.

### Publicar en Render

`render.yaml` es un Blueprint con un servicio web: `runtime: docker`, `plan: free` y
`healthCheckPath: /health`. El servicio se llama igual que el repositorio, para no
pisar otro servicio que ya exista en la cuenta de Render.

1. Sube el repositorio a GitHub (lo hace `scripts/publish.py` después de que una
   persona aprueba la publicación).
2. En Render, **New > Blueprint** y elige el repositorio.
3. Render pide los secretos marcados con `sync: false`: `API_KEYS`, `CF_ACCOUNT_ID` y
   `CF_API_TOKEN`. Se escriben solo en el panel de Render, nunca en el repositorio. En
   producción cada clave de `API_KEYS` debe tener 16 caracteres o más.
4. El resto ya viene en `render.yaml`: `ENVIRONMENT=production`,
   `MODEL_PROVIDER=gateway`, `HIDE_INPUTS=true`, `HIDE_OUTPUTS=true` y
   `CF_GATEWAY_ID=default`. Con `ENVIRONMENT=production` el producto se niega a
   arrancar si la configuración no cumple `doc/compliance-checklist.md`.
5. `LANGSMITH_API_KEY` no está en el Blueprint porque es opcional: si se encienden las
   trazas, se agrega en **Render > Environment**.

Con `autoDeployTrigger: checksPass`, Render publica cada cambio solo cuando el pipeline
de CI pasa.

### Prueba de humo

`scripts/smoke.py <url>` comprueba tres cosas e imprime `[OK]` o `[FAIL]` en cada una:
`GET /health` responde `200`, `POST /ask` sin clave responde `401` y `POST /ask` con
clave responde `200`. La clave se lee de la variable `SMOKE_API_KEY`, nunca de un
argumento, y no se imprime.

Define la variable en la terminal sin que la clave quede escrita en el comando ni en el
historial, y luego corre la prueba desde la raíz del repositorio clonado.

En bash:

```bash
read -rs SMOKE_API_KEY && export SMOKE_API_KEY
python scripts/smoke.py https://<servicio>.onrender.com
```

En PowerShell:

```powershell
$env:SMOKE_API_KEY = Read-Host -MaskInput "Clave"
python scripts/smoke.py https://<servicio>.onrender.com
```

Termina con código 0 si todo pasa, 1 si algo falla y 2 si falta la URL o
`SMOKE_API_KEY`. En el repositorio de la fábrica (no en este), la misma prueba corre
con `uv run python -m verification production <url>`. El servicio `free` de Render se
duerme cuando no tiene tráfico; la prueba espera hasta 90 segundos a que despierte.

## Documentación

La arquitectura está en `doc/architecture.md`, las decisiones en `doc/adr/` y las
reglas de producción en `doc/compliance-checklist.md`.
