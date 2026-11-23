Certificado · Next-Gen Coding: Desarrollo de Software con IA Generativa (Virtual)

**Módulo 4 · Agentes en producción · Manual de práctica**

# Agentes en producción · Sesión 4 · Producción

La fábrica lo publica con tu aprobación

Una fábrica de agentes de Claude Code construye el HR Assistant, lo prueba, lo revisa y lo publica. Tú diriges, apruebas y compruebas.

**CONTENIDO**

1. Cómo usar esta guía

2. Requisitos para todo el módulo

3. Sesión 4 · Producción: la fábrica publica, con tu aprobación

4. Estructura final de la carpeta

5. Resumen de los pasos

6. Si algo falla

7. Lista de comprobación

## Cómo usar esta guía

En este módulo construyes, con tus manos, una **fábrica de agentes** de Claude Code. Después la fábrica construye sola el producto (el HR Assistant), lo prueba, lo revisa contra `QA.md` y, en la sesión 4, lo publica cuando tú lo apruebas. Tú no escribes el producto: escribes los agentes, el orquestador, los hooks y las verificaciones que lo construyen.

Es **incremental**: la sesión 1 parte de una carpeta vacía; cada sesión copia la carpeta anterior y le agrega piezas. Lo que construyas hoy es el punto de partida de la siguiente sesión.

| Concepto | Detalle |
|---|---|
| Sesión | 4 de 4 · Producción |
| Hoy | La fábrica publica el producto, con tu aprobación |
| Patrón de la fábrica | Humano en el lazo y triage de fallas |
| Duración | 2 h 30 min, con tiempos pesimistas |
| Carpeta | `NextGenCode-M4-Agentes/sesion04` |

Cada paso tiene tres partes:

- **Escribe:** el archivo completo, con su ruta; tu editor crea las carpetas al guardar. **Reemplaza** quiere decir que el archivo ya existe y cambia: pega la versión nueva completa encima de la anterior.

- **Ejecuta:** el comando para probar ese paso, para macOS / Linux y para Windows.

- **Observa:** lo que debe salir y la idea que deja.

> **CUIDADO**
>
> **Copia el código del archivo Markdown, no del PDF.** Junto con este PDF recibes `M4_sesion04.md`, con el mismo contenido. Al copiar de un PDF, los visores pierden la sangría, y en Python la sangría es parte del código. Lee en el PDF y copia del `.md` (ábrelo en tu editor).

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

## Sesión 4 · Producción: la fábrica publica, con tu aprobación

Hoy la fábrica cierra el producto (claves, límite de peticiones, compliance), lo empaqueta, escribe el pipeline de CI y lo publica en Render **solo si tú lo apruebas**. Si la prueba de humo falla, un agente de triage decide quién lo corrige.

```mermaid
flowchart TD
  qaunit["qa-unit"] --> sec["security"]
  qaunit --> dep["deploy"]
  qaunit --> e2e["qa-e2e"]
  sec --> gates{"5 compuertas"}
  dep --> gates
  e2e --> gates
  gates --> style{"qa-style"}
  style --> ok{{"¿Publico? Tú decides"}}
  ok -- si --> pub(["publish.py · GitHub"])
  pub --> act["Actions"]
  act --> render(["Render"])
  render --> smoke{"Prueba de humo"}
  smoke -- falla --> triage["triage"]
```

### Paso 0 · Copia la sesión 3 (10 min)

**Ejecuta**

**macOS / Linux**

```bash
cd ..
rsync -a --exclude .venv --exclude output --exclude '__pycache__' sesion03/ sesion04/
cd sesion04
uv venv --python 3.12
```

**Windows (PowerShell)**

```powershell
cd ..
robocopy sesion03 sesion04 /E /XD .venv output __pycache__
cd sesion04
uv venv --python 3.12
```

**Observa:** `sesion04` tiene la fábrica **y el producto** de la sesión 3 (`product/`): es el punto de partida. El entorno virtual se crea de nuevo porque guarda rutas absolutas. Abre `claude` una vez y acepta la confianza de la carpeta.

**Ejecuta**

**Todos los sistemas**

```bash
uv pip install -r requirements.txt
```

### Paso 1 · La especificación de producción (10 min)

**Escribe** `spec/04-production.md`

```markdown
# Sesión 4 · Producción: publicarlo de forma segura

Parte del producto de las sesiones 1 a 3. Lo cierra con acceso por clave, límite de peticiones y reglas de compliance
que se revisan solas. Lo empaqueta en un contenedor, con un pipeline de CI que los ingenieros pueden ver, y lo
publica en Render solo si el pipeline pasa.

## Lo que debe hacer

1. **Una clave por cliente.**
   - `API_KEYS` tiene la forma `cliente:clave,cliente2:clave2`.
   - `POST /ask` y `GET /metrics` exigen el encabezado `X-API-Key`. Sin clave o con una inválida, responden
     `401 {"detail": "invalid or missing API key"}`.
   - `GET /`, `GET /health` y `/docs` no piden clave.
   - El nombre del cliente va en el log (`client`), en la auditoría y en los metadatos de la traza.
   - **La clave nunca se escribe** en el log, en la traza ni en un mensaje de error.
   - Si `API_KEYS` está mal formada, el producto no arranca. El error dice qué entrada falla y su largo, nunca su valor.
2. **Límite de peticiones por cliente.** Más de `RATE_LIMIT_PER_MINUTE` peticiones en un minuto →
   `429 {"detail": "rate limit exceeded"}` con el encabezado `Retry-After` (segundos que faltan). El reloj se inyecta.
3. **Compliance como código.** Con `ENVIRONMENT=production`, el producto **se niega a arrancar** si:
   - `MODEL_PROVIDER` es `fake`.
   - `API_KEYS` está vacía o alguna clave tiene menos de 16 caracteres.
   - Las trazas están encendidas y `HIDE_INPUTS` o `HIDE_OUTPUTS` no valen `true`.

   `doc/compliance-checklist.md` tiene una tabla con tres columnas: la regla, dónde está en el código y cómo se
   comprueba.
4. **La página web** tiene un campo de clave (`data-testid="api-key"`, tipo contraseña).
   - La clave se guarda en `sessionStorage`, nunca en `localStorage` ni en el código de la página, y se manda en `X-API-Key`.
   - Con `401` muestra «Clave inválida». Con `429`, «Demasiadas preguntas; espera N segundos».
5. **Contenedor.**
   - `Dockerfile` con `python:3.12-slim`, un usuario que no es root y
     `uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}`.
   - `.dockerignore` que deja fuera `.env`, `tests/`, `e2e/` y los cachés.
6. **Pipeline de CI** en `.github/workflows/ci.yml`. Corre en cada push y en cada pull request, con cuatro trabajos
   encadenados (`needs`), para que los ingenieros vean cada etapa en la pestaña Actions:
   1. `style`: pylint con 88 columnas.
   2. `unit`: pruebas y BDD con cobertura de 80 % o más.
   3. `e2e`: Playwright con el modelo simulado.
   4. `docker`: `docker build` de la imagen.
7. **Render.** `render.yaml` es un Blueprint con un servicio web:
   - El servicio se llama **igual que el repositorio** que da la persona. Así no choca con un servicio que ya exista
     en su cuenta de Render, porque Render actualizaría ese en lugar de crear uno nuevo.
   - `runtime: docker`, `plan: free`, `healthCheckPath: /health`.
   - `autoDeployTrigger: checksPass`: Render publica solo si el pipeline pasa.
   - `ENVIRONMENT=production`, `MODEL_PROVIDER=gateway`, `HIDE_INPUTS=true` y `HIDE_OUTPUTS=true`.
   - Los secretos (`API_KEYS`, `CF_ACCOUNT_ID`, `CF_API_TOKEN`) con `sync: false`: se escriben en Render y nunca en
     el repositorio. Render exige un valor para cada uno al crear el Blueprint, por eso `LANGSMITH_API_KEY`, que es
     opcional, no va ahí: se agrega en Render > Environment si se encienden las trazas.
8. **Prueba de humo** en `scripts/smoke.py <url>`. Lee la clave de la variable `SMOKE_API_KEY`, nunca de un argumento,
   y comprueba tres cosas, imprimiendo `[OK]` o `[FAIL]` en cada una:
   - `/health` responde `200`.
   - `/ask` sin clave responde `401`.
   - `/ask` con clave responde `200`.

## Pruebas de punta a punta (las actualiza `qa-e2e`)

- Las pruebas de la sesión 3 ahora escriben primero la clave en `data-testid="api-key"`. La clave se lee de la
  variable `E2E_API_KEY`, que pone la verificación; nunca va escrita en la prueba.
- Una clave equivocada muestra «Clave inválida».

## Configuración nueva

| Variable | Por omisión | Para qué |
| --- | --- | --- |
| `ENVIRONMENT` | `development` | Con `production` se aplican las reglas de compliance |
| `API_KEYS` | vacía | Clientes y claves (secreto) |
| `RATE_LIMIT_PER_MINUTE` | `30` | Peticiones por cliente por minuto |

## Cómo se comprueba

- `verification unit`, `contract`, `qa`, `e2e` y `evaluate`, como en la sesión 3, ahora con clave.
- Una persona aprueba la publicación. Después, `scripts/publish.py` crea el repositorio en GitHub y hace el push.
- `uv run python -m verification production <url>`: la prueba de humo contra Render.
```

### Paso 2 · Tres agentes nuevos y uno que cambia (15 min)

**Escribe** `.claude/agents/security.md`

```markdown
---
name: security
description: >-
  Agrega la seguridad del producto (claves por cliente, límite de peticiones,
  compliance como código y el campo de clave en la página) según
  spec/04-production.md. No escribe pruebas. Corre en paralelo con deploy y
  qa-e2e.
tools: Read, Glob, Grep, Write, Edit, Bash
---
Eres el ingeniero de seguridad del HR Assistant.

1. Lee `spec/` (sobre todo `04-production.md`), `output/plan.md`, el código de `product/app/`, las pruebas de
   `product/tests/` y `QA.md`.
2. Implementa los puntos 1 a 4 de la especificación **sin romper** lo de las sesiones anteriores:
   - Claves por cliente.
   - Límite de peticiones con el reloj inyectado.
   - Compliance con `ENVIRONMENT=production`.
   - El campo de clave en la página, en `sessionStorage`.

   Escribe `product/doc/compliance-checklist.md` y actualiza `product/README.md` y `product/.env.example`.
3. Corre `uv run python -m verification unit` y `uv run python -m verification qa` hasta que pasen.
4. Si te pasan un error de la verificación o hallazgos de `qa-style`, corrígelos todos y di cómo.

Reglas:
- Código en inglés; comentarios y docstrings en español (estilo Sphinx).
- Líneas de máximo 88 caracteres. Sin emojis.
- **Una clave nunca se escribe** en el log, en la traza, en un error ni en el código.
- Compara claves con `hmac.compare_digest`.
- No cambies las pruebas.
- Solo puedes escribir en `product/app/`, `product/requirements.txt`, `product/README.md`,
  `product/.env.example` y `product/doc/compliance-checklist.md`.

Termina con la lista de archivos que cambiaste y el resultado de las pruebas.

En Bash solo puedes correr `uv run python -m verification <paso>`; para leer usa Read, Glob y Grep (nunca
`cat`, `grep` ni `cd` en Bash).
```

Prepara todo para publicar, pero no publica:

**Escribe** `.claude/agents/deploy.md`

```markdown
---
name: deploy
description: >-
  Prepara la publicación según spec/04-production.md (Dockerfile,
  .dockerignore, .gitignore, render.yaml, pipeline de CI en
  .github/workflows/ci.yml y scripts/smoke.py). No toca el código de la
  aplicación. Corre en paralelo con security y qa-e2e.
tools: Read, Glob, Grep, Write, Edit
---
Eres el ingeniero de despliegue del HR Assistant. Preparas todo para publicar, pero no publicas: eso pasa
solo cuando una persona lo aprueba.

1. Lee `spec/` (sobre todo `04-production.md`), `product/README.md`, `product/requirements.txt` y la estructura de
   `product/`.
2. Escribe, según los puntos 5 a 8 de la especificación:
   - `product/Dockerfile` y `product/.dockerignore`.
   - `product/.gitignore`: `.env`, `.venv/`, cachés y `.coverage`.
   - `product/render.yaml`.
   - `product/.github/workflows/ci.yml`, con los trabajos `style`, `unit`, `e2e` y `docker` encadenados con `needs`.
     Usa `actions/checkout@v5` y `actions/setup-python@v6` con Python 3.12. Instala con
     `pip install -r requirements.txt`. Para e2e, corre `python -m playwright install --with-deps chromium`,
     arranca el producto con `MODEL_PROVIDER=fake` y una clave de prueba, y pasa esa misma clave en `E2E_API_KEY`.
   - `product/scripts/smoke.py`.
3. Revisa que `product/requirements.txt` tenga lo que el contenedor y el CI necesitan. Si falta algo, dilo en tu
   resumen: ese archivo no es tuyo.

Reglas:
- Comentarios en español y sin emojis.
- **Ningún secreto en ningún archivo.** En `render.yaml` los secretos llevan `sync: false`. En el CI, la clave de
  prueba es un texto de ejemplo, no una clave real.
- Solo puedes escribir en `product/Dockerfile`, `product/.dockerignore`, `product/.gitignore`,
  `product/render.yaml`, `product/.github/` y `product/scripts/`.

Termina con la lista de archivos y un resumen de las etapas del pipeline.
```

No corrige nada: decide a quién le toca. Puede responder `persona`:

**Escribe** `.claude/agents/triage.md`

```markdown
---
name: triage
description: >-
  Cuando falla la prueba de humo en producción, lee el error y decide quién lo
  corrige (security, deploy o una persona). No corrige nada. Escribe
  output/triage.md.
tools: Read, Glob, Grep, Write
---
Eres el responsable de triage. Recibes la salida de la prueba de humo que falló contra Render y decides quién
lo corrige. No corriges nada.

1. Lee la salida que te pasan, `spec/04-production.md`, `product/render.yaml`, `product/Dockerfile` y el código de
   `product/app/` que haga falta.
2. Escribe `output/triage.md`:
   - Primera línea, sola: `security`, `deploy` o `persona`.
   - Después, en pocas líneas: qué falló, la causa más probable y qué tiene que hacer el responsable.
3. Elige `persona` cuando la causa es algo que ningún agente puede ni debe tocar. Por ejemplo, un secreto que falta
   o está mal en **Render > Environment**, el Blueprint sin conectar o el servicio dormido. Di exactamente qué revisar.

Escribe en español y sin emojis. **Nunca pidas ni repitas una clave.** Solo puedes escribir `output/triage.md`.
```

Ahora la página pide clave: las pruebas la leen de una variable:

**Reemplaza (versión nueva completa)** `.claude/agents/qa-e2e.md`

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
   - Si la página pide clave, escríbela con `os.environ["E2E_API_KEY"]`; nunca escribas una clave en la prueba.
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

### Paso 3 · El hook, versión final (10 min)

Dos reglas para todos, también para el orquestador: nadie lee `.env` y nadie publica sin `output/approved.txt`. El arquitecto ya no puede escribir en todo `output/`:

**Reemplaza (versión nueva completa)** `hooks/permissions.py`

```python
"""Hook PreToolUse: cada agente escribe solo en sus carpetas (mínima agencia).

Claude Code llama a este script antes de cada herramienta y le pasa por stdin un
JSON con ``agent_type`` (el agente), ``tool_name`` y ``tool_input``. Si el script
termina con código 2, la herramienta se bloquea y el agente lee el motivo.

Sesión 4: dos reglas para todos, también para el orquestador. Nadie lee ``.env``,
y nadie publica sin ``output/approved.txt``, que solo existe si una persona aprobó.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Dónde puede escribir cada agente. Quien escribe el código no escribe sus pruebas.
WRITABLE = {
    "architect": ["output/plan.md", "product/doc/"],
    "qa-unit": ["product/tests/"],
    "qa-e2e": ["product/e2e/"],
    "qa-style": ["output/qa-review.md"],
    "developer": ["product/app/", "product/data/", "product/requirements.txt"],
    "observability": ["product/app/", "product/requirements.txt", "product/README.md"],
    "costs": ["product/app/", "product/data/", "product/requirements.txt",
              "product/README.md", "product/.env.example"],
    "security": ["product/app/", "product/requirements.txt", "product/README.md",
                 "product/.env.example", "product/doc/compliance-checklist.md"],
    "deploy": ["product/Dockerfile", "product/.dockerignore", "product/render.yaml",
               "product/.github/", "product/scripts/", "product/.gitignore"],
    "triage": ["output/triage.md"],
}
WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}
SECRETS = re.compile(r"\.env(?![\w.])")  # .env sí; .env.example no
PUBLISH = re.compile(r"publish\.py|git push|gh repo create")

def check(event: dict) -> str | None:
    """Devuelve el motivo del bloqueo, o ``None`` si la herramienta puede correr."""
    agent, tool = event.get("agent_type"), event.get("tool_name")
    tool_input = event.get("tool_input", {})
    if tool not in WRITE_TOOLS and SECRETS.search(json.dumps(tool_input)):
        return "Nadie lee .env: ahí van los secretos."
    publishes = tool == "Bash" and PUBLISH.search(tool_input.get("command", ""))
    if publishes and not (ROOT / "output" / "approved.txt").exists():
        return "Publicar requiere que una persona lo apruebe (output/approved.txt)."
    if agent not in WRITABLE or tool not in WRITE_TOOLS:
        return None
    target = (ROOT / tool_input.get("file_path", "")).resolve()
    path = target.relative_to(ROOT).as_posix() if target.is_relative_to(ROOT) else ""
    if any(path == ok or path.startswith(ok) for ok in WRITABLE[agent]):
        return None
    allowed = ", ".join(WRITABLE[agent])
    return f"{agent} no puede escribir {path or target}. Solo puede en: {allowed}"

if __name__ == "__main__":
    REASON = check(json.load(sys.stdin))
    if REASON:
        print(REASON, file=sys.stderr)
    sys.exit(2 if REASON else 0)
```

El hook ahora vigila también las lecturas y la terminal:

**Reemplaza (versión nueva completa)** `.claude/settings.json`

```json
{
  "permissions": {
    "deny": [
      "Read(./.env)",
      "Read(./**/.env)",
      "WebFetch",
      "WebSearch"
    ],
    "allow": [
      "Bash(uv run python -m verification *)",
      "Bash(uv run python scripts/pipeline.py)",
      "Bash(uv run python scripts/publish.py *)"
    ]
  },
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit|MultiEdit|NotebookEdit|Read|Grep|Bash",
        "hooks": [
          {
            "type": "command",
            "command": "uv run python \"$CLAUDE_PROJECT_DIR/hooks/permissions.py\""
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "uv run python \"$CLAUDE_PROJECT_DIR/hooks/activity_log.py\""
          }
        ]
      }
    ],
    "PostToolUseFailure": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "uv run python \"$CLAUDE_PROJECT_DIR/hooks/activity_log.py\""
          }
        ]
      }
    ]
  }
}
```

**Ejecuta**

**macOS / Linux**

```bash
echo '{"agent_type": "developer", "tool_name": "Edit", "tool_input": {"file_path": "product/tests/test_main.py"}}' | uv run python hooks/permissions.py
echo "código: $?"
```

**Windows (PowerShell)**

```powershell
'{"agent_type": "developer", "tool_name": "Edit", "tool_input": {"file_path": "product/tests/test_main.py"}}' | uv run python hooks/permissions.py
"código: $LASTEXITCODE"
```

**Observa:** igual que antes; y si alguien pide leer `.env` o publicar sin aprobación, también se bloquea.

**Si alguien intenta leer .env**

```text
código de salida 2
Nadie lee .env: ahí van los secretos.
```

**Si alguien intenta publicar sin aprobación**

```text
código de salida 2
Publicar requiere que una persona lo apruebe (output/approved.txt).
```

### Paso 4 · Verificaciones con clave y la prueba de humo (15 min)

El producto de prueba arranca con una clave de la fábrica (no es un secreto):

**Reemplaza (versión nueva completa)** `verification/server.py`

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
# Clave de prueba de la fábrica: no es un secreto, solo existe en estas corridas
FACTORY_KEY = "factory-key-0123456789"
DEFAULTS = {
    "MODEL_PROVIDER": "fake",
    "API_KEYS": f"factory:{FACTORY_KEY}",
    "RATE_LIMIT_PER_MINUTE": "1000",
}

@contextmanager
def running_product(port: int, **env: str):
    """Corre ``uvicorn app.main:app`` en ``port`` mientras dure el bloque.

    El cliente que entrega ya manda la clave de la fábrica en ``X-API-Key``.
    """
    settings = {**os.environ, **DEFAULTS, **env}
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
        yield httpx.Client(
            base_url=url, timeout=10, headers={"X-API-Key": FACTORY_KEY}
        )
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

@pytest.fixture(scope="session")
def api_limited():
    """El producto con un límite de dos peticiones por minuto."""
    with running_product(8770, RATE_LIMIT_PER_MINUTE="2") as client:
        yield client
```

**Escribe** `verification/contract/test_contract_04.py`

```python
"""Contrato de la sesión 4: solo entra quien tiene clave, y nadie abusa."""

import os
import subprocess
import sys

import httpx

from verification.server import PRODUCT

QUESTION = {"question": "¿Quién es EMP-0004?"}

def test_asking_without_a_key_returns_401(api):
    response = httpx.post(f"{api.base_url}/ask", json=QUESTION)
    assert response.status_code == 401

def test_asking_with_a_wrong_key_returns_401(api):
    response = api.post("/ask", json=QUESTION, headers={"X-API-Key": "wrong"})
    assert response.status_code == 401

def test_health_and_page_need_no_key(api):
    assert httpx.get(f"{api.base_url}/health").status_code == 200
    assert 'data-testid="api-key"' in httpx.get(f"{api.base_url}/").text

def test_too_many_requests_returns_429_with_retry_after(api_limited):
    codes = [api_limited.post("/ask", json=QUESTION) for _ in range(3)]
    assert [c.status_code for c in codes] == [200, 200, 429]
    assert int(codes[-1].headers["Retry-After"]) > 0

def start(**env):
    settings = {**os.environ, "ENVIRONMENT": "development", **env}
    command = [sys.executable, "-c", "import app.main"]
    return subprocess.run(command, cwd=PRODUCT, env=settings, capture_output=True,
                          text=True, timeout=30, check=False)

def test_production_refuses_the_fake_model():
    started = start(
        ENVIRONMENT="production", MODEL_PROVIDER="fake", API_KEYS="a:" + "k" * 20
    )
    assert started.returncode != 0

def test_a_broken_api_keys_never_leaks_the_key():
    started = start(API_KEYS="secret-value-without-client")
    assert started.returncode != 0
    assert "secret-value-without-client" not in started.stderr
```

**Reemplaza (versión nueva completa)** `verification/e2e.py`

```python
"""Corre las pruebas de Playwright de ``product/e2e/`` contra el producto vivo.

Las pruebas leen la clave de la variable ``E2E_API_KEY`` para escribirla en la página.
"""

import os
import subprocess
import sys

from verification.server import FACTORY_KEY, PRODUCT, running_product

PORT = 8769

def main() -> int:
    """Arranca el producto, corre las pruebas e2e y devuelve su código."""
    if not (PRODUCT / "e2e").is_dir():
        print("[FAIL] e2e: todavía no existe product/e2e/")
        return 1
    command = [sys.executable, "-m", "pytest", "e2e", "-q", "-p", "no:cacheprovider",
               "--base-url", f"http://127.0.0.1:{PORT}"]
    env = {**os.environ, "E2E_API_KEY": FACTORY_KEY}
    with running_product(PORT):
        code = subprocess.run(command, cwd=PRODUCT, env=env, check=False).returncode
    return code

if __name__ == "__main__":
    sys.exit(main())
```

La prueba de humo contra la URL pública. La clave sale de una variable de entorno, nunca del comando ni del chat:

**Escribe** `verification/production.py`

```python
"""Prueba de humo contra el producto publicado.

Uso: ``uv run python -m verification production https://<servicio>.onrender.com``

La clave se lee de la variable ``SMOKE_API_KEY``: nunca va en el comando ni en
el chat, porque quedaría en el historial.
"""

import os
import sys

import httpx

def smoke(url: str, key: str, client: httpx.Client) -> bool:
    """Comprueba ``/health``, ``/ask`` sin clave y ``/ask`` con clave.

    Imprime el código recibido en cada una: con él se ve la causa de una falla
    (401: la clave no coincide; 502: el modelo no responde).
    """
    question = {"question": "¿Quién es EMP-0004?"}
    checks = [
        ("GET /health", 200, client.get(f"{url}/health")),
        ("POST /ask sin clave", 401, client.post(f"{url}/ask", json=question)),
        ("POST /ask con clave", 200, client.post(
            f"{url}/ask", json=question, headers={"X-API-Key": key}
        )),
    ]
    for name, expected, response in checks:
        status = "OK" if response.status_code == expected else "FAIL"
        print(f"  [{status}] {name} -> {response.status_code} (esperado {expected})")
    return all(response.status_code == expected for _, expected, response in checks)

def main(args: list[str]) -> int:
    """Corre la prueba de humo; 0 si todo pasa."""
    key = os.environ.get("SMOKE_API_KEY", "")
    if len(args) != 1 or not key:
        print("Uso: SMOKE_API_KEY=<clave> python -m verification production <url>")
        return 2
    # Render despierta el servicio dormido en hasta un minuto
    with httpx.Client(timeout=90) as client:
        passed = smoke(args[0].rstrip("/"), key, client)
    return 0 if passed else 1

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
```

**Reemplaza (versión nueva completa)** `verification/__main__.py`

```python
"""Corre una verificación del producto y termina con su código de salida.

Uso: ``uv run python -m verification <paso>``, con uno de estos pasos:

- ``unit``: las pruebas que escribió qa-unit, con cobertura de 80 % o más.
- ``contract``: las pruebas de la fábrica contra el producto corriendo.
- ``qa``: la parte de QA.md que revisa un programa (``verification/qa.py``).
- ``e2e``: las pruebas de Playwright que escribió qa-e2e (``verification/e2e.py``).
- ``evaluate``: costo y calidad contra la línea base (``verification/evaluate.py``).
- ``production <url>``: la prueba de humo contra Render (``verification.production``).

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
    "production": ([sys.executable, "-m", "verification.production"], ROOT),
}

def run(step: str, extra: list[str] | None = None) -> int:
    """Corre la verificación ``step`` e imprime ``[OK]`` o ``[FAIL]``.

    ``extra`` son argumentos para el paso, por ejemplo la URL de ``production``.
    """
    if step not in STEPS:
        print(f"Uso: python -m verification {{{'|'.join(STEPS)}}}")
        return 2
    command, folder = STEPS[step]
    if not (PRODUCT / "app").is_dir():
        print(f"[FAIL] {step}: todavía no existe product/app/")
        return 1
    code = subprocess.run(command + (extra or []), cwd=folder, check=False).returncode
    print(f"[{'OK' if code == 0 else 'FAIL'}] {step}")
    return code

if __name__ == "__main__":
    sys.exit(run(sys.argv[1] if len(sys.argv) > 1 else "", sys.argv[2:]))
```

### Paso 5 · Publicar y el orquestador final (10 min)

Crea tu repositorio privado y hace el push, solo si existe la aprobación:

**Escribe** `scripts/publish.py`

```python
"""Publica el producto: crea su repositorio privado en GitHub y hace el push.

Uso: ``uv run python scripts/publish.py <nombre-del-repositorio>``

Solo corre si una persona aprobó (existe ``output/approved.txt``); además, el hook
``hooks/permissions.py`` bloquea este comando sin esa aprobación. Render toma el
código de ese repositorio y publica cuando el pipeline de CI pasa.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PRODUCT = ROOT / "product"
APPROVAL = ROOT / "output" / "approved.txt"
MESSAGE = "HR assistant built by the agent factory"

def problems() -> list[str]:
    """Lo que impide publicar; vacía si se puede.

    :return: Un texto por problema
    :rtype: list[str]
    """
    found = []
    if not APPROVAL.exists():
        found.append("falta la aprobación de una persona (output/approved.txt)")
    ignore = PRODUCT / ".gitignore"
    if not ignore.exists() or ".env" not in ignore.read_text(encoding="utf-8"):
        found.append("product/.gitignore debe excluir .env")
    if not (PRODUCT / "render.yaml").exists():
        found.append("falta product/render.yaml")
    return found

def commands(repo: str, first_time: bool) -> list[list[str]]:
    """Los comandos de git y gh, en orden.

    :param repo: Nombre del repositorio en GitHub
    :type repo: str
    :param first_time: ``True`` si el producto todavía no es un repositorio
    :type first_time: bool
    :return: Cada comando como lista de argumentos
    :rtype: list[list[str]]
    """
    commit = [["git", "add", "-A"], ["git", "commit", "-m", MESSAGE]]
    if first_time:
        return [["git", "init", "-b", "main"], *commit,
                ["gh", "repo", "create", repo, "--private", "--source", ".", "--push"]]
    return [*commit, ["git", "push"]]

def main(args: list[str]) -> int:
    """Revisa que se pueda publicar y corre los comandos; 0 si todo sale bien."""
    if len(args) != 1:
        print("Uso: python scripts/publish.py <nombre-del-repositorio>")
        return 2
    found = problems()
    for problem in found:
        print(f"  {problem}")
    if found:
        print("[FAIL] publish")
        return 1
    for command in commands(args[0], not (PRODUCT / ".git").exists()):
        print("$", " ".join(command))
        if subprocess.run(command, cwd=PRODUCT, check=False).returncode != 0:
            print("[FAIL] publish")
            return 1
    print("[OK] publish")
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
```

Pregunta dos veces: el plan y la publicación. `--aprobar` solo aprueba el plan:

**Reemplaza (versión nueva completa)** `.claude/skills/factory/SKILL.md`

```markdown
---
description: >-
```

`La fábrica de la sesión 4 · architect → aprobación → qa-unit → [security`∥ `deploy`∥ `qa-e2e] → compuertas → qa-style → APROBACIÓN DE PUBLICAR → publish`

```text
  → Render (persona) → humo → triage (máx. 2). Ejemplo /factory hr-assistant
argument-hint: "<nombre-del-repositorio> [--aprobar]"
disable-model-invocation: true
allowed-tools: >-
  Agent, Read, Write, AskUserQuestion, Bash(uv run python -m verification *),
  Bash(uv run python scripts/pipeline.py), Bash(uv run python
  scripts/publish.py *)
---
Eres el SUPERVISOR de la fábrica. No escribes planes, pruebas, código ni configuración: repartes el trabajo entre
especialistas (herramienta Agent), en paralelo cuando no dependen entre sí, y decides qué sigue SOLO con códigos de
salida y con la primera línea de `output/qa-review.md` y de `output/triage.md`.

Entrada: $ARGUMENTS. La primera palabra es el nombre del repositorio que se va a crear en GitHub (por omisión,
`hr-assistant`).
- `--aprobar` aprueba por adelantado **solo el plan** (paso 2). **Publicar siempre se pregunta** (paso 7).
- Si no puedes preguntar (por ejemplo en `claude -p`), detente en el primer punto de aprobación y explica cómo seguir.

Si `product/app/` no existe, detente y di: «Copia primero el producto de la sesión 3 (ver README.md)».

Antes del paso 1, escribe `output/activity.jsonl` vacío: la bitácora del hook empieza con esta corrida.
Lleva una bitácora: una línea por paso con lo que pasó.

1. **Plan.** Lanza `architect` con: «Actualiza el plan para spec/04-production.md».
2. **Aprobación del plan.** Muestra `output/plan.md` y pregunta: «¿Apruebas el plan? Escribe si o tus comentarios».
   Con comentarios, relanza `architect` con ellos. Máximo 2 rechazos; al tercero → ESCALAR (paso 10).
3. **Pruebas primero.** Lanza `qa-unit` con: «Agrega las pruebas de spec/04-production.md».
   Corre `uv run python -m verification unit`; debe FALLAR (rojo).
4. **Especialistas en paralelo.** En UN SOLO mensaje lanza los tres:
   - `security` con «Implementa los puntos 1 a 4 de spec/04-production.md».
   - `deploy` con «Prepara los puntos 5 a 8 de spec/04-production.md. El repositorio y el servicio de Render se
     llaman <nombre-del-repositorio>».
   - `qa-e2e` con «Actualiza las pruebas de punta a punta según spec/04-production.md».
5. **Unión y compuertas (máximo 2 correcciones).** Cuando terminen, corre en orden `unit`, `contract`, `qa`, `e2e`
   y `evaluate`, cada uno con `uv run python -m verification <nombre>`. Al primer fallo decide quién corrige:
   - Una prueba e2e mal escrita → `qa-e2e`.
   - Falta una librería en `requirements.txt` o algo de la aplicación o la página → `security`.
   Vuelve a empezar este paso. Tras 2 correcciones sin pasar → ESCALAR.
6. **Evaluador-optimizador (máximo 2 vueltas).** Lanza `qa-style` con «Revisa el producto». Si la primera línea de
   `output/qa-review.md` es `CAMBIOS`, manda cada hallazgo a su dueño:
   - Código → `security`.
   - Dockerfile, CI o `render.yaml` → `deploy`.
   - Documentos → `architect`.

   Repite el paso 5 y lanza `qa-style` con «Revisa el producto (segunda vuelta)». Tras 2 vueltas con CAMBIOS → ESCALAR.
7. **Aprobación para publicar (humano en el lazo).** Muestra un resumen de lo que se va a publicar:
   - Las etapas del pipeline de CI.
   - Los secretos que la persona debe poner en Render.
   - El nombre del repositorio.

   Pregunta: «¿Publico en GitHub para que Render lo despliegue? Escribe si o no».
   - Con «no» → DETENIDA POR LA PERSONA (paso 10).
   - Con «si» → escribe `output/approved.txt` con la fecha y la frase «Aprobado por la persona».
8. **Publicar.** Corre `uv run python scripts/publish.py <nombre-del-repositorio>`. Si falla → ESCALAR.
   Luego dile a la persona, en pasos numerados, que:
   1. Abra la pestaña Actions del repositorio y vea las cuatro etapas.
   2. Entre en Render > New > Blueprint y conecte el repositorio.
   3. Escriba los secretos en Render > Environment. Nunca en el chat.
   4. Cuando el servicio esté Live, le pase la URL y defina `SMOKE_API_KEY` en su terminal, sin pegarla aquí.

   Espera la URL.
9. **Humo y triage (máximo 2 ciclos).** Corre `uv run python -m verification production <url>`.
   - Si pasa → LISTA.
   - Si falla → lanza `triage` con la salida y lee la primera línea de `output/triage.md`:
     - `security` o `deploy` → relánzalo con el diagnóstico. Corre `scripts/publish.py` de nuevo (el push redespliega)
       y repite este paso.
     - `persona` → muéstrale el diagnóstico y espera a que diga que lo resolvió.

   Tras 2 ciclos sin pasar → ESCALAR.
10. **Pipeline y reporte.** Corre `uv run python scripts/pipeline.py`. Escribe `output/report.md` con:
    - El estado (LISTA, DETENIDA POR LA PERSONA o ESCALAR A UNA PERSONA).
    - La URL pública, si la hay.
    - Las correcciones, las vueltas de QA y los ciclos de triage.
    - La tabla de `evaluate`.
    - La bitácora y un enlace a `output/pipeline.md`.

    Responde con el mismo resumen.

Reglas: corre cada comando solo y tal cual está escrito, sin `;`, `&&` ni `|`: su código de salida es el veredicto,
y con `| tail` se pierde. Nunca edites tú los archivos de `product/`. Nunca te saltes un paso, una verificación ni
una aprobación. Nunca leas `.env` ni pidas, repitas o escribas una clave.
```

**Reemplaza (versión nueva completa)** `CLAUDE.md`

```markdown
# Fábrica del HR Assistant (Módulo 4, sesión 4)

Los agentes construyen el producto en `product/` a partir de la especificación de `spec/`. Las personas dirigen,
aprueban y comprueban: no programan.

- `/factory` corre la fábrica completa.
- `.claude/agents/`: architect, qa-unit, developer, observability, qa-style, costs, qa-e2e,
  security, deploy, triage.
- `hooks/permissions.py`: cada agente escribe solo en sus carpetas; nadie lee `.env` y nadie publica sin
  `output/approved.txt`.
- `hooks/activity_log.py`: bitácora de cada herramienta; `scripts/pipeline.py` dibuja el pipeline.
- `verification/`: el código decide si un paso terminó bien, no el agente.

## Reglas

- El orquestador delega: nunca escribe en `product/` (corrige al agente, no su resultado).
- Todo bucle tiene tope: 2 rechazos del plan, 2 correcciones y 2 vueltas de qa-style; después se escala a una persona.
- Una persona aprueba el plan antes de que se escriba código, y aprueba antes de publicar.
- Nunca leas `.env`.
- Código en inglés; comentarios, docstrings, documentos y mensajes a las personas en español. Sin emojis.
  Es una excepción acordada a QA.md, que pide todo en inglés: no la reportes como incumplimiento.
```

### Paso 6 · Las pruebas de la fábrica (10 min)

**Reemplaza (versión nueva completa)** `tests/test_permissions.py`

```python
"""Pruebas del hook de permisos: cada agente escribe solo en sus carpetas."""

import json
import subprocess
import sys

import pytest

from hooks import permissions
from hooks.permissions import ROOT, check

def write(agent, path, tool="Write"):
    return {"agent_type": agent, "tool_name": tool, "tool_input": {"file_path": path}}

@pytest.mark.parametrize(
    "agent, path",
    [
        ("architect", "output/plan.md"),
        ("deploy", "product/.github/workflows/ci.yml"),
        ("security", "product/doc/compliance-checklist.md"),
        ("architect", "product/doc/adr/0001-stateless-api.md"),
        ("qa-unit", "product/tests/test_agent.py"),
        ("developer", "product/app/main.py"),
        ("developer", "product/requirements.txt"),
    ],
)
def test_agent_can_write_in_its_folders(agent, path):
    assert check(write(agent, path)) is None

def test_developer_cannot_write_tests():
    reason = check(write("developer", "product/tests/test_agent.py"))
    assert "developer no puede escribir product/tests/test_agent.py" in reason

def test_qa_unit_cannot_write_code():
    assert check(write("qa-unit", "product/app/main.py", tool="Edit")) is not None

def test_absolute_paths_are_checked_too():
    assert check(write("developer", str(ROOT / "product/app/main.py"))) is None
    assert check(write("developer", str(ROOT / "hooks/permissions.py"))) is not None

def test_paths_outside_the_project_are_blocked():
    assert "no puede escribir" in check(write("developer", "product/app/../../../x"))

def test_reading_and_the_orchestrator_are_not_restricted():
    assert check({"agent_type": "developer", "tool_name": "Read"}) is None
    assert check(write(None, "product/app/main.py")) is None

@pytest.mark.parametrize("agent, code", [("developer", 0), ("qa-unit", 2)])
def test_hook_exit_code_tells_claude_code_what_to_do(agent, code):
    event = json.dumps(write(agent, "product/app/main.py"))
    hook = subprocess.run(
        [sys.executable, str(ROOT / "hooks/permissions.py")],
        input=event,
        capture_output=True,
        text=True,
        check=False,
    )
    assert hook.returncode == code

def test_architect_cannot_approve_its_own_publication():
    assert check(write("architect", "output/approved.txt")) is not None

@pytest.mark.parametrize(
    "tool, tool_input",
    [
        ("Read", {"file_path": "product/.env"}),
        ("Bash", {"command": "uv run --env-file .env uvicorn app.main:app"}),
        ("Grep", {"pattern": "TOKEN", "path": ".env"}),
    ],
)
def test_nobody_reads_env_files(tool, tool_input):
    event = {"tool_name": tool, "tool_input": tool_input}
    assert check(event) == "Nadie lee .env: ahí van los secretos."

def test_env_example_and_writing_dockerignore_are_fine():
    example = {"tool_name": "Read", "tool_input": {"file_path": ".env.example"}}
    assert check(example) is None
    dockerignore = write("deploy", "product/.dockerignore")
    dockerignore["tool_input"]["content"] = ".env\n"
    assert check(dockerignore) is None

@pytest.mark.parametrize(
    "command",
    ["uv run python scripts/publish.py hr-assistant", "git push", "gh repo create x"],
)
def test_publishing_needs_human_approval(command, tmp_path, monkeypatch):
    monkeypatch.setattr(permissions, "ROOT", tmp_path)
    event = {"tool_name": "Bash", "tool_input": {"command": command}}
    assert check(event).startswith("Publicar requiere")
    (tmp_path / "output").mkdir()
    (tmp_path / "output" / "approved.txt").write_text("ok", encoding="utf-8")
    assert check(event) is None
```

**Escribe** `tests/test_production.py`

```python
"""Pruebas de la prueba de humo, con un servidor simulado (sin red)."""

import httpx

from verification import production

def fake_render(key_required=True, healthy=True):
    def handler(request):
        if request.url.path == "/health":
            return httpx.Response(200 if healthy else 503)
        has_key = request.headers.get("X-API-Key") == "good-key"
        return httpx.Response(200 if has_key or not key_required else 401)

    return httpx.Client(transport=httpx.MockTransport(handler))

def test_a_healthy_protected_service_passes(capsys):
    assert production.smoke("https://x", "good-key", fake_render())
    assert capsys.readouterr().out.count("[OK]") == 3

def test_a_service_without_keys_fails():
    open_service = fake_render(key_required=False)
    assert not production.smoke("https://x", "good-key", open_service)

def test_a_sleeping_service_fails():
    assert not production.smoke("https://x", "good-key", fake_render(healthy=False))

def test_the_key_must_come_from_the_environment(monkeypatch, capsys):
    monkeypatch.delenv("SMOKE_API_KEY", raising=False)
    assert production.main(["https://x"]) == 2
    assert "SMOKE_API_KEY" in capsys.readouterr().out
```

**Escribe** `tests/test_publish.py`

```python
"""Pruebas del script de publicación, sin tocar GitHub."""

import subprocess

from scripts import publish

def ready(tmp_path, monkeypatch, approved=True):
    product = tmp_path / "product"
    product.mkdir()
    (product / ".gitignore").write_text(".env\n", encoding="utf-8")
    (product / "render.yaml").write_text("services: []\n", encoding="utf-8")
    approval = tmp_path / "approved.txt"
    if approved:
        approval.write_text("Aprobado por la persona", encoding="utf-8")
    monkeypatch.setattr(publish, "PRODUCT", product)
    monkeypatch.setattr(publish, "APPROVAL", approval)
    return product

def test_nothing_is_published_without_approval(tmp_path, monkeypatch, capsys):
    ready(tmp_path, monkeypatch, approved=False)
    assert publish.main(["hr-assistant"]) == 1
    assert "falta la aprobación" in capsys.readouterr().out

def test_the_product_must_ignore_env(tmp_path, monkeypatch):
    product = ready(tmp_path, monkeypatch)
    (product / ".gitignore").write_text("__pycache__/\n", encoding="utf-8")
    assert "product/.gitignore debe excluir .env" in publish.problems()

def test_first_publication_creates_a_private_repository():
    first = publish.commands("hr-assistant", first_time=True)
    assert first[0] == ["git", "init", "-b", "main"]
    assert first[-1][:4] == ["gh", "repo", "create", "hr-assistant"]
    assert "--private" in first[-1]

def test_later_publications_just_push():
    assert publish.commands("hr-assistant", first_time=False)[-1] == ["git", "push"]

def test_publish_runs_each_command_in_the_product(tmp_path, monkeypatch, capsys):
    product = ready(tmp_path, monkeypatch)
    calls = []
    def fake_run(command, cwd, check):
        calls.append((command, cwd, check))
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(publish.subprocess, "run", fake_run)
    assert publish.main(["hr-assistant"]) == 0
    assert all(cwd == product for _, cwd, _ in calls)
    assert "[OK] publish" in capsys.readouterr().out

def test_usage_needs_the_repository_name():
    assert publish.main([]) == 2
```

**Ejecuta**

**Todos los sistemas**

```bash
uv run python scripts/verify.py
```

### Paso 7 · Corre la fábrica hasta la pregunta de publicar (25 min)

El argumento es el nombre del repositorio y del servicio de Render:

**Ejecuta** (en la carpeta de la sesión)

**Todos los sistemas**

```bash
claude
```

**Dentro de Claude Code**

```text
/factory hr-assistant
```

**Mientras tanto, el producto ya exige clave**

```text
sin clave: 401 {"detail":"invalid or missing API key"}
con clave: 200 {"answer":"Según el directorio: {\"id\": \"EMP-0004\", \"name\": \"Jorge Díaz\", \"department\": \"Tecnología\", \"role\": \"Líder técnico\", \"start_date\": \"...
```

**Y se niega a arrancar en producción con el modelo simulado**

```text
ValueError: ENVIRONMENT=production refuses to start: MODEL_PROVIDER must not be fake
```

**Observa:** cuando todo pasó, la fábrica muestra qué va a publicar y pregunta «¿Publico en GitHub para que Render lo despliegue?». Lee el resumen antes de responder.

### Paso 8 · Publica, mira el CI y conecta Render (20 min)

1. Responde `si`. La fábrica escribe `output/approved.txt` y corre `scripts/publish.py`.

2. En GitHub, abre tu repositorio, pestaña **Actions**: las cuatro etapas, una tras otra.

3. En dashboard.render.com: **New > Blueprint** y elige tu repositorio. El resumen debe decir **Create web service**; si dice **Update**, detente.

4. Genera tu clave en tu terminal y escribe en Render `API_KEYS` (`hr-portal:<clave>`), `CF_ACCOUNT_ID` y `CF_API_TOKEN`. Pulsa **Apply** y espera **Live**.

**macOS / Linux**

```bash
python3 -c "import secrets; print('hr-portal:' + secrets.token_urlsafe(24))"
```

**Windows (PowerShell)**

```powershell
uv run python -c "import secrets; print('hr-portal:' + secrets.token_urlsafe(24))"
```

**Observa (Actions)**

```text
JOBS
[OK] style in 31s
[OK] unit in 24s
[OK] e2e in 47s
[OK] docker in 24s
```

> **CUIDADO**
>
> Ningún secreto va en el chat de Claude Code. La fábrica nunca los pide ni los lee.

### Paso 9 · Prueba de humo y triage (15 min)

**Ejecuta**

**macOS / Linux**

```bash
export SMOKE_API_KEY='<la parte después de hr-portal:>'
uv run python -m verification production https://<tu-servicio>.onrender.com
```

**Windows (PowerShell)**

```powershell
$env:SMOKE_API_KEY = '<la parte después de hr-portal:>'
uv run python -m verification production https://<tu-servicio>.onrender.com
```

**Observa**

```text
[OK] GET /health -> 200 (esperado 200)
  [OK] POST /ask sin clave -> 401 (esperado 401)
  [OK] POST /ask con clave -> 200 (esperado 200)
[OK] production
```

Pásale a la fábrica la URL y el resultado, nunca la clave. Si falla, lanza `triage`. Así pasó al preparar el curso:

**Un 401 con clave**

```text
[OK] GET /health -> 200 (esperado 200)
  [OK] POST /ask sin clave -> 401 (esperado 401)
  [FAIL] POST /ask con clave -> 401 (esperado 200)
[FAIL] production
```

**output/triage.md (inicio)**

```text
persona

Qué falló: en https://hr-assistant-fabrica-hv45.onrender.com, `POST /ask` con clave responde 401 cuando se esperaba 200. `GET /health` (200) y `POST /ask` sin clave (401) sí pasan.
```

**Observa:** la clave se había copiado con `hr-portal:` adelante. Le tocaba a una persona, como dijo triage.

![La página final, con el campo de clave](M4_sesion04_img/fig01.png)

*La página final, con el campo de clave*

### Paso 10 · README, commit y cierre del módulo (10 min)

**Reemplaza (versión nueva completa)** `README.md`

````markdown
# Sesión 4 · Producción (la fábrica lo publica con tu aprobación)

La fábrica cierra el producto y lo publica:
- Clave por cliente, límite de peticiones y compliance como código.
- Contenedor y pipeline de CI en GitHub Actions, que los ingenieros ven etapa por etapa.
- Render, que publica solo si el pipeline pasa.

**Ningún agente publica por su cuenta.** Primero apruebas tú, y el hook lo garantiza.

| Paso | Quién | Patrón |
| --- | --- | --- |
| Plan | `architect` y tú lo apruebas | Humano en el lazo |
| Pruebas primero | `qa-unit` | |
| Seguridad, despliegue y e2e **al mismo tiempo** | `security`, `deploy` y `qa-e2e` | Supervisor con especialistas en paralelo |
| unit → contract → qa → e2e → evaluate | El supervisor decide quién corrige (máximo 2) | Flujo con compuertas |
| Revisión contra QA.md | `qa-style` (máximo 2 vueltas) | Evaluador-optimizador |
| **¿Publico?** | **Tú** | Humano en el lazo |
| GitHub, Actions y Render | `scripts/publish.py` y tú conectas Render | |
| Prueba de humo y triage (máximo 2) | `verification production` y `triage` | Enrutamiento de fallas |

El hook `hooks/permissions.py` suma dos reglas para todos, también para el orquestador:
- Nadie lee `.env`.
- Nadie corre `publish.py`, `git push` ni `gh repo create` mientras no exista `output/approved.txt`. Ese archivo solo
  lo escribe el orquestador cuando tú dices «si».

## Preparar

Copia el producto de la sesión 3.

macOS / Linux:

```bash
cd NextGenCode-M4-Agentes/sesion04
cp -R ../sesion03/product product
uv venv --python 3.12
uv pip install -r requirements.txt
uv run playwright install chromium
uv run python scripts/verify.py
```

Windows (PowerShell):
```powershell
cd NextGenCode-M4-Agentes\sesion04
Copy-Item -Recurse ..\sesion03\product product
uv venv --python 3.12
uv pip install -r requirements.txt
uv run playwright install chromium
uv run python scripts/verify.py
```

## Correr la fábrica

La primera vez que abres `claude` en esta carpeta te pregunta **«Do you trust the files in this folder?»**:
responde que sí. Sin esa confianza, Claude Code ignora los permisos de `.claude/settings.json` y los agentes no pueden
correr las verificaciones.

Ejecuta `claude` y, dentro, escribe `/factory hr-assistant`. `hr-assistant` es el nombre del repositorio que se
creará en tu cuenta de GitHub. La fábrica te pregunta dos veces: si apruebas el plan y si publica.

Después del push:

1. En GitHub, abre la pestaña **Actions** del repositorio: verás las etapas `style`, `unit`, `e2e` y `docker`.
2. En Render, entra en **New > Blueprint** y conecta el repositorio.
3. En **Render > Environment**, escribe los secretos:
   - `API_KEYS`, con la forma `hr-portal:<una clave larga>`.
   - `CF_ACCOUNT_ID` y `CF_API_TOKEN`.
   - `LANGSMITH_API_KEY` no se pide: agrégala después en Environment si enciendes las trazas.

   **Nunca los pegues en el chat.**
4. Cuando el servicio esté **Live**, define la clave en tu terminal (no en el chat) y pásale la URL a la fábrica.

macOS / Linux:

```bash
export SMOKE_API_KEY='<tu clave>'
```

Windows (PowerShell):

```powershell
$env:SMOKE_API_KEY = '<tu clave>'
```
## Comprobar

```bash
uv run python -m verification production https://<tu-servicio>.onrender.com
```

Abre la URL en el navegador, escribe tu clave en la página y pregunta «¿Quién es EMP-0004?».
````

**Ejecuta**

**Todos los sistemas**

```bash
git add -A
git commit -m "Sesion 4: security, deploy, triage, publicacion con aprobacion y prueba de humo"
```

**Observa:** `product/` y `output/` no entran al commit: están en `.gitignore`. Versionas la fábrica; el producto se reconstruye corriéndola.

- Construiste una fábrica que construye, prueba, revisa y publica un sistema agéntico.

- Patrones: plan y ejecución, reflexión, compuertas, evaluador-optimizador, supervisor con especialistas en paralelo, humano en el lazo y triage.

- Hooks: mínima agencia, bitácora, secretos y aprobación.

## Estructura final de la carpeta

```text
sesion04/
  .claude/agents/architect.md
  .claude/agents/costs.md
  .claude/agents/deploy.md
  .claude/agents/developer.md
  .claude/agents/observability.md
  .claude/agents/qa-e2e.md
  .claude/agents/qa-style.md
  .claude/agents/qa-unit.md
  .claude/agents/security.md
  .claude/agents/triage.md
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
  scripts/publish.py
  scripts/verify.py
  spec/01-architecture.md
  spec/02-observability.md
  spec/03-costs.md
  spec/04-production.md
  spec/employees.json
  spec/model_prices.json
  tests/__init__.py
  tests/test_activity_log.py
  tests/test_evaluate.py
  tests/test_permissions.py
  tests/test_production.py
  tests/test_publish.py
  tests/test_qa.py
  tests/test_verification.py
  verification/__init__.py
  verification/__main__.py
  verification/contract/conftest.py
  verification/contract/test_contract.py
  verification/contract/test_contract_02.py
  verification/contract/test_contract_03.py
  verification/contract/test_contract_04.py
  verification/e2e.py
  verification/eval_set.json
  verification/evaluate.py
  verification/production.py
  verification/qa.py
  verification/server.py
  product/   (lo genera la fábrica)
  output/    (plan, reporte, bitácora)
```

## Resumen de los pasos

| Paso | Qué se construye | Llama al modelo | Tiempo |
|---|---|---|---|
| 0 | Copia la sesión 3 | No | 10 min |
| 1 | La especificación de producción | No | 10 min |
| 2 | Tres agentes nuevos y uno que cambia | No | 15 min |
| 3 | El hook, versión final | No | 10 min |
| 4 | Verificaciones con clave y la prueba de humo | No | 15 min |
| 5 | Publicar y el orquestador final | No | 10 min |
| 6 | Las pruebas de la fábrica | No | 10 min |
| 7 | Corre la fábrica hasta la pregunta de publicar | Sí | 25 min |
| 8 | Publica, mira el CI y conecta Render | Sí | 20 min |
| 9 | Prueba de humo y triage | Sí | 15 min |
| 10 | README, commit y cierre del módulo | No | 10 min |

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
