# Controles de seguridad

El sistema aplica 22 controles en cuatro capas: acceso a la API, manejo de secretos,
protección de datos en logs y trazas, y publicación. El detalle de cada regla de arranque,
con su prueba, está en
[product/doc/compliance-checklist.md](../product/doc/compliance-checklist.md).

## Acceso y uso de la API

| Control | Cómo funciona | Justificación |
| --- | --- | --- |
| Clave por cliente | `POST /ask` y `GET /metrics` exigen `X-API-Key`; sin ella o inválida, `401`. Desde ahí solo viaja el nombre del cliente | Saber quién pregunta y poder revocar a un cliente sin afectar a los demás |
| Comparación en tiempo constante | Las claves se comparan con `hmac.compare_digest` contra todas | Evita adivinar una clave midiendo cuánto tarda la respuesta |
| Límite de peticiones | 30 por cliente por minuto (`RATE_LIMIT_PER_MINUTE`); si se pasa, `429` con `Retry-After` | Frena abusos y gasto descontrolado del modelo |
| Validación de entrada | Pregunta no vacía y de hasta 2000 caracteres; historial con roles `user` o `assistant`; si no, `422` | Rechaza entradas malformadas antes de gastar tokens |
| Agente acotado | Herramientas de solo lectura, tope de 3 llamadas al modelo y protocolo JSON; una herramienta desconocida no se ejecuta | Aunque el modelo reciba instrucciones maliciosas, no puede modificar datos ni quedar en un ciclo |
| Errores sin detalles | Un fallo da `500 internal error` o `502 model unavailable` con el id de petición, sin mensaje ni stack trace | No revela rutas, versiones ni datos internos |
| Página sin inyección de HTML | La respuesta se escribe como texto (`textContent`), nunca como HTML | Un texto con etiquetas no puede ejecutar código en el navegador |
| Clave en `sessionStorage` | La página guarda la clave solo durante la sesión de la pestaña | Se borra al cerrar la pestaña |

## Secretos

| Control | Cómo funciona | Justificación |
| --- | --- | --- |
| Secretos solo en el entorno | `API_KEYS`, `CF_API_TOKEN` y `LANGSMITH_API_KEY` vienen de variables de entorno; en Render, de **Environment** (`sync: false` en `render.yaml`) | El repositorio no guarda ningún valor secreto |
| `.env` fuera de git y de la imagen | `.gitignore` y `.dockerignore` excluyen `.env`; solo se sube `.env.example`, vacío | Un secreto no puede llegar al repositorio ni al contenedor |
| CI sin secretos | El CI usa el modelo simulado y una clave de ejemplo marcada como no secreta | Una fuga del CI no expone nada real |
| Secretos ocultos en memoria | `repr=False` en la configuración; el token de Cloudflare solo viaja en el encabezado `Authorization` | Imprimir la configuración no muestra claves |
| Errores de configuración sin valores | Si `API_KEYS` está mal formada, el error dice el número de entrada y su largo, nunca el valor | El mensaje de error se puede compartir sin riesgo |

## Logs, trazas y datos

| Control | Cómo funciona | Justificación |
| --- | --- | --- |
| Redactor central | Todo evento del log pasa por un filtro que tapa campos con nombres sensibles, los valores de los secretos configurados y cualquier `Bearer ...` | Una credencial no llega al log aunque un evento la traiga por error |
| Sin texto de las personas en el log | El log guarda conteos, tiempos y herramientas, nunca la pregunta ni la respuesta | Las preguntas pueden contener datos personales |
| Trazas con texto oculto | En LangSmith, `HIDE_INPUTS` y `HIDE_OUTPUTS` valen `true` por omisión y son obligatorios en producción | El servicio externo ve la estructura y los tiempos, no el contenido |
| Librerías HTTP calladas | Los logs de `httpx` y `httpcore` se quedan en `WARNING` | En `DEBUG` imprimen encabezados, incluido el token |
| Auditoría por petición | Cada herramienta usada deja un evento `audit` con el cliente y el id de petición | Se puede reconstruir qué consultó cada cliente |

## Producción y publicación

| Control | Cómo funciona | Justificación |
| --- | --- | --- |
| Compliance como código | Con `ENVIRONMENT=production` el servicio no arranca con el modelo simulado, sin claves, con claves de menos de 16 caracteres, con trazas sin ocultar texto o con `LOG_LEVEL=debug` | Una configuración insegura nunca atiende peticiones |
| Contenedor sin privilegios | Imagen `python:3.12-slim` que corre con un usuario sin privilegios de administrador | Limita el daño si alguien compromete el proceso |
| Publicación con compuertas | Render despliega solo si pasan `style`, `unit`, `e2e` y `docker`, y si `/health` responde | Código roto o con estilo fuera de norma no llega a producción |
| Aprobación humana y permisos de la fábrica | Ningún agente publica sin `output/approved.txt`, que solo existe si una persona aprobó; cada agente escribe solo en sus carpetas; nadie lee `.env` | Un agente no puede publicar, leer secretos ni tocar el trabajo de otro por su cuenta |

## Cómo se comprueba

- `uv run python -m verification unit` incluye una prueba "canario": configura secretos
  falsos con valores únicos, provoca una respuesta correcta, una clave inválida, un `500` y
  un `502`, y falla si alguno de esos valores aparece en el log.
- `uv run python -m verification contract` prueba las rutas protegidas y las reglas de
  arranque contra el servidor real.
- La prueba de humo de producción confirma que `/ask` sin clave responde `401`.

## Riesgos conocidos

- **Límite por copia:** el límite de peticiones vive en la memoria de cada proceso; con
  varias copias, el límite real se multiplica. Render gratuito corre una sola.
- **Fuerza bruta:** un `401` no consume el límite. Se mitiga con claves largas.
- **Historial sin tope:** el número de turnos y el largo de cada uno no se limitan; solo se
  recortan antes de llegar al modelo.
- **Datos personales en auditoría:** una búsqueda por nombre deja ese nombre en el evento
  `audit`. El redactor detecta credenciales, no datos personales.
- **Sin escáner de secretos en el CI:** hoy lo cubre la protección de push de GitHub y la
  revisión de `qa-style`.
