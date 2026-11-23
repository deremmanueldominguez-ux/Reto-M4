Certificado · Next-Gen Coding: Desarrollo de Software con IA Generativa (Virtual)

**Módulo 4 · Agentes en producción · Manual de práctica**

# Agentes en producción · Sesión 2 · Observabilidad

La fábrica la agrega y se observa

Una fábrica de agentes de Claude Code construye el HR Assistant, lo prueba, lo revisa y lo publica. Tú diriges, apruebas y compruebas.

**CONTENIDO**

1. Cómo usar esta guía

2. Requisitos para todo el módulo

3. Sesión 2 · Observabilidad: la fábrica la agrega y se observa

4. Estructura final de la carpeta

5. Resumen de los pasos

6. Si algo falla

7. Lista de comprobación

## Cómo usar esta guía

En este módulo construyes, con tus manos, una **fábrica de agentes** de Claude Code. Después la fábrica construye sola el producto (el HR Assistant), lo prueba, lo revisa contra `QA.md` y, en la sesión 4, lo publica cuando tú lo apruebas. Tú no escribes el producto: escribes los agentes, el orquestador, los hooks y las verificaciones que lo construyen.

Es **incremental**: la sesión 1 parte de una carpeta vacía; cada sesión copia la carpeta anterior y le agrega piezas. Lo que construyas hoy es el punto de partida de la siguiente sesión.

| Concepto | Detalle |
|---|---|
| Sesión | 2 de 4 · Observabilidad |
| Hoy | La fábrica agrega observabilidad y se observa a sí misma |
| Patrón de la fábrica | Flujo: encadenamiento con compuertas y evaluador-optimizador |
| Duración | 2 h 30 min, con tiempos pesimistas |
| Carpeta | `NextGenCode-M4-Agentes/sesion02` |

Cada paso tiene tres partes:

- **Escribe:** el archivo completo, con su ruta; tu editor crea las carpetas al guardar. **Reemplaza** quiere decir que el archivo ya existe y cambia: pega la versión nueva completa encima de la anterior.

- **Ejecuta:** el comando para probar ese paso, para macOS / Linux y para Windows.

- **Observa:** lo que debe salir y la idea que deja.

> **CUIDADO**
>
> **Copia el código del archivo Markdown, no del PDF.** Junto con este PDF recibes `M4_sesion02.md`, con el mismo contenido. Al copiar de un PDF, los visores pierden la sangría, y en Python la sangría es parte del código. Lee en el PDF y copia del `.md` (ábrelo en tu editor).

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

## Sesión 2 · Observabilidad: la fábrica la agrega y se observa

Hoy le agregas a la fábrica un agente que construye observabilidad (`request_id`, log JSON, auditoría, `/metrics` con SLO, LangSmith), un agente que revisa contra `QA.md` y un hook que registra cada herramienta de cada agente.

```mermaid
flowchart TD
  obs["observability · código"] --> unit{"unit"}
  unit --> contract{"contract"}
  contract --> qa{"qa"}
  qa -- "falla (máx. 2)" --> obs
  qa --> style{"qa-style · APROBADO o CAMBIOS"}
  style -- "CAMBIOS (máx. 2)" --> obs
  style -- APROBADO --> pipe(["pipeline.md"])
```

### Paso 0 · Copia la sesión 1 (10 min)

**Ejecuta**

**macOS / Linux**

```bash
cd ..
rsync -a --exclude .venv --exclude output --exclude '__pycache__' sesion01/ sesion02/
cd sesion02
uv venv --python 3.12
```

**Windows (PowerShell)**

```powershell
cd ..
robocopy sesion01 sesion02 /E /XD .venv output __pycache__
cd sesion02
uv venv --python 3.12
```

**Observa:** `sesion02` tiene la fábrica **y el producto** de la sesión 1 (`product/`): es el punto de partida. El entorno virtual se crea de nuevo porque guarda rutas absolutas. Abre `claude` una vez y acepta la confianza de la carpeta.

Se agrega `langsmith`:

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
```

**Ejecuta**

**Todos los sistemas**

```bash
uv pip install -r requirements.txt
```

### Paso 1 · La especificación de observabilidad (10 min)

**Escribe** `spec/02-observability.md`

```markdown
# Sesión 2 · Observabilidad: ¿qué pasó con la petición X?

Parte del producto de la sesión 1 (`spec/01-architecture.md`) y le agrega lo necesario para responder, con datos,
qué pasó con cualquier petición.

## Lo que debe hacer

1. **Un id por petición.** Si el cliente manda el encabezado `X-Request-ID`, se usa ese valor; si no, se genera
   un UUID. Toda respuesta lo devuelve en `X-Request-ID`, y `POST /ask` también en el cuerpo, como `request_id`.
2. **Log en JSON, una línea por evento**, en la salida estándar. Cada línea lleva `ts` (ISO 8601 en UTC),
   `service`, `event` y `request_id`. Eventos:
   - `request`: `method`, `path`, `status` y `latency_ms`, uno por cada petición.
   - `agent_run`: `question_chars`, `history_messages`, `steps`, `tools`, `input_tokens`, `output_tokens` y `stopped`.
     **Nunca** el texto de la pregunta ni de la respuesta.
   - `audit`: uno por cada herramienta que llama el agente, con `action: "tool_call"`, `tool` y `args`.
   - `error`: si algo truena, con el tipo de error (no el mensaje completo). La respuesta es `500` con
     `{"detail": "internal error", "request_id": ...}`.
3. **`GET /metrics`** de este proceso:
   `{"pid", "requests", "error_rate", "latency_ms": {"p50", "p95"}, "tokens": {"input", "output"},
   "slo": {"p95_ms_target", "met"}}`. `met` es `true` si el p95 está por debajo de `SLO_P95_MS`.
4. **Trazas en LangSmith (opcional).** Con `LANGSMITH_TRACING=true` y `LANGSMITH_API_KEY`, cada corrida del agente,
   cada llamada al modelo y cada herramienta quedan como trazas (`@traceable`), con el `request_id` en sus metadatos.
   Si `HIDE_INPUTS`/`HIDE_OUTPUTS` valen `true`, no se mandan entradas ni salidas. Sin la clave, el producto
   funciona igual y no intenta conectarse.
5. **La página web** muestra el `request_id` de cada respuesta, para que la persona lo pase a soporte.

## Configuración nueva

| Variable | Por omisión | Para qué |
| --- | --- | --- |
| `SERVICE_NAME` | `hr-assistant` | Campo `service` del log |
| `SLO_P95_MS` | `2000` | Meta de latencia p95 en milisegundos |
| `LANGSMITH_TRACING` | `false` | Enciende las trazas |
| `HIDE_INPUTS` / `HIDE_OUTPUTS` | `true` | No mandar a LangSmith el texto de preguntas ni respuestas (valor seguro por omisión) |

La clave `LANGSMITH_API_KEY` se lee del entorno y nunca se escribe en el log ni en el código.

## Reglas

- La hora se obtiene a través de un reloj inyectado (no `datetime.now()` directo), para que las pruebas sean
  deterministas.
- Se agrega `langsmith` a `requirements.txt`.
- El producto tiene `README.md` (qué es, cómo correrlo y sus variables) y `doc/` con la arquitectura y los ADR.
- Todo lo de la sesión 1 sigue funcionando.

## Cómo se comprueba

- `uv run python -m verification unit`: pruebas del producto, con cobertura de 80 % o más.
- `uv run python -m verification contract`: el contrato de las sesiones 1 y 2.
- `uv run python -m verification qa`: el estilo de QA.md (pylint, 88 columnas, sin emojis, documentos en su lugar).
- `qa-style` revisa lo que un script no ve y escribe `output/qa-review.md`, que empieza con `APROBADO` o `CAMBIOS`.
```

### Paso 2 · Dos agentes: uno construye, otro revisa (15 min)

**Escribe** `.claude/agents/observability.md`

```markdown
---
name: observability
description: >-
  Agrega observabilidad al producto (request_id, log JSON, auditoría,
  /metrics, LangSmith) según spec/02-observability.md, hasta que pasen las
  pruebas. No escribe pruebas. Úsalo después de qa-unit, o para corregir con
  los hallazgos de qa-style.
tools: Read, Glob, Grep, Write, Edit, Bash
---
Eres el ingeniero de observabilidad del HR Assistant.

1. Lee `spec/` (sobre todo `02-observability.md`), `output/plan.md`, el código de `product/app/`, las pruebas de
   `product/tests/` y `QA.md`.
2. Implementa lo que pide la especificación **sin romper** lo de la sesión 1. Actualiza `product/README.md`
   (qué es, cómo correrlo y sus variables) y `product/requirements.txt`.
3. Corre `uv run python -m verification unit` y `uv run python -m verification qa` hasta que pasen.
4. Si te pasan hallazgos de `qa-style` o un error de la verificación, corrígelos todos y di cómo.

Reglas: código en inglés, comentarios y docstrings en español (estilo Sphinx), líneas de máximo 88 caracteres,
sin emojis. La hora, con un reloj inyectado. Nunca escribas claves en el código ni en el log. Solo puedes escribir
en `product/app/`, `product/requirements.txt` y `product/README.md`. No cambies pruebas (no puedes).
Termina con la lista de archivos que cambiaste y el resultado de las pruebas.

En Bash solo puedes correr `uv run python -m verification <paso>`; para leer usa Read, Glob y Grep (nunca
`cat`, `grep` ni `cd` en Bash).
```

El revisor no corrige: devuelve hallazgos. Su primera línea, `APROBADO` o `CAMBIOS`, decide el camino:

**Escribe** `.claude/agents/qa-style.md`

```markdown
---
name: qa-style
description: >-
  Revisa el producto contra QA.md (lo que un script no ve) y escribe
  output/qa-review.md con APROBADO o CAMBIOS. No corrige: devuelve hallazgos.
  Úsalo después de que pasan las verificaciones.
tools: Read, Glob, Grep, Write, Bash
---
Eres el revisor de QA. Tu trabajo es decir qué falta para cumplir `QA.md`, no arreglarlo.

1. Lee `QA.md`, `spec/` y todo `product/` (código, pruebas, README y `doc/`).
2. Corre `uv run python -m verification qa` y toma en cuenta su resultado.
3. Revisa lo que un programa no ve:
   - Nombres claros en inglés.
   - Funciones pequeñas con una sola responsabilidad.
   - Valores fijos que deberían ser configuración.
   - Docstrings estilo Sphinx en lo público.
   - Manejo de errores.
   - Que el README explique cómo correrlo.
   - Que los ADR sigan vigentes.
   - Que el log no tenga datos personales ni claves.
4. Escribe `output/qa-review.md`:
   - Primera línea: `APROBADO` o `CAMBIOS`, sola.
   - Después, si hay cambios, **máximo 5 hallazgos**, los más importantes. Cada uno con el archivo, qué incumple
     (cita la regla de QA.md) y qué hacer. Nada de detalles de gusto personal.
   - Apruebas si no hay nada que **claramente** incumpla QA.md, aunque se pueda mejorar. Lo mecánico (estilo,
     PEP8, largo de línea) ya lo decide `verification qa`: no lo repitas.
   - **Si te dicen que es una segunda vuelta**, revisa solo que se corrigieron los hallazgos de la primera
     (están en `output/qa-review.md`) y que no haya un incumplimiento grave nuevo. No agregues mejoras opcionales.

Escribe en español y sin emojis. Solo puedes escribir `output/qa-review.md`.
Termina con la primera línea de tu revisión.

En Bash solo puedes correr `uv run python -m verification <paso>`; para leer usa Read, Glob y Grep (nunca
`cat`, `grep` ni `cd` en Bash).
```

> **PATRÓN DE FLUJO: EVALUADOR-OPTIMIZADOR**
>
> Un agente produce y otro evalúa, hasta aprobar o llegar al tope. Lo mecánico lo decide un programa; en la segunda vuelta el revisor solo revisa lo que pidió.

### Paso 3 · La verificación de QA.md (15 min)

Lo que un programa sí puede revisar: pylint en 10, sin emojis, documentos en su lugar:

**Escribe** `verification/qa.py`

```python
"""La parte de QA.md que un programa puede revisar en el producto.

- pylint sobre ``app`` y ``tests``, con líneas de máximo 88 caracteres.
- Ningún emoji en el código ni en los documentos.
- En la raíz del producto, el único Markdown es ``README.md``; el resto va en ``doc/``.

Lo que un programa no ve (nombres claros, funciones pequeñas, valores fijos en el
código) lo revisa el agente ``qa-style``.
"""

import subprocess
import sys
from pathlib import Path

PRODUCT = Path(__file__).resolve().parent.parent / "product"
PYLINT = [
    sys.executable, "-m", "pylint", "app", "tests", "--max-line-length=88",
    "--fail-under=10",
    "--disable=missing-function-docstring,redefined-outer-name,too-few-public-methods",
]

def has_emoji(text: str) -> bool:
    """Indica si el texto tiene emojis o símbolos gráficos."""
    return any(ord(c) > 0xFFFF or 0x2600 <= ord(c) <= 0x27BF for c in text)

def problems(product: Path) -> list[str]:
    """Lista lo que incumple QA.md, sin contar pylint.

    :param product: Carpeta del producto
    :type product: pathlib.Path
    :return: Un texto por problema; vacía si todo está bien
    :rtype: list[str]
    """
    found = []
    for path in sorted(product.rglob("*")):
        relative = path.relative_to(product).as_posix()
        is_text = path.suffix in {".py", ".md", ".html"}
        if is_text and has_emoji(path.read_text("utf-8")):
            found.append(f"emoji en {relative}")
        if path.suffix == ".md" and "/" not in relative and relative != "README.md":
            found.append(f"{relative} debe ir en doc/")
    if not (product / "README.md").exists():
        found.append("falta README.md")
    return found

def main() -> int:
    """Corre pylint y las revisiones de archivos; 0 si todo pasa."""
    lint = subprocess.run(PYLINT, cwd=PRODUCT, check=False).returncode
    found = problems(PRODUCT)
    for problem in found:
        print(f"  {problem}")
    ok = lint == 0 and not found
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
```

Se agrega el paso `qa`:

**Reemplaza (versión nueva completa)** `verification/__main__.py`

```python
"""Corre una verificación del producto y termina con su código de salida.

Uso: ``uv run python -m verification unit`` (o ``contract``, o ``qa``)

- ``unit``: las pruebas que escribió qa-unit, con cobertura de 80 % o más.
- ``contract``: las pruebas de la fábrica contra el producto corriendo.
- ``qa``: la parte de QA.md que revisa un programa (``verification/qa.py``).

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

El contrato de la sesión 2:

**Escribe** `verification/contract/test_contract_02.py`

```python
"""Contrato de la sesión 2: cada petición se puede rastrear y medir."""

import uuid

def test_every_response_carries_a_request_id(api):
    request_id = api.get("/health").headers["X-Request-ID"]
    assert uuid.UUID(request_id)

def test_the_client_request_id_is_kept(api):
    response = api.post(
        "/ask", json={"question": "¿Quién es EMP-0004?"},
        headers={"X-Request-ID": "demo-123"},
    )
    assert response.headers["X-Request-ID"] == "demo-123"
    assert response.json()["request_id"] == "demo-123"

def test_metrics_report_latency_tokens_and_slo(api):
    api.post("/ask", json={"question": "¿Quién es EMP-0004?"})
    metrics = api.get("/metrics").json()
    assert metrics["requests"] >= 1
    assert set(metrics["latency_ms"]) == {"p50", "p95"}
    assert metrics["tokens"]["input"] > 0
    assert isinstance(metrics["slo"]["met"], bool)

def test_home_page_shows_the_request_id(api):
    assert "request_id" in api.get("/").text
```

### Paso 4 · El hook de bitácora (15 min)

Un hook **PostToolUse**: después de cada herramienta escribe una línea JSON con rutas relativas, para no exponer carpetas personales:

**Escribe** `hooks/activity_log.py`

```python
"""Hook PostToolUse: la fábrica también se observa.

Después de cada herramienta, de cualquier agente, agrega una línea JSON a
``output/activity.jsonl``: cuándo, quién, qué herramienta y si salió bien. Con
esa bitácora ``scripts/pipeline.py`` dibuja el pipeline de la corrida.
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOG = ROOT / "output" / "activity.jsonl"

def entry(event: dict, now: datetime) -> dict:
    """Arma la línea de la bitácora a partir del evento de Claude Code."""
    tool_input = event.get("tool_input", {})
    target = (tool_input.get("subagent_type") or tool_input.get("command")
              or tool_input.get("file_path"))
    return {
        "ts": now.isoformat(timespec="seconds"),
        "agent": event.get("agent_type") or "orchestrator",
        "tool": event.get("tool_name"),
        # Rutas relativas al proyecto: la bitácora no expone carpetas personales
        "target": target.replace(f"{ROOT}{os.sep}", "").replace(f"{ROOT}/", "")
        if target else None,
        "ok": event.get("hook_event_name") != "PostToolUseFailure",
    }

if __name__ == "__main__":
    LOG.parent.mkdir(exist_ok=True)
    line = entry(json.load(sys.stdin), datetime.now(timezone.utc))
    with LOG.open("a", encoding="utf-8") as log:
        log.write(json.dumps(line, ensure_ascii=False) + "\n")
```

Los dos agentes nuevos y dónde pueden escribir:

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

Registra la bitácora para las herramientas que salen bien y las que fallan:

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
      "Bash(uv run python scripts/pipeline.py)"
    ]
  },
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit|MultiEdit|NotebookEdit",
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

### Paso 5 · El pipeline de la fábrica (10 min)

Lee la bitácora y dibuja la corrida en `output/pipeline.md`: un diagrama Mermaid y una tabla de tiempos:

**Escribe** `scripts/pipeline.py`

````python
"""Dibuja el pipeline de la última corrida a partir de la bitácora de la fábrica.

Lee ``output/activity.jsonl`` (lo escribe ``hooks/activity_log.py``), se queda con
los pasos del orquestador (cada agente y cada verificación) y escribe
``output/pipeline.md``: un diagrama Mermaid, que GitHub y los editores dibujan,
y una tabla con lo que tardó cada paso. Los agentes lanzados juntos quedan en la
misma columna: corrieron en paralelo.

Uso: ``uv run python scripts/pipeline.py``
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOG = ROOT / "output" / "activity.jsonl"
PIPELINE = ROOT / "output" / "pipeline.md"
# Agentes lanzados con menos de estos segundos de diferencia corrieron en paralelo
PARALLEL_GAP = 10

def step_name(event: dict) -> str | None:
    """Nombre del paso: el agente lanzado o la verificación corrida."""
    target = str(event.get("target") or "")
    if event["tool"] == "Agent":
        return target
    found = re.search(r"verification (\w+)", target)
    return f"verify {found.group(1)}" if event["tool"] == "Bash" and found else None

def last_activity(events: list[dict], agent: str, since: datetime) -> datetime:
    """Hora de la última herramienta de ``agent`` desde ``since``.

    Sirve para los agentes en paralelo: su lanzamiento regresa de inmediato,
    pero siguen trabajando. Se cuenta hasta que el orquestador lo vuelve a lanzar.
    """
    relaunches = [
        e["time"] for e in events
        if e["agent"] == "orchestrator"
        and e.get("target") == agent
        and e["time"] > since
    ]
    until = min(relaunches, default=datetime.max.replace(tzinfo=since.tzinfo))
    times = [
        e["time"] for e in events if e["agent"] == agent and since <= e["time"] < until
    ]
    return max(times, default=since)

def steps(lines: list[str]) -> list[dict]:
    """Pasos del orquestador con su duración en segundos.

    Un agente se mide desde la acción anterior del orquestador hasta su última
    herramienta. Una verificación, desde lo último que pasó hasta que termina.

    :param lines: Líneas JSON de la bitácora
    :type lines: list[str]
    :return: Pasos con ``name``, ``ok``, ``launch``, ``is_agent`` y ``seconds``
    :rtype: list[dict]
    """
    events = [json.loads(line) for line in lines if line.strip()]
    for event in events:
        event["time"] = datetime.fromisoformat(event["ts"])
    found, previous_any, previous_orchestrator = [], None, None
    for event in events:
        moment = event["time"]
        before_any, previous_any = previous_any or moment, moment
        if event["agent"] != "orchestrator":
            continue
        before, previous_orchestrator = previous_orchestrator or moment, moment
        name = step_name(event)
        if not name:
            continue
        is_agent = event["tool"] == "Agent"
        start = before if is_agent else before_any
        end = last_activity(events, name, moment) if is_agent else moment
        seconds = int((end - start).total_seconds())
        found.append({"name": name, "ok": event["ok"], "launch": moment,
                      "is_agent": is_agent, "seconds": seconds})
    return found

def columns(found: list[dict]) -> list[list[int]]:
    """Agrupa en columnas los pasos; los agentes lanzados juntos comparten columna.

    :return: Listas de índices de ``found``, en orden
    :rtype: list[list[int]]
    """
    grouped: list[list[int]] = []
    for index, step in enumerate(found):
        head: dict = found[grouped[-1][0]] if grouped else {}
        together = head.get("is_agent") and step["is_agent"] and (
            (step["launch"] - head["launch"]).total_seconds() <= PARALLEL_GAP
        )
        if together:
            grouped[-1].append(index)
        else:
            grouped.append([index])
    return grouped

def render(found: list[dict]) -> str:
    """Convierte los pasos en Markdown con un diagrama Mermaid y una tabla.

    :param found: Pasos de :func:`steps`
    :type found: list[dict]
    :return: El contenido de ``output/pipeline.md``
    :rtype: str
    """
    nodes = [
        f'  s{n}["{s["name"]}<br/>{s["seconds"]} s"]:::{"ok" if s["ok"] else "fail"}'
        for n, s in enumerate(found)
    ]
    grouped = columns(found)
    arrows = [
        f"  s{a} --> s{b}"
        for before, after in zip(grouped, grouped[1:])
        for a in before
        for b in after
    ]
    rows = [
        f"| {n + 1} | {s['name']} | {'pasó' if s['ok'] else 'falló'} | {s['seconds']} |"
        for n, s in enumerate(found)
    ]
    return "\n".join(
        ["# Pipeline de la fábrica", "", "```mermaid", "flowchart LR", *nodes, *arrows,
         "  classDef ok fill:#d4f4dd,stroke:#1e7b3a",
         "  classDef fail fill:#fde2e2,stroke:#a12a2a", "```", "",
         "| # | Paso | Resultado | Segundos |", "| --- | --- | --- | --- |", *rows, ""]
    )

def main() -> int:
    """Escribe ``output/pipeline.md`` y dice cuántos pasos encontró."""
    if not LOG.exists():
        print("[FAIL] no existe output/activity.jsonl: corre primero /factory")
        return 1
    found = steps(LOG.read_text(encoding="utf-8").splitlines())
    PIPELINE.write_text(render(found), encoding="utf-8")
    print(f"[OK] {len(found)} pasos en {PIPELINE.relative_to(ROOT).as_posix()}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
````

### Paso 6 · El orquestador, versión 2 (10 min)

Ahora encadena tres compuertas y agrega la revisión de `qa-style`:

**Reemplaza (versión nueva completa)** `.claude/skills/factory/SKILL.md`

```markdown
---
description: >-
  La fábrica de la sesión 2 · architect → aprobación → qa-unit → observability
  → verificación → qa-style (evaluador-optimizador, máx. 2) → pipeline y
  reporte. Ejemplo /factory
argument-hint: "[--aprobar]"
disable-model-invocation: true
allowed-tools: >-
  Agent, Read, Write, AskUserQuestion, Bash(uv run python -m verification *),
  Bash(uv run python scripts/pipeline.py)
---
Eres el ORQUESTADOR de la fábrica. No escribes planes, pruebas ni código: delegas cada paso en su agente
(herramienta Agent) y decides qué sigue SOLO con códigos de salida y con la primera línea de `output/qa-review.md`.

Entrada: $ARGUMENTS. Si trae `--aprobar`, la persona aprobó por adelantado: no preguntes en el paso 2.
Si no lo trae y no puedes preguntar (por ejemplo en `claude -p`), detente en el paso 2 y explica cómo seguir.

Si `product/app/` no existe, detente y di: «Copia primero el producto de la sesión 1 (ver README.md)».

Antes del paso 1, escribe `output/activity.jsonl` vacío: la bitácora del hook empieza con esta corrida.
Lleva una bitácora: una línea por paso con lo que pasó.

1. **Plan.** Lanza `architect` con: «Actualiza el plan para spec/02-observability.md».
2. **Aprobación humana.** Muestra `output/plan.md` y pregunta: «¿Apruebas el plan? Escribe si o tus comentarios».
   Con comentarios, relanza `architect` con ellos. Máximo 2 rechazos; al tercero → ESCALAR (paso 7).
3. **Pruebas primero.** Lanza `qa-unit` con: «Agrega las pruebas de spec/02-observability.md».
   Corre `uv run python -m verification unit`; debe FALLAR (rojo).
4. **Código.** Lanza `observability` con: «Implementa spec/02-observability.md hasta que pasen product/tests/».
5. **Encadenamiento con compuertas (máximo 2 correcciones).** Corre en orden `uv run python -m verification unit`,
   `uv run python -m verification contract` y `uv run python -m verification qa`. Al primer fallo, relanza
   `observability` con «La verificación <nombre> falló; corrige esto: <últimas 40 líneas>» y vuelve a empezar
   este paso. Tras 2 correcciones sin pasar → ESCALAR.
6. **Evaluador-optimizador (máximo 2 vueltas).** Lanza `qa-style` con «Revisa el producto». Lee la primera línea
   de `output/qa-review.md`:
   - `APROBADO` → LISTA.
   - `CAMBIOS` → relanza `observability` con «Corrige los hallazgos de output/qa-review.md», repite el paso 5 y
     vuelve a lanzar `qa-style` con «Revisa el producto (segunda vuelta)». Tras 2 vueltas con CAMBIOS → ESCALAR.
7. **Pipeline y reporte.** Corre `uv run python scripts/pipeline.py`. Escribe `output/report.md` con el estado
   (LISTA, DETENIDA POR LA PERSONA o ESCALAR A UNA PERSONA), las correcciones y vueltas de QA, la bitácora y un
   enlace a `output/pipeline.md`. Si quedó LISTA, agrega cómo abrir la página y ver el log y las métricas:
   `cd product`, `uv run uvicorn app.main:app`, http://127.0.0.1:8000 y http://127.0.0.1:8000/metrics.
   Responde con el mismo resumen.

Reglas: corre cada verificación sola y tal cual está escrita, sin `;`, `&&` ni `|`: su código de salida es el veredicto, y con `| tail` se pierde. Nunca edites tú los archivos de
`product/`. Nunca te saltes un paso ni una verificación. No leas `.env`.
```

**Reemplaza (versión nueva completa)** `CLAUDE.md`

```markdown
# Fábrica del HR Assistant (Módulo 4, sesión 2)

Los agentes construyen el producto en `product/` a partir de la especificación de `spec/`. Las personas dirigen,
aprueban y comprueban: no programan.

- `/factory` corre la fábrica completa.
- `.claude/agents/`: architect, qa-unit, developer, observability, qa-style.
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

> **PATRÓN DE FLUJO: ENCADENAMIENTO CON COMPUERTAS**
>
> Cada paso solo empieza si el anterior pasó su verificación. Al primer fallo se corrige y la cadena vuelve a empezar.

### Paso 7 · Las pruebas de las piezas nuevas (10 min)

**Escribe** `tests/test_activity_log.py`

```python
"""Pruebas del hook de bitácora y del dibujo del pipeline."""

import json
from datetime import datetime, timezone

from scripts import pipeline
from hooks.activity_log import ROOT, entry

NOW = datetime(2026, 11, 4, 18, 0, tzinfo=timezone.utc)

def test_subagent_tools_are_logged_with_their_agent():
    event = {"agent_type": "qa-unit", "tool_name": "Write",
             "tool_input": {"file_path": "product/tests/test_x.py"},
             "hook_event_name": "PostToolUse"}
    assert entry(event, NOW) == {
        "ts": "2026-11-04T18:00:00+00:00", "agent": "qa-unit", "tool": "Write",
        "target": "product/tests/test_x.py", "ok": True,
    }

def test_paths_inside_the_project_are_logged_relative():
    event = {"agent_type": "developer", "tool_name": "Write",
             "tool_input": {"file_path": f"{ROOT}/product/app/main.py"}}
    assert entry(event, NOW)["target"] == "product/app/main.py"

def test_orchestrator_steps_and_failures_are_logged():
    event = {"tool_name": "Bash", "hook_event_name": "PostToolUseFailure",
             "tool_input": {"command": "uv run python -m verification unit"}}
    line = entry(event, NOW)
    assert line["agent"] == "orchestrator"
    assert line["ok"] is False

def log_line(minute, agent, tool, target, ok=True):
    ts = f"2026-11-04T18:{minute:02d}:00+00:00"
    line = {"ts": ts, "agent": agent, "tool": tool, "target": target, "ok": ok}
    return json.dumps(line)

LINES = [
    log_line(0, "orchestrator", "Read", "spec/01-architecture.md"),
    log_line(1, "architect", "Write", "output/plan.md"),
    log_line(2, "orchestrator", "Agent", "architect"),
    log_line(5, "orchestrator", "Bash", "uv run python -m verification unit", ok=False),
    log_line(9, "orchestrator", "Read", "output/plan.md"),
]

def summary(found):
    return [(s["name"], s["ok"], s["seconds"]) for s in found]

def test_pipeline_keeps_only_agents_and_verifications():
    assert summary(pipeline.steps(LINES)) == [
        ("architect", True, 120),
        ("verify unit", False, 180),
    ]

PARALLEL = [
    log_line(0, "orchestrator", "Read", "output/plan.md"),
    log_line(1, "orchestrator", "Agent", "costs"),
    log_line(1, "orchestrator", "Agent", "qa-e2e"),
    log_line(3, "qa-e2e", "Write", "product/e2e/test_page.py"),
    log_line(6, "costs", "Edit", "product/app/main.py"),
    log_line(7, "orchestrator", "Bash", "uv run python -m verification unit"),
]

def test_parallel_agents_are_measured_by_their_own_work():
    assert summary(pipeline.steps(PARALLEL)) == [
        ("costs", True, 360),
        ("qa-e2e", True, 120),
        ("verify unit", True, 60),
    ]

def test_parallel_agents_share_a_column_in_the_diagram():
    text = pipeline.render(pipeline.steps(PARALLEL))
    for arrow in ("s0 --> s2", "s1 --> s2"):
        assert arrow in text

def test_pipeline_is_a_mermaid_diagram_with_a_table():
    text = pipeline.render(pipeline.steps(LINES))
    assert "flowchart LR" in text
    assert "s0 --> s1" in text
    assert ":::fail" in text
    assert "| 2 | verify unit | falló | 180 |" in text

def test_pipeline_needs_the_log(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(pipeline, "LOG", tmp_path / "activity.jsonl")
    assert pipeline.main() == 1
    assert "corre primero /factory" in capsys.readouterr().out

def test_pipeline_writes_the_markdown(tmp_path, monkeypatch):
    log = tmp_path / "activity.jsonl"
    log.write_text("\n".join(LINES), encoding="utf-8")
    monkeypatch.setattr(pipeline, "LOG", log)
    monkeypatch.setattr(pipeline, "ROOT", tmp_path)
    monkeypatch.setattr(pipeline, "PIPELINE", tmp_path / "pipeline.md")
    assert pipeline.main() == 0
    assert "verify unit" in (tmp_path / "pipeline.md").read_text(encoding="utf-8")
```

**Escribe** `tests/test_qa.py`

```python
"""Pruebas de la revisión automática de QA.md sobre el producto."""

import subprocess

from verification import qa

def make_product(root, files):
    for name, text in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return root

def test_a_clean_product_has_no_problems(tmp_path):
    product = make_product(tmp_path, {"README.md": "# HR", "doc/adr/0001.md": "x"})
    assert not qa.problems(product)

def test_emojis_loose_markdown_and_missing_readme_are_reported(tmp_path):
    files = {"app/x.py": "# listo " + chr(0x2705), "NOTES.md": "x"}
    product = make_product(tmp_path, files)
    assert qa.problems(product) == [
        "NOTES.md debe ir en doc/", "emoji en app/x.py", "falta README.md",
    ]

def test_qa_fails_when_pylint_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(qa, "PRODUCT", make_product(tmp_path, {"README.md": "# HR"}))
    monkeypatch.setattr(
        qa.subprocess, "run", lambda *a, **k: subprocess.CompletedProcess(a, 1)
    )
    assert qa.main() == 1
```

**Ejecuta**

**Todos los sistemas**

```bash
uv run python scripts/verify.py
```

**Observa:** las tres líneas de QA en `[OK]`.

### Paso 8 · Corre la fábrica (25 min)

**Ejecuta** (en la carpeta de la sesión)

**Todos los sistemas**

```bash
claude
```

**Dentro de Claude Code**

```text
/factory
```

**Observa:** aprueba el plan. Mientras trabaja, abre `output/activity.jsonl` en tu editor: crece con cada herramienta.

**Cuatro líneas de la bitácora**

```text
{"ts": "2026-11-05T04:38:33+00:00", "agent": "architect", "tool": "Read", "target": "product/app/main.py", "ok": true}
{"ts": "2026-11-05T04:38:34+00:00", "agent": "architect", "tool": "Read", "target": "product/app/agent.py", "ok": true}
{"ts": "2026-11-05T04:38:34+00:00", "agent": "architect", "tool": "Read", "target": "product/app/config.py", "ok": true}
{"ts": "2026-11-05T04:38:35+00:00", "agent": "architect", "tool": "Read", "target": "product/app/llm.py", "ok": true}
```

### Paso 9 · Rastrea una petición y mira el pipeline (20 min)

**Ejecuta**

**Todos los sistemas**

```bash
uv run python -m verification qa
```

**Observa**

```text
[OK] qa
```

**Ejecuta**

**Todos los sistemas**

```bash
cd product
uv run uvicorn app.main:app
```

**Observa:** pregunta algo en http://127.0.0.1:8000, copia el `request_id` que muestra la página y búscalo en la terminal. Luego abre /metrics.

**Las líneas de una petición con X-Request-ID: demo-123**

```text
{"ts": "2026-11-05T04:52:07.427242+00:00", "service": "hr-assistant", "event": "audit", "request_id": "demo-123", "action": "tool_call", "tool": "get_employee", "args": {"employee_id": "EMP-0004"}}
{"ts": "2026-11-05T04:52:07.427307+00:00", "service": "hr-assistant", "event": "agent_run", "request_id": "demo-123", "question_chars": 19, "history_messages": 0, "steps": 2, "tools": ["get_employee"], "input_tokens": 29, "output_tokens": 23, "stopped": "answer"}
{"ts": "2026-11-05T04:52:07.427547+00:00", "service": "hr-assistant", "event": "request", "request_id": "demo-123", "method": "POST", "path": "/ask", "status": 200, "latency_ms": 0.88}
```

**/metrics**

```text
{"pid":24175,"requests":2,"error_rate":0.0,"latency_ms":{"p50":0.798,"p95":0.88},"tokens":
{"input":29,"output":23},"slo":{"p95_ms_target":2000,"met":true}}
```

**Ejecuta**

**Todos los sistemas**

```bash
uv run python scripts/pipeline.py
```

**La tabla de output/pipeline.md**

```text
| # | Paso | Resultado | Segundos |
| --- | --- | --- | --- |
| 1 | architect | pasó | 122 |
| 2 | qa-unit | pasó | 602 |
| 3 | verify unit | falló | 2 |
| 4 | observability | pasó | 316 |
| 5 | verify unit | falló | 3 |
| 6 | qa-unit | pasó | 54 |
| 7 | verify unit | pasó | 3 |
| 8 | verify contract | pasó | 1 |
| 9 | verify qa | pasó | 3 |
| 10 | qa-style | pasó | 44 |
```

**Observa:** el primer `verify unit` falla: es el rojo esperado de TDD. Abre `output/pipeline.md` con la vista previa de Markdown para ver el diagrama.

### Paso 10 · README y commit (10 min)

**Reemplaza (versión nueva completa)** `README.md`

````markdown
# Sesión 2 · Observabilidad (la fábrica la agrega y se observa a sí misma)

La fábrica toma el producto de la sesión 1 y le agrega lo necesario para responder «¿qué pasó con la petición X?»:
`request_id`, log JSON, auditoría, `/metrics` con SLO y trazas en LangSmith. Además, la fábrica **se observa a sí
misma**: cada herramienta de cada agente queda en una bitácora, y con ella se dibuja el pipeline de la corrida.

| Paso | Quién | Patrón |
| --- | --- | --- |
| Plan | `architect` y tú lo apruebas | Humano en el lazo |
| Pruebas primero | `qa-unit` | |
| Código | `observability` | |
| unit → contract → qa | El código decide; al primer fallo se corrige (máximo 2) | **Flujo**: encadenamiento con compuertas |
| Revisión contra QA.md | `qa-style` devuelve APROBADO o CAMBIOS (máximo 2 vueltas) | **Flujo**: evaluador-optimizador |
| Pipeline y reporte | `scripts/pipeline.py` con la bitácora | |

Hooks: `hooks/permissions.py` (cada agente escribe solo en sus carpetas) y `hooks/activity_log.py`, nuevo, que
escribe una línea en `output/activity.jsonl` por cada herramienta.

## Preparar

Copia el producto que construiste en la sesión 1.

macOS / Linux:

```bash
cd NextGenCode-M4-Agentes/sesion02
cp -R ../sesion01/product product
uv venv --python 3.12
uv pip install -r requirements.txt
uv run python scripts/verify.py
```

Windows (PowerShell):

```powershell
cd NextGenCode-M4-Agentes\sesion02
Copy-Item -Recurse ..\sesion01\product product
uv venv --python 3.12
uv pip install -r requirements.txt
uv run python scripts/verify.py
```

## Correr la fábrica

La primera vez que abres `claude` en esta carpeta te pregunta **«Do you trust the files in this folder?»**:
responde que sí. Sin esa confianza, Claude Code ignora los permisos de `.claude/settings.json` y los agentes no pueden
correr las verificaciones.

Ejecuta `claude` y, dentro, escribe `/factory`. Al terminar tendrás tres archivos:
- `output/report.md`: el estado.
- `output/qa-review.md`: la revisión de QA.
- `output/pipeline.md`: el diagrama del pipeline. Ábrelo en GitHub o en la vista previa de Markdown de tu editor.

## Comprobar

```bash
uv run python -m verification unit
uv run python -m verification contract
uv run python -m verification qa
cd product
uv run uvicorn app.main:app
```

Abre http://127.0.0.1:8000. Pregunta algo, copia el `request_id` que muestra la página y búscalo en el log de la
terminal. Luego abre http://127.0.0.1:8000/metrics.
````

**Ejecuta**

**Todos los sistemas**

```bash
git add -A
git commit -m "Sesion 2: observability, qa-style, verificacion de QA y bitacora de la fabrica"
```

**Observa:** `product/` y `output/` no entran al commit: están en `.gitignore`. Versionas la fábrica; el producto se reconstruye corriéndola.

## Estructura final de la carpeta

```text
sesion02/
  .claude/agents/architect.md
  .claude/agents/developer.md
  .claude/agents/observability.md
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
  scripts/pipeline.py
  scripts/verify.py
  spec/01-architecture.md
  spec/02-observability.md
  spec/employees.json
  tests/__init__.py
  tests/test_activity_log.py
  tests/test_permissions.py
  tests/test_qa.py
  tests/test_verification.py
  verification/__init__.py
  verification/__main__.py
  verification/contract/conftest.py
  verification/contract/test_contract.py
  verification/contract/test_contract_02.py
  verification/qa.py
  product/   (lo genera la fábrica)
  output/    (plan, reporte, bitácora)
```

## Resumen de los pasos

| Paso | Qué se construye | Llama al modelo | Tiempo |
|---|---|---|---|
| 0 | Copia la sesión 1 | No | 10 min |
| 1 | La especificación de observabilidad | No | 10 min |
| 2 | Dos agentes: uno construye, otro revisa | No | 15 min |
| 3 | La verificación de QA.md | No | 15 min |
| 4 | El hook de bitácora | No | 15 min |
| 5 | El pipeline de la fábrica | No | 10 min |
| 6 | El orquestador, versión 2 | No | 10 min |
| 7 | Las pruebas de las piezas nuevas | No | 10 min |
| 8 | Corre la fábrica | Sí | 25 min |
| 9 | Rastrea una petición y mira el pipeline | No | 20 min |
| 10 | README y commit | No | 10 min |

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
