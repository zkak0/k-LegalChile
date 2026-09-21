# AGENTS.md — Reglas operativas del proyecto K-LegalChile

Este documento fija las reglas permanentes para cualquier agente que trabaje en este repositorio. **Son obligaciones**, no sugerencias.

---

## 1. Regla de obligación — RESPONDER SIEMPRE PRIMERO CON EL SERVIDOR MCP INTERNO

Toda pregunta del usuario se responde **primero con el corpus local del servidor MCP K-LegalChile** y solo después, **si la cobertura interna no existe o no calza**, con fuentes externas (LeyChile, PJUD, CGR en vivo, SciELO, etc.).

**Nunca al revés. Nunca externo primero.**

### 1.1 Cómo se decide → `clasificar()` en `indice_cobertura.py`

El sistema ya tiene implementado el índice de cobertura. Cualquier agente que toque `analizar_consulta` (o futuros motores de respuesta) debe rutar usando `clasificar(consulta)`, que devuelve:

- `"interno"` → materia con cobertura local alta (leyes/normas, Contraloría, JPL/policía local).
- `"hibrido"` → materia con cobertura local escasa (SII, TGR, INAPI, TDLC, SMA, SuperIR): intentar interno; si no calza, externo.
- `"externo"` → materia sin cobertura local (familia, civil, laboral, penal, garantía): ir directo a fuentes externas.

### 1.2 Orden de las secciones en la respuesta (obligatorio)

1. **Respuesta directa** (3-5 líneas) al inicio.
2. **Fundamento normativo** con texto literal del artículo (LeyChile/JPL local primero).
3. **Casos por tipo**: CGR (corpus local) → JPL → jurisprudencia judicial → otras fuentes externas; cada caso con carátula/rol, N° y fechas, qué resolvió, por qué aplica, link oficial.
4. **Criterios** de Contraloría con su estado (cuando corresponda).
5. **Lo no cubierto** por las fuentes.
6. **Referencias** con URLs oficiales.

### 1.3 Reglas de contenido (fijas, no negociables)

- **Sin recortes** de contenido en la respuesta final. No usar `[:N]` en la salida al usuario.
- **Sin placeholders** genéricos (`"[Redactar conclusión…]"`, `"Criterio 1: …"`). Si el dato no existe, o se busca o se declara que no se encontró.
- **Sin branding externo**: no mencionar COCHID / Veridictum / dictamina.bot / "réplica". El corpus es de **K-LegalChile**.
- Los casos de Contraloría se presentan con **sumario + N° + fecha + link oficial** (no traen carátula de partes).
- **Verdadero antes que bonito**: si una fuente no responde o el dato no existe, decirlo, nunca inventar.

### 1.4 Orden de decisión (resumen rápido)

```
¿La pregunta tiene materia con cobertura interna alta (leyes / Contraloría / JPL)?
  Sí → responder con corpus local. Agregar externo solo si algo falta.
  No → ¿tiene cobertura baja (SII/TGR/INAPI/TDLC/SMA/SuperIR)?
      Sí → intentar interno; si no calza, salir a externo.
      No → (familia/civil/laboral/penal) salir directo a externo.
  En duda → `interno` por defecto con índice `hibrido`.
```

---

## 2. Áreas adicionales (redacción de documentos)

- Los documentos judiciales se generan desde `jpl/generator.py` **componiendo desde los formatos reales del corpus**, nunca desde plantillas inventadas.
- Toda cita de ley/artículo en un documento generado se verifica contra el corpus (`etapa_verificar`); la alerta final indica si quedaron sin confirmar.
- El documento al usuario se devuelve completo (sin cortes); el usuario revisa y rellena los marcadores `[NOMBRE]`/`[ROL]`/etc.

---

## 3. Testing

- `pytest tests/ -q` debe pasar completo. Nuevo test relevante: `tests/test_indice_cobertura.py` cubre `clasificar()` y el ruteo de `analizar_consulta`.

---

## 4. Convenciones de este repo

- Lenguaje: Python 3.14 (`/Library/Frameworks/Python.framework/Versions/3.14/bin/python3`).
- Sin emojis en el código ni en documentos generados.
- Los PDF/DB locales (data/, kb/*.db, data/*.csv) no se versionan (ver `.gitignore`).
