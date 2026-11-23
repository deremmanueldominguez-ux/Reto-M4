# ADR 0003: Un solo agente con bucle con tope y protocolo JSON

Estado: propuesto

## Contexto

El agente consulta herramientas de solo lectura antes de responder. Un modelo puede pedir
herramientas sin fin o devolver texto mal formado; hay que acotar costo y latencia.

## Decisión

Un solo agente con dos herramientas (`get_employee`, `search_by_department`). En cada
vuelta el modelo devuelve un único objeto JSON: `{"tool", "args"}` o `{"answer"}`. El
resultado de la herramienta vuelve como mensaje `user` que empieza con
`Resultado de la herramienta: `. `steps` cuenta llamadas al modelo. Al llegar a
`AGENT_MAX_STEPS` sin respuesta se devuelve exactamente
`No pude completar la respuesta. Intenta con una pregunta más concreta.` Un JSON
inválido o una herramienta desconocida se informan al modelo y consumen una vuelta.

## Consecuencias

- El costo por pregunta está acotado por configuración.
- El protocolo es simple de probar y de implementar en otros proveedores.
- Preguntas que necesiten muchas herramientas pueden toparse con el límite; se ajusta con
  `AGENT_MAX_STEPS`, nunca quitando el tope.
