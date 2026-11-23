# ADR 0005: Id por petición y eventos JSON con reloj inyectado

Estado: propuesto

## Contexto

Hay que responder "qué pasó con la petición X" con datos, en varias copias del proceso,
sin guardar el texto de preguntas ni respuestas y con pruebas deterministas.

## Decisión

Un middleware asigna a cada petición un `request_id` (el `X-Request-ID` del cliente si
es válido: 1 a 128 caracteres de `[A-Za-z0-9._:-]`; si no, un UUID4) y lo devuelve en el
encabezado de toda respuesta y en el cuerpo de `POST /ask`. El id se pasa
explícitamente (`request.state` y un `RequestLog` inyectado al agente), sin variables
globales. Cada evento (`request`, `agent_run`, `audit`, `error`) es una línea JSON en la
salida estándar con `ts`, `service`, `event` y `request_id`. La hora y la latencia salen
de un `Clock` inyectado; `SystemClock` es el único que toca el reloj del sistema.
`agent_run` lleva solo conteos y `error` solo el tipo de la excepción.

## Consecuencias

- Basta filtrar el log por `request_id` para reconstruir una petición en cualquier copia.
- Las pruebas fijan el `ts` y la latencia con un reloj falso.
- El log no sirve para leer conversaciones; depurar un caso exige reproducirlo.
- El log de acceso de uvicorn no es JSON; se recomienda `--no-access-log`.
