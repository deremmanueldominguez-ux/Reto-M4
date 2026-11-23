# ADR 0009: Enrutamiento por regla y ventana de historial

Estado: propuesto

## Contexto

La mayoría de las preguntas son simples (un id o un departamento) y no necesitan el
modelo grande; y el historial que manda el cliente crece con la conversación y encarece
cada llamada. Las palancas deben ser deterministas, baratas y medibles.

## Decisión

`app/router.py` decide con una regla en código, no con otro modelo:
`route(question, settings) -> Route(model, reason)`. Elige `MODEL_LARGE` si
`ROUTING=false` (`routing_off`), si `len(question) > ROUTER_MAX_CHARS`
(`long_question`) o si el texto normalizado (minúsculas, sin tildes) contiene «compara»,
«resume», «explica», «por que», «analiza» o «todos» (`keyword:<palabra>`); si no,
`MODEL_SMALL` (`short_question`). `apply_window(history, n)` deja los últimos `n`
mensajes del historial del cliente (con `n = 0`, ninguno); nunca recorta la pregunta ni
los mensajes del bucle actual. La decisión se toma una vez por pregunta.

## Consecuencias

- El motivo (`route`) va en la respuesta y en `agent_run`, así se audita cada decisión.
- La regla «contiene» puede mandar al modelo grande preguntas simples: cuesta más, no
  empeora la calidad.
- Una ventana corta puede perder contexto de turnos viejos; `verification evaluate`
  comprueba que la calidad no baje.
