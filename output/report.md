# Reporte de la fábrica: spec/05-debug.md

**Estado: DETENIDA POR LA PERSONA.** El producto está listo y verificado en local; la persona decidió no
publicar todavía. No existe `output/approved.txt` y no se corrió `scripts/publish.py`.

- URL pública: ninguna nueva (Render sigue con la versión de la sesión 4).
- Correcciones de compuertas: 0 (pasaron a la primera tras la implementación).
- Vueltas de qa-style: 1, con APROBADO. Dos observaciones menores de documentos, corregidas después.
- Ciclos de triage: 0 (no hubo publicación ni prueba de humo).

## Compuertas

| Paso | Resultado |
| --- | --- |
| `unit` | OK, 178 pruebas, cobertura 97.94 % |
| `contract` | OK, 22 pruebas |
| `qa` | OK, pylint 10.00/10 (también tras corregir los documentos) |
| `e2e` | OK, 5 pruebas |
| `evaluate` | OK |

## Evaluate

| Variante | Calidad | Costo USD | Tokens de entrada |
| --- | --- | --- | --- |
| baseline | 100 % | 0.001163 | 2507 |
| levers | 100 % | 0.000160 | 1937 |

## Bitácora

1. La persona aprobó `spec/05-debug.md`.
2. `architect` escribió `output/plan.md`, el ADR 0014 y actualizó `product/doc/architecture.md`.
3. La persona aprobó el plan y decidió que `startup` lleve un campo `credentials` (sin excepción en el
   redactor); `architect` lo registró.
4. `qa-unit` escribió las pruebas. Se instalaron las dependencias de `requirements.txt` en el entorno
   (faltaban pytest y pylint). `unit` en rojo: solo fallaban las pruebas nuevas.
5. `observability` implementó los puntos 1 a 6 (redactor, `LOG_LEVEL`, eventos de debug, `frames`,
   loggers de terceros en `WARNING`) y documentó el README.
6. En paralelo: `security` implementó el punto 7 (debug prohibido en producción) y el checklist;
   `qa-unit` corrigió un aviso de pylint en `tests/test_events.py`.
7. Compuertas `unit`, `contract`, `qa`, `e2e` (con Chromium instalado) y `evaluate`: todas OK.
8. `qa-style`: APROBADO.
9. Observaciones menores: `observability` corrigió el README y `architect` el checklist; `qa` OK.
10. La persona probó en local: el log en debug salió limpio (sin canarios, sin `Bearer`, sin la
    pregunta) y producción con debug no arranca.
11. La persona pidió no publicar todavía.

Pipeline: [output/pipeline.md](pipeline.md)

## Para publicar después

Responder «si» a la aprobación de publicar en una nueva corrida (o pedirlo al orquestador): se escribe
`output/approved.txt`, se corre `scripts/publish.py <repositorio>` y luego la prueba de humo
`uv run python -m verification production <url>`. En Render no hay secretos nuevos; no definir
`LOG_LEVEL=debug` allí.
