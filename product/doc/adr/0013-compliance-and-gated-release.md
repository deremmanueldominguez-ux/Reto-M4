# ADR 0013: Compliance al arrancar y publicación solo con compuertas

Estado: propuesto

## Contexto

Una mala configuración en producción (modelo simulado, claves cortas, trazas con texto
de preguntas) no debe llegar a servir peticiones, y nadie debe revisarla a mano. Tampoco
debe publicarse código que no pasó las pruebas.

## Decisión

`app/compliance.py` tiene `check_production(settings)`, que `create_app` llama antes de
armar nada. Con `ENVIRONMENT=production` lanza `ConfigError` si `MODEL_PROVIDER=fake`, si
`API_KEYS` está vacía o alguna clave mide menos de 16, o si `LANGSMITH_TRACING=true` y
`HIDE_INPUTS` o `HIDE_OUTPUTS` no valen `true`. Se usa la petición de trazas, no si hay
clave de LangSmith: es la regla más estricta. Cada regla figura en
`doc/compliance-checklist.md` con su prueba. La publicación tiene tres compuertas: una
persona aprueba, el CI pasa (`style`, `unit`, `e2e`, `docker`) y Render despliega solo con
`autoDeployTrigger: checksPass`; después corre la prueba de humo.

## Consecuencias

- Una configuración insegura hace fallar el arranque: Render no ve `/health` y no cambia
  la versión que ya servía.
- Desarrollo no cambia: las reglas solo aplican con `ENVIRONMENT=production`.
- `ENVIRONMENT` con otro valor impide arrancar, para que un error de dedo no apague las
  reglas.
- Los secretos se escriben en Render (`sync: false`), nunca en el repositorio.
