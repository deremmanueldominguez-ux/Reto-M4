# ADR 0002: Modelo detrás de una interfaz y modelo simulado por omisión

Estado: propuesto

## Contexto

El agente debe poder cambiar de proveedor de modelo sin modificarse, y las pruebas deben
ser deterministas, sin red ni costo.

## Decisión

`llm.py` define el protocolo `LanguageModel` con un solo método
`complete(messages) -> Completion` (texto y tokens de entrada y salida). La única
implementación de esta sesión es `FakeModel` (`MODEL_PROVIDER=fake`), con reglas fijas y
la lista de departamentos recibida por constructor. `create_app(settings, model,
directory)` recibe sus dependencias; `app = create_app()` construye las reales.

## Consecuencias

- Agregar un proveedor real es escribir otra clase y una rama en `build_model`.
- Las pruebas inyectan modelos guionizados para cubrir casos que el simulado no produce
  (JSON inválido, herramienta desconocida).
- El conteo de tokens del simulado es aproximado (palabras) y no refleja costos reales.
