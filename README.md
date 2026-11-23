# Reto M4: fábrica de agentes y HR Assistant

Este repositorio contiene dos cosas:

- **El HR Assistant** (`product/`): un asistente de Recursos Humanos que responde en español
  preguntas sobre los empleados de la empresa. Es una API web sin estado (FastAPI) con un
  agente de IA que usa herramientas de solo lectura sobre el directorio, una página web de
  chat y un modelo real en Cloudflare Workers AI.
- **La fábrica de agentes** que lo construyó: diez agentes de Claude Code (architect,
  qa-unit, developer, observability, costs, qa-e2e, qa-style, security, deploy y triage)
  que trabajan a partir de la especificación de `spec/`, con aprobación humana del plan y
  de cada publicación, y con verificaciones en código que deciden si un paso terminó bien.

El código que se despliega vive en el repositorio privado `hr-assistant`. La carpeta
`product/` de este repositorio es una copia de ese código en el momento de la entrega.

## Demo

GitHub no permite embeber este video (pesa 220 MB), así que está adjunto al release
[v1.0-entrega](https://github.com/deremmanueldominguez-ux/Reto-M4/releases/tag/v1.0-entrega).

**Ver el video:** [demo-reto-m4.mp4](https://github.com/deremmanueldominguez-ux/Reto-M4/releases/download/v1.0-entrega/demo-reto-m4.mp4)

## Documentación de la entrega

| Documento | Contenido |
| --- | --- |
| [docs/arquitectura.md](docs/arquitectura.md) | Diagrama de arquitectura, flujo entre componentes y decisiones clave |
| [docs/costos.md](docs/costos.md) | Modelo de costos, optimizaciones aplicadas y resultados medidos |
| [docs/seguridad.md](docs/seguridad.md) | Controles de seguridad implementados y su justificación |
| [product/README.md](product/README.md) | Referencia completa del producto: rutas, variables y pruebas |
| [product/doc/adr/](product/doc/adr/) | Las 14 decisiones de arquitectura (ADR) |

## Estructura

| Carpeta | Qué contiene |
| --- | --- |
| `product/` | El HR Assistant: `app/`, pruebas, `Dockerfile`, CI y `render.yaml` |
| `spec/` | La especificación por sesión (arquitectura, observabilidad, costos, producción, debug) |
| `.claude/` | Los agentes, la skill `/factory` y los permisos de la fábrica |
| `hooks/` | Permisos por agente y bitácora de cada herramienta |
| `verification/` | Las compuertas: `unit`, `contract`, `qa`, `e2e`, `evaluate` y `production` |
| `scripts/` | Publicación con aprobación, dibujo del pipeline y lista de QA de la fábrica |
| `output/` | Evidencia de la última corrida: plan, revisión de QA, reporte y bitácora |

## Requisitos previos

- Python 3.12 y git.
- [uv](https://docs.astral.sh/uv/) para el entorno de la fábrica (o pip para el producto solo).
- Chromium de Playwright, solo para las pruebas de punta a punta.
- Docker, solo para construir la imagen en local.
- Opcionales: cuenta de Cloudflare (Workers AI y AI Gateway) para el modelo real, LangSmith
  para trazas, GitHub y Render para publicar, y Claude Code para correr la fábrica.

Sin ninguna cuenta, el producto funciona con un modelo simulado.

## Instalación

```bash
git clone https://github.com/deremmanueldominguez-ux/Reto-M4.git
cd Reto-M4
uv venv --python 3.12
uv pip install -r requirements.txt -r product/requirements.txt
uv run playwright install chromium
```

El primer archivo instala la fábrica y sus pruebas; el segundo, las dependencias del producto
(incluida `python-dotenv`, que necesita `--env-file`).

## Ejecutar el producto en local

Desde `product/`. Con el modelo simulado no hace falta red ni cuenta.

Windows (PowerShell):

```powershell
cd product
$env:API_KEYS = "local:una-clave-de-16-o-mas"
uv run uvicorn app.main:app --no-access-log
```

macOS / Linux:

```bash
cd product
export API_KEYS="local:una-clave-de-16-o-mas"
uv run uvicorn app.main:app --no-access-log
```

Abre `http://127.0.0.1:8000/`, escribe `una-clave-de-16-o-mas` en «Clave de acceso» y
pregunta «¿Quién es EMP-0004?». Otras rutas: `GET /health`, `GET /metrics` (con clave) y
`GET /docs` (documentación interactiva).

**Con el modelo real:** copia `product/.env.example` a `product/.env`, pon
`MODEL_PROVIDER=gateway` y completa `CF_ACCOUNT_ID`, `CF_GATEWAY_ID`, `CF_API_TOKEN` y
`API_KEYS`. Arranca con `uv run uvicorn app.main:app --no-access-log --env-file .env`.
`.env` está en `.gitignore`: nunca lo subas.

**Modo debug:** `LOG_LEVEL=debug` agrega eventos de diagnóstico al log sin mostrar
credenciales. Está prohibido en producción.

## Verificar

Desde la raíz del repositorio:

```bash
uv run python -m verification unit       # pruebas y cobertura de 80 % o más
uv run python -m verification contract   # contrato HTTP contra el servidor real
uv run python -m verification qa         # estilo (pylint) y reglas de QA.md
uv run python -m verification e2e        # Playwright sobre la página
uv run python -m verification evaluate   # costo y calidad contra la línea base
uv run python scripts/verify.py          # pruebas de la propia fábrica
```

## Desplegar

El despliegue pasa por GitHub Actions y Render. La fábrica lo hace con aprobación humana;
también se puede hacer a mano.

1. **Publicar el código del producto** en un repositorio propio. Con la fábrica: abre
   `claude` en la raíz, ejecuta `/factory hr-assistant` y responde «si» cuando pregunte si
   publica. A mano: sube el contenido de `product/` a un repositorio nuevo.
2. **CI:** cada push corre cuatro etapas en GitHub Actions: `style` (pylint),
   `unit` (cobertura de 80 % o más), `e2e` (Playwright con el modelo simulado) y `docker`
   (la imagen se construye y responde en `/health`).
3. **Render:** en **New > Blueprint**, conecta el repositorio. `render.yaml` crea el
   servicio con Docker, `ENVIRONMENT=production`, el modelo real y `healthCheckPath: /health`.
   Render despliega solo cuando el CI pasa.
4. **Secretos en Render > Environment** (nunca en el código ni en un chat):
   - `API_KEYS`, con la forma `cliente:clave` y claves de 16 caracteres o más.
   - `CF_ACCOUNT_ID` y `CF_API_TOKEN`.
   - `LANGSMITH_API_KEY`, solo si enciendes las trazas.
5. **Prueba de humo**, cuando el servicio esté *Live*:

   ```powershell
   $env:SMOKE_API_KEY = "<tu clave de cliente>"
   uv run python -m verification production https://<tu-servicio>.onrender.com
   ```

   Comprueba que `/health` responde `200`, que `/ask` sin clave da `401` y que con clave
   da `200`. Si falla, el agente `triage` dice quién lo corrige.

Con `ENVIRONMENT=production` el servicio se niega a arrancar si la configuración es
insegura: modelo simulado, sin claves, claves cortas, trazas sin ocultar texto o modo debug.
El plan gratuito de Render apaga el servicio tras unos minutos sin uso; la primera petición
puede tardar cerca de un minuto.
