donde encuentro la documentación de la API REST (OpenAI o Swagger) utilizada en este proyecto?

No hay un archivo OpenAPI o Swagger guardado en el repositorio. La documentación la genera FastAPI cuando la aplicación está corriendo: product/app/main.py:197 crea FastAPI(title="HR Assistant") sin desactivar la documentación, así que quedan activas las rutas que FastAPI trae por defecto.

Cómo verla en local:

cd product
uvicorn app.main:app --no-access-log

Luego abre en el navegador:


| URL | Qué es |
| :--- | :--- |
| http://127.0.0.1:8000/docs | Swagger UI, donde puedes probar los endpoints |
| http://127.0.0.1:8000/redoc | ReDoc, una vista de solo lectura |
| http://127.0.0.1:8000/openapi.json | El esquema OpenAPI en JSON |



En producción (Render) las rutas son las mismas, con la URL del servicio en lugar de 127.0.0.1:8000.

Endpoints que vas a encontrar (definidos en product/app/main.py:299-314):
- GET /: la página web.
- GET /health: abierto, no pide clave.
- GET /metrics: pide clave de cliente y tiene límite de peticiones.
- POST /ask: pide clave de cliente y tiene límite de peticiones. Su respuesta usa el modelo AskResponse.

Para llamar a /ask o /metrics desde Swagger UI tienes que mandar la clave de cliente. Swagger no muestra un botón "Authorize" para esa clave, porque se valida en código y no está declarada en el esquema. La forma de enviarla está en product/README.md y en product/doc/adr/0011-api-key-per-client.md.

 estoy usando API REST?

Sí, en el sentido en que se usa habitualmente: el producto es una API HTTP que intercambia JSON, hecha con FastAPI. Si lo miras con rigor, se parece más a una API RPC sobre HTTP que a una API REST pura.

Lo que sí coincide con REST:
- Funciona sobre HTTP con métodos estándar (GET, POST) y códigos de estado con significado: 401 sin clave, 429 si te pasas del límite, 502 si falla el modelo.
- No guarda estado entre peticiones. Así lo decide el ADR product/doc/adr/0001-stateless-api.md: el historial de la conversación lo manda el cliente en cada llamada.
- Envía y recibe JSON, y el contrato queda descrito en OpenAPI (/openapi.json).


el sistema puede manejar múltiples requests concurrentes?

  Ran 3 shell commands

Sí, puede atender varias peticiones a la vez, pero con límites que conviene conocer. Lo revisé en el código de product/app/.

Cómo atiende varias peticiones a la vez

- Las rutas (ask, health, metrics, en app/main.py:299-314) están escritas con def normal, no con async def. Por eso FastAPI ejecuta cada una en un pool de hilos, que por defecto tiene unos 40. Mientras una petición a /ask espera la respuesta del modelo, las demás se siguen atendiendo.
- Cada petición crea su propio Agent (make_agent en main.py:176). Ninguna petición comparte el historial ni el estado de otra.
- Lo que sí se comparte está protegido con threading.Lock: las métricas (app/metrics.py:34), el límite de peticiones (app/rate_limit.py:38) y el log JSON (app/events.py:37). Ese estado no se corrompe aunque lleguen peticiones simultáneas.
- Todas las peticiones usan el mismo cliente HTTP hacia el gateway (httpx.Client), y ese cliente admite el uso desde varios hilos.

Límites

1. Hay un solo proceso. El Dockerfile arranca uvicorn sin --workers. Toda la concurrencia depende de esos ~40 hilos.
2. Cada /ask ocupa un hilo mucho tiempo. El agente hace hasta agent_max_steps llamadas al modelo, y cada una puede tardar hasta 30 s (GATEWAY_TIMEOUT_SECONDS en app/gateway.py:16). Si llegan más de ~40 preguntas lentas a la vez, las siguientes quedan en cola y la latencia crece.
3. El estado vive en memoria del proceso (los ADR 0006 y 0012 lo documentan así). Si un día escalas a varios procesos o instancias:
   - el límite por cliente se multiplica: con N procesos, un cliente puede hacer N veces su límite;
   - /metrics muestra solo los datos del proceso que respondió. Por eso devuelve el pid.

En resumen, la concurrencia alcanza para el uso del curso y para una instancia pequeña en Render. Para más carga habría dos caminos: subir el número de hilos, o pasar a varios workers moviendo el límite y las métricas a un almacén compartido, como Redis. Cualquiera de los dos es un cambio de arquitectura. Lo correcto sería pedírselo al architect para que lo incluya en el plan, y que no lo toque yo directamente en product/.

