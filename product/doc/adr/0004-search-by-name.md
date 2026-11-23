# ADR 0004: Búsqueda por nombre como tercera herramienta

Estado: propuesto (pendiente de aprobación de una persona)

## Contexto

El personal de RH pide buscar empleados por nombre, no solo por id o departamento. El
comportamiento ya aprobado (dos herramientas, cuatro reglas del modelo simulado, texto de
ayuda literal) y el contrato de `verification/contract/` no deben cambiar.

## Decisión

Se agrega `search_by_name(name)` en `EmployeeDirectory`, de solo lectura: búsqueda
parcial (subcadena) sobre el nombre completo, sin distinguir mayúsculas ni tildes
(`normalize_text`). Sin coincidencias devuelve `{"error": "No hay empleados cuyo nombre
contenga <name>."}`; con menos de 2 caracteres devuelve un error. El agente la registra
como tercera herramienta. El `FakeModel` recibe los nombres por constructor (opcional) y
gana una regla nueva en cuarto lugar: después de id y departamento, antes de la ayuda.
La regla compara palabras completas de 3 letras o más, no subcadenas.

## Consecuencias

- Toda pregunta que hoy llega a una herramienta sigue llegando a la misma; solo cambian
  preguntas que hoy reciben la ayuda y mencionan un nombre.
- Si una pregunta menciona departamento y nombre, gana el departamento.
- La herramienta es más permisiva (parcial) que la regla del simulado (palabra completa);
  un modelo real puede aprovechar la búsqueda parcial.
- `spec/01-architecture.md` queda desactualizada hasta que una persona la actualice.
- Sube `input_tokens` porque el mensaje `system` describe una herramienta más.
