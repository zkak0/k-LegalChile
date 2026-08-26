# Ejemplos de uso — chilean-legal-mcp

Instalación única: **cero registro, cero costo, una sola base SQLite local.**

## 1 · Primera consulta — buscar normativa

> **Abogado:** "Busca la ley que sanciona el acoso laboral"

El asistente invoca automáticamente `buscar_normas("acoso laboral")` y devuelve:
- Ley 21.643 (2022) — delitos laborales, art. 495 bis
- Ley 20.005 — acoso sexual laboral
- Links oficiales a LeyChile con `idNorma` listo para `obtener_texto_norma`

> **Tip:** si el resultado es largo, pedí `obtener_texto_norma(idNorma=x, offset=0, limite=3000)` para el articulado completo.

---

## 2 · Verificar si una ley sigue vigente

> **Abogado:** "La Ley 18.962, ¿está vigente o fue derogada?"

`estado_vigencia("18.962")` → Lee el encabezado oficial de LeyChile directamente.

Resultado esperado:
- **DEROGADA** — refundida por el DFL-1
- La consulta se cachea en SQLite; repeticiones son instantáneas.

---

## 3 · Usar la memoria (nunca perdés contexto)

### Guardar datos de un cliente
> **Abogado:** "Guardá en memoria: Cliente Rojas, causa rol C-4521-2025, 12° Juzgado Civil Santiago"

El asistente ejecuta:
```
guardar_memoria("Cliente Rojas", "Causa rol C-4521-2025, 12° Juzgado Civil Santiago. Clave OJV: rdc4521", "causa")
```
Esa información **nunca expira** y solo está en tu computadora.

### Retomar al día siguiente
> **Abogado:** "¿Qué estábamos viendo de Rojas?"

`consultar_memoria("Rojas")` devuelve la nota + todas las interacciones anteriores.

### Ver las últimas consultas de la semana
`historial_conversacion(limite=20)` — muestra preguntas y respuestas en orden cronológico.

### Resumen de trabajo
`resumen_trabajo(dias=7)` — cuántas consultas se hicieron, qué se trabajó cada día.

> **Nota:** las consultas se registran automáticamente — no necesitás guardar nada a mano, salvo datos importantes como claves o causales.

---

## 4 · Análisis multi-fuente

> **Abogado:** "Analiza el art. 495 bis del Código del Trabajo: jurisprudencia y vigencia"

El asistente ejecuta `analizar_consulta("art. 495 bis Código del Trabajo")` y consulta en paralelo:
- BCN SPARQL (DepositaNormas)
- LeyChile texto completo
- TGR → fallos de Cortes de Apelaciones
- SII → oficios por materia
- SciELO → doctrina académica (vía DOI)

El resultado es un solo informe síntesis con links oficiales para verificar cada fuente.

---

## 5 · Buscar casos parecidos

> **Abogado:** "Busca casos similares: demandante despedido por denunciar acoso laboral"

`buscar_casos("demandante despedido denunciar acoso laboral")` busca en los casos ya extraídos por el sistema (FTS5 sobre hechos y resolución). A medida que usás las herramientas de SII/TGR/BCN, los casos se agregan solo.

---

## 6 · Obtener el texto completo de una norma

`obtener_texto_norma(idNorma=30669, offset=0, limite=5000)` devuelve el artículo 495 bis completo en texto plano. Usá `offset` y `limite` para recorrer normas largas como códigos (ej. `offset=5000, limite=5000` para el segundo bloque).

---

## 7 · Exportar informe a Word

> **Abogado:** "Exportá el informe a Word"

Cualquier respuesta del análisis se puede exportar con `exportar_a_word(titulo, cuerpo_markdown)` y se genera `informe.docx` listo para presentar.

---

## 8 · Verificar el estado de las fuentes

`verificar_estado_fuentes()` revisa 15 endpoints oficiales en tiempo real:
- ONLINE (13/15) — responden normalmente
- WAF_BLOQUEADO (SciELO, TGR raíz) — bloqueo automático temporal, no crítico
- CAIDO — sitio fuera de línea

---

## 9 · Acceso honesto para fuentes bloqueadas

Algunas fuentes tienen restricciones técnicas (reCAPTCHA, WAF): el sistema te redirige al link oficial directo sin inventar datos.
- **INAPI marcas**: captcha oficial → link directo al buscador
- **CPLT**: bloqueo Imperva → link a base de datos
- **Historia de la Ley**: formulario incompleto → link funcional

---

## 10 · Vigilancia legal automática (estilo Magnar Monitor, pero gratis)

Define una condición en lenguaje natural y el servidor vigila fuentes oficiales por ti:

```
vigilancia_crear(
    nombre='datos_salud',
    condicion='nuevas sentencias o normas sobre protección de datos de salud',
    fuentes=['tc','cgr','normas'])
```

Luego, cada vez que quieras revisar novedades:

```
vigilancia_ejecutar('datos_salud')   → informe narrativo SOLO con lo nuevo (dedupe por URL)
vigilancia_historial('datos_salud')  → ítems acumulados
vigilancia_marcar_revisados('datos_salud') → cierra la ronda
vigilancia_listar() / vigilancia_pausar() / vigilancia_eliminar()
```

Fuentes vigilables: `tc` (sentencias TC), `cgr` (dictámenes), `tgr` (Tesorería), `sii`
(oficios tributarios), `diario_oficial` (normas DO vía LeyChile), `normas` (legislación BCN).

El servidor detecta por palabras clave derivadas de tu condición; tú (o tu LLM) haces el
filtrado semántico final leyendo los títulos. Cada novedad llega con su link oficial verificable.

---

## 11 · Análisis de expedientes propios (estilo Magnar Agent)

Indexa una carpeta con los documentos del caso y pregúntale:

```
expediente_indexar(nombre='caso_rocio', carpeta='/Users/yo/Desktop/caso_rocio')
expediente_preguntar('caso_rocio', pregunta='qué resolvió la Vista Fiscal')
expediente_timeline('caso_rocio')     → fechas ordenadas con contexto
expediente_partes('caso_rocio')       → RUTs + nombres candidatos
expediente_listar() / expediente_eliminar()
```

Soporta PDF, DOCX, TXT y MD (recursivo). Las respuestas son extractos TEXTUALES citando el
documento fuente — úsalas como base fáctica y conéctalas con buscar_normas/buscar_tc.
Todo queda local: tus documentos nunca salen del computador.

---

## Reglas del sistema

- Chile solo — fuentes oficiales chilenas.
- Sin limite — no hay cupos ni pagos.
- Fechas en `DD-MM-AAAA` en toda la conversación.
- No inventar casos — todas las citas son verificables con fecha oficial.
- Terceros (Crossref) rotulados como `[vía DOI/Crossref]`.