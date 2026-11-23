# ADR 0011: Clave por cliente como dependencia de ruta

Estado: propuesto

## Contexto

El producto se publica en Internet. `POST /ask` gasta cuota del modelo y `GET /metrics`
expone datos del proceso: deben pedir clave. `GET /`, `/health` y `/docs` no. El log, la
auditoría y las trazas deben decir qué cliente preguntó, sin escribir nunca su clave.

## Decisión

`API_KEYS` (`cliente:clave,...`) se lee al arrancar con `auth.parse_api_keys`; si una
entrada está mal formada, `ConfigError` con su número y su largo, nunca su valor. Las
claves viven en `Settings.api_keys` con `repr=False`. Una dependencia FastAPI declarada
solo en `/ask` y `/metrics` lee `X-API-Key`, la compara con cada clave con
`hmac.compare_digest` y fija `request.state.client`; si falla, `401 {"detail":
"invalid or missing API key"}`. Va dentro del middleware de observabilidad, así el `401`
también lleva `X-Request-ID` y su evento `request`. `events` y `tracing` reciben solo el
nombre del cliente con `bind(request_id, client)`.

## Consecuencias

- Las rutas abiertas quedan explícitas: no hay lista de excepciones en un middleware.
- La clave no pasa de la dependencia: nada más en el código la ve.
- Sin `API_KEYS` en desarrollo, `/ask` responde `401`; las pruebas inyectan una clave.
- Cambiar claves exige reiniciar: no hay rotación en caliente.
