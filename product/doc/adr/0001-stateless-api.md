# ADR 0001: API sin estado con historial en el cliente

Estado: propuesto

## Contexto

El personal de RH conversa con el asistente desde una página web. La API debe escalar
corriendo más copias detrás de un balanceador, sin sesiones pegajosas ni base de datos.

## Decisión

La API no guarda nada entre peticiones. El navegador conserva el historial y lo envía en
cada `POST /ask` como `history`. Los datos de empleados se cargan una vez al arrancar y
son de solo lectura. `GET /health` expone el `pid` para comprobar qué copia respondió.

## Consecuencias

- Cualquier copia puede atender cualquier petición; escalar es sumar procesos.
- El cliente controla el historial: la API lo valida (roles y largo de la pregunta) y no
  confía en él más allá de usarlo como contexto.
- Las peticiones crecen con la conversación; si hace falta, se limitará el historial.
- Recargar la página pierde la conversación, lo cual es aceptable en esta sesión.
