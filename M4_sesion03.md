Certificado · Next-Gen Coding: Desarrollo de Software con IA Generativa (Virtual)

**Módulo 4 · Agentes en producción · Manual de práctica**

# Agentes en producción · Sesión 3 · Costos

Especialistas en paralelo

Una fábrica de agentes de Claude Code construye el HR Assistant, lo prueba, lo revisa y lo publica. Tú diriges, apruebas y compruebas.

**CONTENIDO**

1. Cómo usar esta guía

2. Requisitos para todo el módulo

3. Sesión 3 · Costos: especialistas en paralelo

4. Estructura final de la carpeta

5. Resumen de los pasos

6. Si algo falla

7. Lista de comprobación

## Cómo usar esta guía

En este módulo construyes, con tus manos, una **fábrica de agentes** de Claude Code. Después la fábrica construye sola el producto (el HR Assistant), lo prueba, lo revisa contra `QA.md` y, en la sesión 4, lo publica cuando tú lo apruebas. Tú no escribes el producto: escribes los agentes, el orquestador, los hooks y las verificaciones que lo construyen.

Es **incremental**: la sesión 1 parte de una carpeta vacía; cada sesión copia la carpeta anterior y le agrega piezas. Lo que construyas hoy es el punto de partida de la siguiente sesión.

| Concepto | Detalle |
|---|---|
| Sesión | 3 de 4 · Costos |
| Hoy | Especialistas en paralelo, coordinados por un supervisor |
| Patrón de la fábrica | Multiagente: supervisor con especialistas en paralelo |
| Duración | 2 h 30 min, con tiempos pesimistas |
| Carpeta | `NextGenCode-M4-Agentes/sesion03` |

Cada paso tiene tres partes:

- **Escribe:** el archivo completo, con su ruta; tu editor crea las carpetas al guardar. **Reemplaza** quiere decir que el archivo ya existe y cambia: pega la versión nueva completa encima de la anterior.

- **Ejecuta:** el comando para probar ese paso, para macOS / Linux y para Windows.

- **Observa:** lo que debe salir y la idea que deja.

> **CUIDADO**
>
> **Copia el código del archivo Markdown, no del PDF.** Junto con este PDF recibes `M4_sesion03.md`, con el mismo contenido. Al copiar de un PDF, los visores pierden la sangría, y en Python la sangría es parte del código. Lee en el PDF y copia del `.md` (ábrelo en tu editor).

No avances hasta que el paso anterior funcione. Casi todo se prueba sin el modelo (hooks y verificaciones son Python normal); solo los pasos con «Sí» en la columna «Llama al modelo» (resumen al final) gastan cuota de tu suscripción de Claude Code.

## Requisitos para todo el módulo

Este capítulo es igual en todos los manuales del módulo. Reúne **todo** lo que necesitas para las cuatro sesiones: cuentas, programas y datos que vas a sacar de cada cuenta. Resuélvelo **antes de la primera sesión**: si algo falta, la sesión se va en instalar y no en dirigir la fábrica.

| Sesión | Tema | Patrón de la fábrica | Cuenta que se usa por primera vez |
|---|---|---|---|
| 1 | Arquitectura | Razonamiento: plan y ejecución | GitHub y Claude Code |
| 2 | Observabilidad | Flujo: compuertas y evaluador-optimizador | LangSmith (opcional) |
| 3 | Costos | Multiagente: supervisor y paralelo | Cloudflare |
| 4 | Producción | Humano en el lazo y triage | Render |

Las cuentas de GitHub, Cloudflare, LangSmith y Render son **gratuitas** y no pidieron tarjeta al preparar el curso (noviembre de 2026). **Claude Code** es la excepción: necesita un plan **Pro o Max**, porque es el motor de la fábrica. No hace falta una clave de la API de Anthropic.

### Equipo

- Una computadora con **Windows 10 u 11**, **macOS** o **Linux**, con permiso para instalar programas.

- Conexión a internet: los agentes trabajan en la nube de Anthropic.

- Un navegador actualizado (Chrome, Edge, Firefox o Safari).

### Programas obligatorios

| Programa | Para qué | Comprobación |
|---|---|---|
| Git | Guardar versiones y publicar el producto | `git --version` |
| uv | Instalar Python 3.12 y las dependencias; correr todo con `uv run` | `uv --version` |
| Python 3.12 (lo instala uv) | El lenguaje de la fábrica y del producto | `uv run --python 3.12 python -- version` |
| GitHub CLI (`gh`) | Publicar el producto en tu repositorio (sesión 4) | `gh --version` |
| Claude Code | El motor de la fábrica: sus agentes, skills y hooks | `claude --version` |
| Un editor de código | Leer lo que escriben los agentes (sugerido: VS Code) | Abre la carpeta |

**Instalar Git**

**macOS / Linux**

```bash
# macOS (abre el instalador de herramientas de Apple)
xcode-select --install
# Linux (Debian / Ubuntu)
sudo apt install git
```

**Windows (PowerShell)**

```powershell
winget install --id Git.Git -e
```

**Instalar uv y Python 3.12**

**macOS / Linux**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv python install 3.12
```

**Windows (PowerShell)**

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
uv python install 3.12
```

Cierra y vuelve a abrir la terminal después de instalar uv. En todo el módulo usamos `uv run ...`: así no importa qué `python` traiga tu sistema. En macOS, `python3` suele ser la versión 3.9 de Apple y **no sirve**. No actives otros entornos virtuales en la misma terminal: `uv run` usaría ese y no el de la sesión.

**Instalar GitHub CLI e iniciar sesión**

**macOS / Linux**

```bash
# macOS (con Homebrew)
brew install gh
# Linux: sigue https://github.com/cli/cli#installation
gh auth login
```

**Windows (PowerShell)**

```powershell
winget install --id GitHub.cli -e
gh auth login
```

En `gh auth login` elige **GitHub.com**, **HTTPS** y **Login with a web browser**. Comprueba con `gh auth status`.

**Instalar Claude Code e iniciar sesión con tu plan**

**macOS / Linux**

```bash
curl -fsSL https://claude.ai/install.sh | bash
claude auth login
```

**Windows (PowerShell)**

```powershell
irm https://claude.ai/install.ps1 | iex
claude auth login
```

Si tienes la variable `ANTHROPIC_API_KEY` definida, quítala antes de `claude auth login`: Claude Code la usaría en lugar de tu suscripción y te cobraría por uso.

**macOS / Linux**

```bash
unset ANTHROPIC_API_KEY
```

**Windows (PowerShell)**

```powershell
Remove-Item Env:ANTHROPIC_API_KEY -ErrorAction SilentlyContinue
```

### Programas opcionales

| Programa | Para qué | Por qué es opcional |
|---|---|---|
| Docker Desktop | Probar el contenedor de la sesión 4 en tu máquina | Render y GitHub Actions construyen el contenedor en la nube |
| Un gestor de contraseñas | Guardar las claves que vas a generar | Muy recomendado: las claves no van en notas, chats ni capturas |

### Cuentas

Para cada cuenta, la tabla dice qué dato sacas y si es **secreto**. Un dato secreto nunca se pega en un chat (tampoco en el de Claude Code), un ticket, una captura de pantalla ni un comando: va en el archivo `.env` de tu máquina o en el panel de Render.

| Cuenta | Sesión | Dato que sacas | ¿Secreto? |
|---|---|---|---|
| Claude | 1 | Plan Pro o Max; `claude auth login` hecho | No |
| GitHub | 1 | Tu usuario y `gh auth login` hecho | No |
| LangSmith | 2 | API key de tipo *Tracing Only* (opcional) | **Sí** |
| Cloudflare | 3 | Account ID | No |
|  | 3 | API token de Workers AI | **Sí** |
|  | 3 | Nombre del AI Gateway: `default` | No |
| Render | 4 | Cuenta creada **con GitHub** | No |

**GitHub**

1. Crea la cuenta en github.com (plan Free) y confirma tu correo.

2. Instala GitHub CLI y corre `gh auth login` (arriba).

En la sesión 4 la fábrica publica el producto en **tu propio** repositorio privado; ahí corre el pipeline de CI y de ahí lo toma Render.

**LangSmith (trazas del producto, opcional)**

1. Crea la cuenta en smith.langchain.com (plan Developer, gratuito).

2. Ve a **Settings > API Keys > Create API Key** y elige el tipo **Tracing Only**: solo puede *escribir* trazas. Si tu cuenta no lo muestra, usa **Personal Access Token**.

3. Copia la clave **en tu gestor de contraseñas**. Por lo general solo se muestra una vez.

**Cloudflare (el modelo real del producto)**

1. Crea la cuenta en dash.cloudflare.com (plan Free) y confirma tu correo. No necesitas un dominio.

2. En el menú izquierdo entra a **AI > Workers AI** y elige **Use REST API**.

3. Copia el **Account ID**: 32 caracteres de números y letras de la `a` a la `f`. **No es tu correo.** También aparece en la URL: `dash.cloudflare.com/<ACCOUNT_ID>/...`.

4. Pulsa **Create a Workers AI API Token** y crea el token. Guárdalo en tu gestor de contraseñas: es secreto y solo se muestra una vez.

5. Entra a **AI > AI Gateway**. Debe existir un gateway llamado `default`; si no, pulsa **Create Gateway** y nómbralo `default`.

El plan gratuito da **10,000 neuronas al día** (se reinician a las 00:00 UTC). Al terminarse, las llamadas fallan; no se cobran. La fábrica prueba con el modelo simulado, así que casi no gasta cuota.

**Render (publicar el producto)**

1. Entra a render.com y elige **Sign up with GitHub**. Así Render puede leer tus repositorios.

2. Elige el plan **Free** (Hobby). No pidió tarjeta al preparar el curso.

El plan gratuito **duerme** el servicio tras 15 minutos sin uso: la primera petición después tarda cerca de un minuto. Es normal.

### Tu carpeta de trabajo

No clonas nada: construyes la fábrica tú, desde una carpeta vacía llamada `NextGenCode-M4-Agentes`, con una subcarpeta por sesión (`sesion01` a `sesion04`). El paso 0 de la sesión 1 la crea. Cada sesión copia la anterior y le agrega piezas; el producto lo construyen los agentes en `product/`.

### Confía en la carpeta (una vez)

La primera vez que abres `claude` en tu carpeta de trabajo, pregunta **«Do you trust the files in this folder?»**. Responde que sí. Sin esa confianza, Claude Code ignora los permisos de `.claude/settings.json` y los agentes no pueden correr las verificaciones. Hazlo en una terminal normal, no con un comando que corra `claude` sin pantalla.

### Lista de comprobación

Corre esto en una terminal nueva. Todo debe responder sin error.

```text
git --version
uv --version
uv run --python 3.12 python --version
gh --version
gh auth status
claude --version
```

- [ ] Git, uv, Python 3.12 y Claude Code responden
- [ ] `gh auth status` dice que entraste a github.com
- [ ] `claude auth login` hecho con mi plan Pro o Max
- [ ] Cloudflare: Account ID y token guardados; existe el gateway `default`
- [ ] Render: cuenta creada con GitHub

## Sesión 3 · Costos: especialistas en paralelo

Hoy la fábrica agrega el modelo real (Workers AI vía AI Gateway) y cuatro palancas de costo. Dos especialistas trabajan **al mismo tiempo**, coordinados por un supervisor, y un programa decide si las palancas se quedan.

```mermaid
flowchart TD
  qaunit["qa-unit"] --> costs["costs · palancas"]
  qaunit --> e2e["qa-e2e · Playwright"]
  costs --> join(("unión"))
  e2e --> join
  join --> ver{"unit, contract, qa, e2e, evaluate"}
  ver -- "falla: el supervisor decide quién corrige" --> costs
  ver --> style{"qa-style"}
  style --> lista(["LISTA"])
```

### Paso 0 · Copia la sesión 2 (10 min)

**Ejecuta**

**macOS / Linux**

```bash
cd ..
rsync -a --exclude .venv --exclude output --exclude '__pycache__' sesion02/ sesion03/
cd sesion03
uv venv --python 3.12
```

**Windows (PowerShell)**

```powershell
cd ..
robocopy sesion02 sesion03 /E /XD .venv output __pycache__
cd sesion03
uv venv --python 3.12
```

**Observa:** `sesion03` tiene la fábrica **y el producto** de la sesión 2 (`product/`): es el punto de partida. El entorno virtual se crea de nuevo porque guarda rutas absolutas. Abre `claude` una vez y acepta la confianza de la carpeta.

Se agrega pytest-playwright:

**Reemplaza (versión nueva completa)** `requirements.txt`

```text
# Lo que usa la fábrica (hooks, verificación) y lo que puede usar el producto.
# El producto no instala nada por su cuenta: todo vive en este mismo entorno.
fastapi>=0.115
uvicorn>=0.30
pydantic>=2.7
httpx>=0.27
pytest>=8
pytest-bdd>=7
pytest-cov>=5
pylint>=3
langsmith>=0.1
pytest-playwright>=0.5
```

**Ejecuta**

**Todos los sistemas**

```bash
uv pip install -r requirements.txt
uv run playwright install chromium
```

### Paso 1 · La especificación de costos y sus datos (10 min)

**Escribe** `spec/03-costs.md`

```markdown
# Sesión 3 · Costos: abaratar cada respuesta sin empeorarla

Parte del producto de las sesiones 1 y 2. Agrega el modelo real (Cloudflare Workers AI a través de AI Gateway) y
cuatro palancas de costo. Cada palanca se mide: si baja la calidad, no se usa.

## Lo que debe hacer

1. **Modelo real** con `MODEL_PROVIDER=gateway`: llama a
   `https://gateway.ai.cloudflare.com/v1/{CF_ACCOUNT_ID}/{CF_GATEWAY_ID}/workers-
ai/v1/chat/completions`
   con `Authorization: Bearer {CF_API_TOKEN}` y el cuerpo `{"model", "messages", "max_tokens", "temperature"}`.
   - Los tokens se leen de `usage.prompt_tokens` y `usage.completion_tokens`.
   - Si la llamada falla, la API responde `502 {"detail": "model unavailable", "request_id": ...}`.
   - Con `gateway`, faltar cualquiera de las tres variables `CF_*` impide arrancar.
2. **Palanca 1: enrutamiento.** Una regla en código (no otro modelo) elige el modelo por pregunta:
   - `MODEL_LARGE` si `ROUTING=false`, si la pregunta pasa de `ROUTER_MAX_CHARS` caracteres, o si contiene
     «compara», «resume», «explica», «por qué», «analiza» o «todos».
   - `MODEL_SMALL` en cualquier otro caso.
3. **Palanca 2: ventana de historial.** Al modelo solo se mandan los últimos `HISTORY_WINDOW` mensajes del historial.
4. **Palanca 3: tope de salida.** `MODEL_MAX_TOKENS` en cada llamada.
5. **Palanca 4: caché de AI Gateway.** Con `CACHE_TTL_SECONDS` mayor que 0 se manda el encabezado
   `cf-aig-cache-ttl`. Si el gateway responde `cf-aig-cache-status: HIT`, esa llamada cuenta como cacheada y no cuesta.
6. **Costo por respuesta.** Con los precios de `data/model_prices.json` (copia de `spec/model_prices.json`, en USD por
   millón de tokens). `POST /ask` agrega a su respuesta `model`, `route` (el motivo del enrutador), `cached_calls`
   y `cost_usd`. `/metrics` agrega `cost_usd` acumulado.
7. **El modelo simulado también tiene precio.** Con `MODEL_PROVIDER=fake` hay dos modelos simulados que se llaman como
   `MODEL_SMALL` y `MODEL_LARGE`. Responden igual, pero el costo se calcula con el precio de su nombre. Así las palancas
   se pueden medir sin red y sin gastar cuota.

## Configuración nueva

| Variable | Por omisión | Para qué |
| --- | --- | --- |
| `CF_ACCOUNT_ID`, `CF_GATEWAY_ID`, `CF_API_TOKEN` | vacías, `default`, vacía | Cuenta, gateway y token de Cloudflare (el token es secreto) |
| `MODEL_SMALL` | `@cf/meta/llama-3.1-8b-instruct-fast` | Modelo barato |
| `MODEL_LARGE` | `@cf/meta/llama-3.3-70b-instruct-fp8-fast` | Modelo capaz |
| `ROUTING` | `true` | Enrutamiento por pregunta |
| `ROUTER_MAX_CHARS` | `80` | Preguntas más largas van al modelo capaz |
| `HISTORY_WINDOW` | `6` | Mensajes de historial que se mandan |
| `MODEL_MAX_TOKENS` | `300` | Tope de tokens de salida |
| `MODEL_TEMPERATURE` | `0` | Con 0 las evaluaciones son repetibles |
| `CACHE_TTL_SECONDS` | `0` | Caché del gateway (0: apagada) |
| `PRICES_PATH` | `data/model_prices.json` | Precios por modelo |

Se agrega `.env.example` con todas las variables del producto, sin valores secretos.

## Pruebas de punta a punta (las escribe `qa-e2e`)

En `product/e2e/`, con pytest-playwright y el producto corriendo con el modelo simulado:

- Escribir una pregunta, enviarla y ver la respuesta y su `request_id`.
- Una pregunta vacía muestra un mensaje de error en español.
- Una segunda pregunta mantiene la conversación anterior en pantalla.

## Cómo se comprueba

- `verification unit`, `contract` y `qa`, como en la sesión 2.
- `uv run python -m verification e2e`: las pruebas de Playwright pasan.
- `uv run python -m verification evaluate`: corre el set de evaluación dos veces con el modelo simulado.
  - **Línea base:** `ROUTING=false` y sin ventana.
  - **Con palancas:** la configuración por omisión.
  - Pasa solo si la calidad no baja y el costo sí baja.
```

Precios de Workers AI por millón de tokens (verifícalos antes de clase):

**Escribe** `spec/model_prices.json`

```json
{
  "currency": "USD",
  "unit": "per million tokens",
  "source": "https://developers.cloudflare.com/workers-ai/platform/pricing/",
  "checked": "2026-11-04 (verify before class: prices change)",
  "models": {
    "fake": {"input": 0.0, "output": 0.0},
    "@cf/meta/llama-3.1-8b-instruct-fast": {"input": 0.045, "output": 0.384},
    "@cf/meta/llama-3.3-70b-instruct-fp8-fast": {"input": 0.293, "output": 2.253}
  }
}
```

El set de evaluación: preguntas y lo que debe contener cada respuesta:

**Escribe** `verification/eval_set.json`

```json
[
  {
    "question": "¿Quién es EMP-0004?",
    "must_include": [
      "Jorge Díaz"
    ]
  },
  {
    "question": "¿Qué puesto tiene EMP-0005?",
    "must_include": [
      "Contadora"
    ]
  },
  {
    "question": "¿Quiénes trabajan en el departamento de Finanzas?",
    "must_include": [
      "Sofía Gómez"
    ]
  },
  {
    "question": "Lista el departamento de Tecnología",
    "must_include": [
      "Ana López",
      "Jorge Díaz"
    ]
  },
  {
    "question": "¿Sigue activa Marta Ruiz? Su número es EMP-0003",
    "any_of": [
      "baja",
      "no está activa",
      "no sigue activa",
      "inactiva",
      "ya no"
    ]
  },
  {
    "question": "¿En qué año ingresó EMP-0002?",
    "must_include": [
      "2021"
    ]
  },
  {
    "question": "¿Quién es EMP-0099?",
    "any_of": [
      "no existe",
      "no se encontr",
      "no encontr",
      "sin resultados",
      "no hay",
      "no tengo"
    ]
  },
  {
    "question": "¿Qué clima hace hoy en Monterrey?",
    "any_of": [
      "RH",
      "Recursos Humanos",
      "empleado"
    ]
  }
]
```

### Paso 2 · Dos especialistas (15 min)

**Escribe** `.claude/agents/costs.md`

```markdown
---
name: costs
description: >-
  Agrega el modelo real (Workers AI vía AI Gateway) y las palancas de costo
  (enrutamiento, ventana, tope de salida, caché, costo por respuesta) según
  spec/03-costs.md. No escribe pruebas. Corre en paralelo con qa-e2e.
tools: Read, Glob, Grep, Write, Edit, Bash
---
Eres el ingeniero de costos del HR Assistant.

1. Lee `spec/` (sobre todo `03-costs.md`), `output/plan.md`, el código de `product/app/`, las pruebas de
   `product/tests/` y `QA.md`.
2. Implementa lo que pide la especificación **sin romper** lo de las sesiones 1 y 2: el modelo `gateway`, las cuatro
   palancas, el costo por respuesta y los modelos simulados con nombre y precio. Copia `spec/model_prices.json` a
   `product/data/`, escribe `product/.env.example` y actualiza `product/README.md` y `product/requirements.txt`.
3. Para el modelo real usa `httpx`. En las pruebas nunca se llama a la red: por eso el cliente HTTP se inyecta.
4. Corre `uv run python -m verification unit` y `uv run python -m verification qa` hasta que pasen.
5. Si te pasan un error de la verificación o hallazgos de `qa-style`, corrígelos todos y di cómo.

Reglas: código en inglés, comentarios y docstrings en español (estilo Sphinx), líneas de máximo 88 caracteres, sin
emojis. **Nunca** escribas un token ni un id de cuenta reales: en `.env.example` van vacíos. No cambies la página web
ni las pruebas. Solo puedes escribir en `product/app/`, `product/data/`, `product/requirements.txt`,
`product/README.md` y `product/.env.example`.
Termina con la lista de archivos que cambiaste y el resultado de las pruebas.

En Bash solo puedes correr `uv run python -m verification <paso>`; para leer usa Read, Glob y Grep (nunca
`cat`, `grep` ni `cd` en Bash).
```

Prueba el producto desde el navegador, buscando elementos por `data-testid`:

**Escribe** `.claude/agents/qa-e2e.md`

```markdown
---
name: qa-e2e
description: >-
  Escribe pruebas de punta a punta con Playwright sobre la página web del
  producto en product/e2e/. No toca el código. Corre en paralelo con costs.
tools: Read, Glob, Grep, Write, Edit, Bash
---
Eres el ingeniero de QA de punta a punta. Pruebas el producto como lo usa una persona: desde el navegador.

1. Lee `spec/`, `QA.md` y la página `product/app/static/index.html` (para saber sus `data-testid`).
2. Escribe en `product/e2e/` las pruebas que pide la sección «Pruebas de punta a punta» de la especificación, con
   pytest-playwright (fixture `page`, y `page.goto("/")`: la URL base la pone la verificación).
   - Busca los elementos por `data-testid` (`page.get_by_test_id(...)`), no por textos ni estilos.
   - Usa `expect(...)` de Playwright, que espera solo; nunca `time.sleep`.
   - Nombres en inglés que se lean como frases. **Máximo 6 pruebas.**
3. Para probarlas, la verificación arranca el producto sola: corre `uv run python -m verification e2e`.
   Si una prueba falla porque la página no tiene lo que pide la especificación, **no la debilites**: dilo en tu resumen.

Escribe sin emojis. Solo puedes escribir en `product/e2e/`.
Termina con la lista de pruebas y el resultado de la verificación.

En Bash solo puedes correr `uv run python -m verification <paso>`; para leer usa Read, Glob y Grep (nunca
`cat`, `grep` ni `cd` en Bash).
```

### Paso 3 · El producto vivo, para cualquier verificación (15 min)

Lo que antes vivía en `conftest.py` se mueve aquí, para que lo usen el contrato, `e2e` y `evaluate`:

**Escribe** `verification/server.py`

```python
"""Arranca el producto con el modelo simulado para probarlo por HTTP.

Las verificaciones no importan el código del producto: le hablan como un
cliente, así que valen sin importar cómo lo haya escrito el agente.
"""

import os
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path

import httpx

PRODUCT = Path(__file__).resolve().parent.parent / "product"

@contextmanager
def running_product(port: int, **env: str):
    """Corre ``uvicorn app.main:app`` en ``port`` mientras dure el bloque."""
    settings = {**os.environ, "MODEL_PROVIDER": "fake", **env}
    command = [sys.executable, "-m", "uvicorn", "app.main:app", "--port", str(port)]
    server = subprocess.Popen(command, cwd=PRODUCT, env=settings)
    url = f"http://127.0.0.1:{port}"
    try:
        for _ in range(40):
            try:
                httpx.get(f"{url}/health", timeout=1)
                break
            except httpx.TransportError:
                time.sleep(0.25)
        yield httpx.Client(base_url=url, timeout=10)
    finally:
        server.terminate()
        server.wait(timeout=10)
```

**Reemplaza (versión nueva completa)** `verification/contract/conftest.py`

```python
"""El producto corriendo, para las pruebas de contrato."""

import pytest

from verification.server import running_product

@pytest.fixture(scope="session")
def api():
    """El producto con su configuración por omisión."""
    with running_product(8765) as client:
        yield client

@pytest.fixture(scope="session")
def api_one_step():
    """El producto con el bucle limitado a una sola vuelta."""
    with running_product(8766, AGENT_MAX_STEPS="1") as client:
        yield client
```

**Escribe** `verification/contract/test_contract_03.py`

```python
"""Contrato de la sesión 3: cada respuesta dice qué modelo usó y cuánto costó."""

def ask(api, question):
    return api.post("/ask", json={"question": question}).json()

def test_simple_questions_go_to_the_small_model(api):
    body = ask(api, "¿Quién es EMP-0004?")
    assert body["model"] == "@cf/meta/llama-3.1-8b-instruct-fast"
    assert body["cost_usd"] > 0

def test_complex_questions_go_to_the_large_model(api):
    body = ask(api, "Compara a los empleados del departamento de Finanzas")
    assert body["model"] == "@cf/meta/llama-3.3-70b-instruct-fp8-fast"
    assert body["route"]

def test_metrics_add_up_the_cost(api):
    ask(api, "¿Quién es EMP-0004?")
    assert api.get("/metrics").json()["cost_usd"] > 0
```

### Paso 4 · Costo contra calidad, y pruebas de punta a punta (15 min)

Corre el set dos veces (línea base y con palancas) y pasa solo si la calidad no baja y el costo sí:

**Escribe** `verification/evaluate.py`

```python
"""Compara costo y calidad: línea base contra la configuración con palancas.

Corre ``verification/eval_set.json`` contra el producto dos veces, con el modelo
simulado. Cada pregunta lleva un historial de relleno, como una conversación
larga. Pasa solo si la calidad no baja y el costo sí baja.
"""

import json
import sys
from pathlib import Path

from verification.server import running_product

EVAL_SET = Path(__file__).resolve().parent / "eval_set.json"
BASELINE = {"ROUTING": "false", "HISTORY_WINDOW": "1000"}
HISTORY = [
    {"role": role, "content": text}
    for _ in range(5)
    for role, text in (
        ("user", "Hola, necesito datos de un empleado del directorio de RH."),
        ("assistant", "Claro, dime el número de empleado o el departamento."),
    )
]

def is_correct(answer: str, case: dict) -> bool:
    """Indica si la respuesta cumple lo que pide el caso de evaluación."""
    if "must_include" in case:
        return all(text in answer for text in case["must_include"])
    return any(text.lower() in answer.lower() for text in case["any_of"])

def measure(client, cases: list[dict]) -> dict:
    """Pregunta cada caso y suma calidad y costo.

    :return: ``quality`` (fracción correcta), ``cost_usd`` e ``input_tokens``
    :rtype: dict
    """
    correct, cost, tokens = 0, 0.0, 0
    for case in cases:
        body = client.post(
            "/ask", json={"question": case["question"], "history": HISTORY}
        ).json()
        correct += is_correct(body["answer"], case)
        cost += body["cost_usd"]
        tokens += body["input_tokens"]
    return {"quality": correct / len(cases), "cost_usd": cost, "input_tokens": tokens}

def verdict(baseline: dict, levers: dict) -> bool:
    """La regla de la sesión: misma calidad o mejor, y menos costo."""
    return levers["quality"] >= baseline["quality"] and (
        levers["cost_usd"] < baseline["cost_usd"]
    )

def main() -> int:
    """Mide las dos configuraciones, imprime la tabla y decide."""
    cases = json.loads(EVAL_SET.read_text(encoding="utf-8"))
    with running_product(8767, **BASELINE) as client:
        baseline = measure(client, cases)
    with running_product(8768) as client:
        levers = measure(client, cases)
    for name, result in (("baseline", baseline), ("levers", levers)):
        print(
            f"{name:9} quality={result['quality']:.0%} "
            f"cost_usd={result['cost_usd']:.6f} input_tokens={result['input_tokens']}"
        )
    passed = verdict(baseline, levers)
    return 0 if passed else 1

if __name__ == "__main__":
    sys.exit(main())
```

**Escribe** `verification/e2e.py`

```python
"""Corre las pruebas de Playwright de ``product/e2e/`` contra el producto vivo."""

import subprocess
import sys

from verification.server import PRODUCT, running_product

PORT = 8769

def main() -> int:
    """Arranca el producto, corre las pruebas e2e y devuelve su código."""
    if not (PRODUCT / "e2e").is_dir():
        print("[FAIL] e2e: todavía no existe product/e2e/")
        return 1
    command = [sys.executable, "-m", "pytest", "e2e", "-q", "-p", "no:cacheprovider",
               "--base-url", f"http://127.0.0.1:{PORT}"]
    with running_product(PORT):
        code = subprocess.run(command, cwd=PRODUCT, check=False).returncode
    return code

if __name__ == "__main__":
    sys.exit(main())
```

Se agregan `e2e` y `evaluate`:

**Reemplaza (versión nueva completa)** `verification/__main__.py`

```python
"""Corre una verificación del producto y termina con su código de salida.

Uso: ``uv run python -m verification <paso>``, con uno de estos pasos:

- ``unit``: las pruebas que escribió qa-unit, con cobertura de 80 % o más.
- ``contract``: las pruebas de la fábrica contra el producto corriendo.
- ``qa``: la parte de QA.md que revisa un programa (``verification/qa.py``).
- ``e2e``: las pruebas de Playwright que escribió qa-e2e (``verification/e2e.py``).
- ``evaluate``: costo y calidad contra la línea base (``verification/evaluate.py``).

Código 0: pasa. Cualquier otro: falla, y la salida dice por qué.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PRODUCT = ROOT / "product"
PYTEST = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"]
STEPS = {
    "unit": (PYTEST + ["tests", "--cov=app", "--cov-fail-under=80"], PRODUCT),
    "contract": (PYTEST + ["verification/contract"], ROOT),
    "qa": ([sys.executable, "-m", "verification.qa"], ROOT),
    "e2e": ([sys.executable, "-m", "verification.e2e"], ROOT),
    "evaluate": ([sys.executable, "-m", "verification.evaluate"], ROOT),
}

def run(step: str) -> int:
    """Corre la verificación ``step`` e imprime ``[OK]`` o ``[FAIL]``."""
    if step not in STEPS:
        print(f"Uso: python -m verification {{{'|'.join(STEPS)}}}")
        return 2
    command, folder = STEPS[step]
    if not (PRODUCT / "app").is_dir():
        print(f"[FAIL] {step}: todavía no existe product/app/")
        return 1
    code = subprocess.run(command, cwd=folder, check=False).returncode
    print(f"[{'OK' if code == 0 else 'FAIL'}] {step}")
    return code

if __name__ == "__main__":
    sys.exit(run(sys.argv[1] if len(sys.argv) > 1 else ""))
```

### Paso 5 · El supervisor (15 min)

Los especialistas escriben en carpetas distintas: por eso pueden trabajar en paralelo:

**Reemplaza (versión nueva completa)** `hooks/permissions.py`

```python
"""Hook PreToolUse: cada agente escribe solo en sus carpetas (mínima agencia).

Claude Code llama a este script antes de cada herramienta y le pasa por stdin un
JSON con ``agent_type`` (el agente), ``tool_name`` y ``tool_input``. Si el script
termina con código 2, la herramienta se bloquea y el agente lee el motivo.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Dónde puede escribir cada agente. Quien escribe el código no escribe sus pruebas.
WRITABLE = {
    "architect": ["output/", "product/doc/"],
    "qa-unit": ["product/tests/"],
    "developer": ["product/app/", "product/data/", "product/requirements.txt"],
    "observability": ["product/app/", "product/requirements.txt", "product/README.md"],
    "qa-style": ["output/qa-review.md"],
    "costs": ["product/app/", "product/data/", "product/requirements.txt",
              "product/README.md", "product/.env.example"],
    "qa-e2e": ["product/e2e/"],
}
WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}

def check(event: dict) -> str | None:
    """Devuelve el motivo del bloqueo, o ``None`` si la herramienta puede correr."""
    agent = event.get("agent_type")
    if agent not in WRITABLE or event.get("tool_name") not in WRITE_TOOLS:
        return None
    target = (ROOT / event.get("tool_input", {}).get("file_path", "")).resolve()
    path = target.relative_to(ROOT).as_posix() if target.is_relative_to(ROOT) else ""
    if any(path == allowed or path.startswith(allowed) for allowed in WRITABLE[agent]):
        return None
    allowed = ", ".join(WRITABLE[agent])
    return f"{agent} no puede escribir {path or target}. Solo puede en: {allowed}"

if __name__ == "__main__":
    REASON = check(json.load(sys.stdin))
    if REASON:
        print(REASON, file=sys.stderr)
    sys.exit(2 if REASON else 0)
```

El orquestador ahora es un **supervisor**: lanza dos agentes en un solo mensaje y, cuando algo falla, decide quién lo corrige:

**Reemplaza (versión nueva completa)** `.claude/skills/factory/SKILL.md`

```markdown
---
description: >-
```

`La fábrica de la sesión 3 · architect → aprobación → qa-unit → [costs`∥

```text
  qa-e2e] (supervisor) → unit, contract, qa, e2e, evaluate → qa-style →
  pipeline y reporte. Ejemplo /factory
argument-hint: "[--aprobar]"
disable-model-invocation: true
allowed-tools: >-
  Agent, Read, Write, AskUserQuestion, Bash(uv run python -m verification *),
  Bash(uv run python scripts/pipeline.py)
---
Eres el SUPERVISOR de la fábrica. No escribes planes, pruebas ni código: repartes el trabajo entre especialistas
(herramienta Agent), los pones a trabajar en paralelo cuando no dependen entre sí, y decides qué sigue SOLO con
códigos de salida y con la primera línea de `output/qa-review.md`.

Entrada: $ARGUMENTS. Si trae `--aprobar`, la persona aprobó por adelantado: no preguntes en el paso 2.
Si no lo trae y no puedes preguntar (por ejemplo en `claude -p`), detente en el paso 2 y explica cómo seguir.

Si `product/app/` no existe, detente y di: «Copia primero el producto de la sesión 2 (ver README.md)».

Antes del paso 1, escribe `output/activity.jsonl` vacío: la bitácora del hook empieza con esta corrida.
Lleva una bitácora: una línea por paso con lo que pasó.

1. **Plan.** Lanza `architect` con: «Actualiza el plan para spec/03-costs.md».
2. **Aprobación humana.** Muestra `output/plan.md` y pregunta: «¿Apruebas el plan? Escribe si o tus comentarios».
   Con comentarios, relanza `architect` con ellos. Máximo 2 rechazos; al tercero → ESCALAR (paso 7).
3. **Pruebas primero.** Lanza `qa-unit` con: «Agrega las pruebas de spec/03-costs.md».
   Corre `uv run python -m verification unit`; debe FALLAR (rojo).
4. **Especialistas en paralelo.** En UN SOLO mensaje lanza los dos:
   - `costs` con «Implementa spec/03-costs.md hasta que pasen product/tests/».
   - `qa-e2e` con «Escribe las pruebas de punta a punta de spec/03-costs.md».
5. **Unión y compuertas (máximo 2 correcciones).** Cuando terminen los dos, corre en orden `unit`, `contract`,
   `qa`, `e2e` y `evaluate`, cada uno con `uv run python -m verification <nombre>`. Al primer fallo decide **quién**
   corrige con la salida:
   - Si falla `e2e` porque la prueba está mal escrita (selector o espera), relanza `qa-e2e` con el error.
   - Si falla `e2e` porque la página no hace lo que pide la especificación, relanza `developer` con
     «La página no cumple la especificación; corrige esto: <últimas 40 líneas>». La página es suya.
   - Cualquier otro fallo, relanza `costs` con «La verificación <nombre> falló; corrige esto: <últimas 40 líneas>».
   Vuelve a empezar este paso. Tras 2 correcciones sin pasar → ESCALAR.
6. **Evaluador-optimizador (máximo 2 vueltas).** Lanza `qa-style` con «Revisa el producto». Lee la primera línea de
   `output/qa-review.md`:
   - `APROBADO` → LISTA.
   - `CAMBIOS` → relanza `costs` con «Corrige los hallazgos de output/qa-review.md», repite el paso 5 y lanza `qa-style`
     con «Revisa el producto (segunda vuelta)».
   Tras 2 vueltas con CAMBIOS → ESCALAR.
7. **Pipeline y reporte.** Corre `uv run python scripts/pipeline.py`. Escribe `output/report.md` con:
   - El estado (LISTA, DETENIDA POR LA PERSONA o ESCALAR A UNA PERSONA).
   - Las correcciones y las vueltas de QA.
   - **La tabla de `evaluate`**: calidad y costo, línea base contra palancas.
   - La bitácora y un enlace a `output/pipeline.md`.
   Responde con el mismo resumen.

Reglas: corre cada verificación sola y tal cual está escrita, sin `;`, `&&` ni `|`: su código de salida es el veredicto, y con `| tail` se pierde. Nunca edites tú los archivos de
`product/`. Nunca te saltes un paso ni una verificación. No leas `.env`.
```

**Reemplaza (versión nueva completa)** `CLAUDE.md`

```markdown
# Fábrica del HR Assistant (Módulo 4, sesión 3)

Los agentes construyen el producto en `product/` a partir de la especificación de `spec/`. Las personas dirigen,
aprueban y comprueban: no programan.

- `/factory` corre la fábrica completa.
- `.claude/agents/`: architect, qa-unit, developer, observability, qa-style, costs, qa-e2e.
- `hooks/permissions.py`: cada agente escribe solo en sus carpetas.
- `hooks/activity_log.py`: bitácora de cada herramienta; `scripts/pipeline.py` dibuja el pipeline.
- `verification/`: el código decide si un paso terminó bien, no el agente.

## Reglas

- El orquestador delega: nunca escribe en `product/` (corrige al agente, no su resultado).
- Todo bucle tiene tope: 2 rechazos del plan, 2 correcciones y 2 vueltas de qa-style; después se escala a una persona.
- Una persona aprueba el plan antes de que se escriba código.
- Nunca leas `.env`.
- Código en inglés; comentarios, docstrings, documentos y mensajes a las personas en español. Sin emojis.
  Es una excepción acordada a QA.md, que pide todo en inglés: no la reportes como incumplimiento.
```

> **PATRÓN MULTIAGENTE: SUPERVISOR CON ESPECIALISTAS**
>
> El supervisor no escribe nada: reparte, pone en paralelo lo independiente y enruta cada falla a su dueño.

### Paso 6 · Las pruebas de la fábrica (10 min)

**Escribe** `tests/test_evaluate.py`

```python
"""Pruebas de la regla de costo y calidad, sin correr el producto."""

from verification import evaluate

class FakeClient:
    """Cliente que responde siempre lo mismo, para medir sin servidor."""

    def __init__(self, answer, cost):
        self.answer, self.cost = answer, cost

    def post(self, _path, json):
        assert json["history"]
        return self

    def json(self):
        return {"answer": self.answer, "cost_usd": self.cost, "input_tokens": 10}

def test_must_include_needs_every_text():
    case = {"must_include": ["Ana", "Jorge"]}
    assert evaluate.is_correct("Ana y Jorge", case)
    assert not evaluate.is_correct("Ana", case)

def test_any_of_needs_one_text_ignoring_case():
    assert evaluate.is_correct("Ya NO EXISTE", {"any_of": ["no existe"]})

def test_measure_adds_quality_cost_and_tokens():
    cases = [{"question": "q", "must_include": ["Ana"]}] * 2
    assert evaluate.measure(FakeClient("Ana", 0.5), cases) == {
        "quality": 1.0, "cost_usd": 1.0, "input_tokens": 20,
    }

def test_levers_must_be_cheaper_without_losing_quality():
    baseline = {"quality": 0.9, "cost_usd": 1.0}
    assert evaluate.verdict(baseline, {"quality": 0.9, "cost_usd": 0.4})
    assert not evaluate.verdict(baseline, {"quality": 0.8, "cost_usd": 0.1})
    assert not evaluate.verdict(baseline, {"quality": 1.0, "cost_usd": 1.0})
```

Lo que solo corre con el producto vivo se prueba corriendo la fábrica:

**Escribe** `scripts/coverage.ini`

```
# Lo que solo corre con el producto vivo se prueba corriéndolo (/factory), no aquí.
[run]
omit =
    verification/server.py
    verification/e2e.py
    verification/contract/*
```

**Reemplaza (versión nueva completa)** `scripts/verify.py`

```python
"""Lista de QA.md de la fábrica (no del producto), para Windows, Linux y macOS.

Corre las pruebas de los hooks y de la verificación con cobertura, pylint y busca
emojis. Termina con código 0 solo si todo pasa.

Uso: ``uv run python scripts/verify.py``
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CODE = ("hooks", "verification", "scripts", "tests")
CHECKS = {
    "Tests and coverage >= 80%": [
        "-m", "pytest", "tests", "-q", "-p", "no:cacheprovider",
        "--cov=hooks", "--cov=verification", "--cov-fail-under=80",
        "--cov-config=scripts/coverage.ini",
    ],
    "Pylint": [
        "-m", "pylint", *CODE, "--max-line-length=88", "--fail-under=9.5",
        "--disable=missing-function-docstring,missing-module-docstring",
    ],
}
TEXT = ("*.py", "*.md", "*.json")

def has_emoji(text: str) -> bool:
    """Indica si el texto tiene emojis o símbolos gráficos.

    :param text: Texto a revisar
    :type text: str
    :return: ``True`` si hay al menos uno
    :rtype: bool
    """
    return any(ord(c) > 0xFFFF or 0x2600 <= ord(c) <= 0x27BF for c in text)

def files_with_emojis() -> list[str]:
    """Lista los archivos de la fábrica que tienen emojis.

    :return: Rutas relativas
    :rtype: list[str]
    """
    paths = [p for pattern in TEXT for p in ROOT.rglob(pattern)]
    skip = (".venv", "product", "output")
    return sorted(
        str(p.relative_to(ROOT))
        for p in paths
        if not any(part in skip for part in p.relative_to(ROOT).parts)
        and has_emoji(p.read_text(encoding="utf-8"))
    )

def main() -> int:
    """Corre cada verificación e imprime el resumen.

    :return: 0 si todo pasa, 1 si algo falla
    :rtype: int
    """
    results = {}
    for name, args in CHECKS.items():
        run = subprocess.run([sys.executable, *args], cwd=ROOT, check=False)
        results[name] = run.returncode == 0
    emojis = files_with_emojis()
    results["No emojis"] = not emojis
    print("\nQA checklist")
    for name, passed in results.items():
        print(f"  [{'OK' if passed else 'FAIL'}] {name}")
    for path in emojis:
        print(f"         emoji in {path}")
    return 0 if all(results.values()) else 1

if __name__ == "__main__":
    sys.exit(main())
```

**Ejecuta**

**Todos los sistemas**

```bash
uv run python scripts/verify.py
```

### Paso 7 · Corre la fábrica (25 min)

**Ejecuta** (en la carpeta de la sesión)

**Todos los sistemas**

```bash
claude
```

**Dentro de Claude Code**

```text
/factory
```

**Observa:** en `output/activity.jsonl`, `costs` y `qa-e2e` escriben al mismo tiempo.

### Paso 8 · Costo, calidad, e2e y el paralelo (25 min)

**Ejecuta**

**Todos los sistemas**

```bash
uv run python -m verification evaluate
```

**Observa**

```text
baseline  quality=100% cost_usd=0.000913 input_tokens=1679
levers    quality=100% cost_usd=0.000122 input_tokens=1109
[OK] evaluate
```

**Observa:** misma calidad y 87 % menos costo, con el modelo simulado y los precios reales.

**Ejecuta**

**Todos los sistemas**

```bash
uv run python -m verification e2e
```

**Observa**

```text
4 passed, 1 warning in 0.81s
[OK] e2e
```

![La página como la ve Playwright](M4_sesion03_img/fig01.png)

*La página como la ve Playwright*

**Ejecuta**

**Todos los sistemas**

```bash
uv run python scripts/pipeline.py
```

**Las primeras filas de output/pipeline.md**

```text
| # | Paso | Resultado | Segundos |
| --- | --- | --- | --- |
| 1 | architect | pasó | 146 |
| 2 | qa-unit | pasó | 217 |
| 3 | verify unit | pasó | 3 |
| 4 | costs | pasó | 493 |
| 5 | qa-e2e | pasó | 53 |
| 6 | verify unit | pasó | 21 |
```

**Observa:** `costs` y `qa-e2e` empiezan juntos y comparten columna en el diagrama.

Opcional, con tu cuenta de Cloudflare: copia `product/.env.example` a `product/.env`, escribe tu Account ID y tu token **en tu editor** (nunca en el chat), pon `MODEL_PROVIDER=gateway` y corre `uv run --env-file .env uvicorn app.main:app` dentro de `product/`.

### Paso 9 · README y commit (10 min)

**Reemplaza (versión nueva completa)** `README.md`

````markdown
# Sesión 3 · Costos (especialistas en paralelo con un supervisor)

La fábrica agrega al producto el modelo real (Cloudflare Workers AI a través de AI Gateway) y cuatro palancas de
costo: enrutamiento, ventana de historial, tope de salida y caché. Ninguna palanca se queda si empeora la calidad:
lo decide `verification evaluate`, un programa, no un agente.

| Paso | Quién | Patrón |
| --- | --- | --- |
| Plan | `architect` y tú lo apruebas | Humano en el lazo |
| Pruebas primero | `qa-unit` | |
| Costos y pruebas e2e **al mismo tiempo** | `costs` y `qa-e2e` | **Multiagente**: supervisor con especialistas en paralelo |
| unit → contract → qa → e2e → evaluate | El supervisor decide quién corrige cada fallo (máximo 2) | Flujo con compuertas |
| Revisión contra QA.md | `qa-style` (máximo 2 vueltas) | Evaluador-optimizador |

## Preparar

Copia el producto de la sesión 2 e instala el navegador de Playwright (una vez).

macOS / Linux:

```bash
cd NextGenCode-M4-Agentes/sesion03
cp -R ../sesion02/product product
uv venv --python 3.12
uv pip install -r requirements.txt
uv run playwright install chromium
uv run python scripts/verify.py
```

Windows (PowerShell):

```powershell
cd NextGenCode-M4-Agentes\sesion03
Copy-Item -Recurse ..\sesion02\product product
uv venv --python 3.12
uv pip install -r requirements.txt
uv run playwright install chromium
uv run python scripts/verify.py
```

## Correr la fábrica
La primera vez que abres `claude` en esta carpeta te pregunta **«Do you trust the files in this folder?»**:
responde que sí. Sin esa confianza, Claude Code ignora los permisos de `.claude/settings.json` y los agentes no pueden
correr las verificaciones.

Ejecuta `claude` y, dentro, escribe `/factory`. En `output/pipeline.md` vas a ver que `costs` y `qa-e2e`
trabajaron al mismo tiempo.

## Comprobar

```bash
uv run python -m verification evaluate
uv run python -m verification e2e
```

`evaluate` imprime la calidad y el costo de la línea base y de la configuración con palancas.

Para probar con el modelo real, copia `product/.env.example` a `product/.env` y escribe tu Account ID y tu token de
Cloudflare. Nunca los pegues en el chat ni en el código. Después:

```bash
cd product
uv run --env-file .env uvicorn app.main:app
```
````

**Ejecuta**

**Todos los sistemas**

```bash
git add -A
git commit -m "Sesion 3: supervisor con costs y qa-e2e en paralelo, evaluate y e2e"
```

**Observa:** `product/` y `output/` no entran al commit: están en `.gitignore`. Versionas la fábrica; el producto se reconstruye corriéndola.

## Estructura final de la carpeta

```text
sesion03/
  .claude/agents/architect.md
  .claude/agents/costs.md
  .claude/agents/developer.md
  .claude/agents/observability.md
  .claude/agents/qa-e2e.md
  .claude/agents/qa-style.md
  .claude/agents/qa-unit.md
  .claude/settings.json
  .claude/skills/factory/SKILL.md
  .gitignore
  CLAUDE.md
  QA.md
  README.md
  hooks/__init__.py
  hooks/activity_log.py
  hooks/permissions.py
  requirements.txt
  scripts/__init__.py
  scripts/coverage.ini
  scripts/pipeline.py
  scripts/verify.py
  spec/01-architecture.md
  spec/02-observability.md
  spec/03-costs.md
  spec/employees.json
  spec/model_prices.json
  tests/__init__.py
  tests/test_activity_log.py
  tests/test_evaluate.py
  tests/test_permissions.py
  tests/test_qa.py
  tests/test_verification.py
  verification/__init__.py
  verification/__main__.py
  verification/contract/conftest.py
  verification/contract/test_contract.py
  verification/contract/test_contract_02.py
  verification/contract/test_contract_03.py
  verification/e2e.py
  verification/eval_set.json
  verification/evaluate.py
  verification/qa.py
  verification/server.py
  product/   (lo genera la fábrica)
  output/    (plan, reporte, bitácora)
```

## Resumen de los pasos

| Paso | Qué se construye | Llama al modelo | Tiempo |
|---|---|---|---|
| 0 | Copia la sesión 2 | No | 10 min |
| 1 | La especificación de costos y sus datos | No | 10 min |
| 2 | Dos especialistas | No | 15 min |
| 3 | El producto vivo, para cualquier verificación | No | 15 min |
| 4 | Costo contra calidad, y pruebas de punta a punta | No | 15 min |
| 5 | El supervisor | No | 15 min |
| 6 | Las pruebas de la fábrica | No | 10 min |
| 7 | Corre la fábrica | Sí | 25 min |
| 8 | Costo, calidad, e2e y el paralelo | No | 25 min |
| 9 | README y commit | No | 10 min |

## Si algo falla

| Síntoma | Causa probable | Qué hacer |
|---|---|---|
| Una verificación pide aprobación y los agentes se detienen | La carpeta no es de confianza | Abre `claude` en una terminal normal y acepta «trust» |
| `uv run` usa otro Python | Hay otro entorno virtual activo | Cierra la terminal o `deactivate` |
| El hook no bloquea nada | `settings.json` mal escrito o carpeta sin confianza | Valida el JSON y la confianza |
| `verification` dice que no existe `product/app/` | No corriste la fábrica o no copiaste la sesión anterior | Corre `/factory` o copia `product/` |
| La fábrica termina en ESCALAR | Se llegó a un tope | Lee `output/report.md`: dice qué falló y qué decidir |
| Una verificación «pasa» y no debería | Se corrió con `\| tail` | Córrela sola: el código de salida es el veredicto |
| Un archivo pegado da error de sangría | El PDF partió o juntó líneas | Compara con el manual línea por línea; Python es sensible a la sangría |

## Lista de comprobación

- [ ] `uv run python scripts/verify.py` dice `[OK]` en todo
- [ ] `/factory` terminó en LISTA (o entiendo por qué escaló)
- [ ] Las verificaciones de la sesión pasan contra mi producto
- [ ] Hice commit de la fábrica (sin `product/` ni `output/`)
