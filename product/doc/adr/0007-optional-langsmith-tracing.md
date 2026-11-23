# ADR 0007: Trazas opcionales con LangSmith detrás de un adaptador

Estado: propuesto

## Contexto

Se quieren trazas de cada corrida del agente, llamada al modelo y herramienta, pero el
producto debe funcionar igual sin clave, sin red en las pruebas y sin enviar datos
personales por omisión.

## Decisión

Un adaptador `Tracer` (`app/tracing.py`) decide según `Settings`: se enciende solo con
`LANGSMITH_TRACING=true` y `LANGSMITH_API_KEY` presente. Apagado, `wrap` devuelve la
misma función y `langsmith` ni se importa. Encendido, crea un `langsmith.Client` con
`hide_inputs`/`hide_outputs` según `HIDE_INPUTS`/`HIDE_OUTPUTS` (por omisión `true`) y
envuelve con `traceable` el agente, `complete` y cada herramienta, con el `request_id`
en `metadata`. El agente y el modelo no importan `langsmith`. La clave no se guarda en
`Settings` ni se registra.

## Consecuencias

- Sin clave no hay costo, red ni riesgo de fuga; las pruebas no la necesitan.
- Cambiar de proveedor de trazas toca un solo módulo.
- Con entradas y salidas ocultas, las trazas muestran estructura y tiempos, no texto.
- `langsmith` entra en `requirements.txt` aunque casi nunca se cargue.
