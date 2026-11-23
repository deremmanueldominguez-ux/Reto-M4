# ADR 0012: Límite de peticiones por cliente en memoria del proceso

Estado: propuesto

## Contexto

Un cliente no debe gastar toda la cuota del modelo. El límite es
`RATE_LIMIT_PER_MINUTE` por cliente, con `429` y `Retry-After`. Las pruebas deben ser
deterministas, y la API es sin estado (ADR 0001): no hay base de datos ni caché compartida.

## Decisión

`app/rate_limit.py` tiene un `RateLimiter` con una ventana deslizante de 60 segundos por
cliente: guarda las marcas de `clock.monotonic()` del reloj inyectado y descarta las
viejas. Si ya hay `RATE_LIMIT_PER_MINUTE` marcas, responde `429 {"detail": "rate limit
exceeded"}` con `Retry-After` igual a los segundos que faltan para liberar la más vieja,
redondeados hacia arriba y nunca menos de 1. Es una dependencia que corre después de la
clave, con un candado para los hilos de uvicorn.

## Consecuencias

- Con el reloj falso, las pruebas avanzan el tiempo sin esperar.
- La memoria tiene tope: un cliente por entrada de `API_KEYS`, como máximo el límite de
  marcas cada uno.
- Como las métricas (ADR 0006), el estado es de cada proceso: con N copias el límite real
  es N veces mayor. En Render `free` hay una sola instancia; para escalar haría falta un
  almacén compartido.
- Las peticiones con `401` no consumen límite.
