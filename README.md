# chilean-legal-mcp

Servidor MCP de investigación legal chilena — 93 herramientas, fuentes oficiales verificables, sin registro ni créditos. Local, ilimitado, con cuerpo FTS, semántica híbrida, corpus CGR/TC/LeyChile, export Word/PDF y corpus JPL opcional.

## Qué hace (93 tools: base + JPL + corpus CGR/TC + conectores FNE/TA/SMA)

| Herramienta | Fuente | Qué devuelve |
|---|---|---|
| `buscar_normas` | BCN SPARQL 748k + FTS local + body | Leyes con filtros `fecha_desde/hasta DD-MM-AAAA`, `tipo`, `materia` + cita |
| `citar_norma` / `citar_json` | BCN | Cita texto y JSON `{numero, fecha DD-MM-AAAA, titulo, url}` |
| `obtener_texto_norma` | `leychile.cl/Consulta/obtxml?opt=7` XML oficial cacheado | Texto completo 14k |
| `exportar_norma` | local | Word `.docx` (python-docx) / PDF `.pdf` (reportlab/weasyprint) en `/tmp` |
| `buscar_semantico` | Híbrido FTS + embeddings MiniLM + sinónimos | `acoso ≈ maltrato` |
| `buscar_dictamenes` | CGR Domino + BCN + FTS | Dictámenes con URL |
| `buscar_jurisprudencia` | BCN + CGR + PJUD público | Jurisprudencia + links |
| `buscar_doctrina` | BCN Articulo 30k + fallback | Artículos |
| `historial_norma` | BCN `hasVersion/modifiesTo` | Vigencia y relaciones |
| `buscar_scielo` / `buscar_dt` / `buscar_diario_oficial` | SciELO, DT, Diario Oficial | Doctrina y normativa sectorial |
| `buscar_todo` | Paralelo real `ThreadPoolExecutor(5)` — incluye JPL si está instalado | Multi-fuente en 1 llamada |
| `jpl_buscar_ley` / `jpl_buscar_articulo` / `jpl_buscar_texto` | Corpus JPL local (53 leyes + ordenanzas 344 comunas) | Leyes JPL, artículos exactos, búsqueda global |
| `jpl_buscar_ordenanza` / `jpl_listar_ordenanzas` | Ordenanzas municipales JPL | Ordenanzas por comuna/materia |
| `jpl_generar_documento` | Corpus JPL + plantillas tribunal | Sentencias, resoluciones, oficios, comparendos |
| `jpl_estado` | local | Estado del corpus JPL |
| `expediente_indexar` / `expediente_preguntar` / `expediente_timeline` / `expediente_partes` | Carpeta local PDF/DOCX/TXT (FTS5) | Expediente propio: fragmentos citados, línea de tiempo, partes |
| `expediente_citas_legales` | Expediente ↔ base nacional local | Derecho invocado con artículo/inciso + verificación [VERIFICADA]/[POR VERIFICAR] |
| `expediente_vigencia_citas` | Expediente ↔ LeyChile | VIGENCIA de cada norma citada (derogada/refundida) + nota intertemporal |
| `expediente_plazos` | Expediente + cómputo procesal | Plazos detectados en documentos con vencimiento y estado frente a hoy |
| `obtener_articulo_texto` | LeyChile XML + caché | Artículo (e inciso) exacto; corte forense con ordinal º/° (art. 2 ≠ art. 20) |
| `computar_plazo_procesal` | Reglas CPC/COT offline | Vencimiento con fundamentos (arts. 38/40 CPC, 66 COT, ley 2.977) |
| `ayuda_acceso_abogado` | — | Links oficiales |

Todas las respuestas incluyen **cita y enlace a la fuente oficial**. Fechas chilenas `DD-MM-AAAA` en entrada y salida. JPL auto-activo si `data/jpl/corpus.db.zlib` está instalado (ver `SETUP.md` + `scripts/install_jpl.py`).

## Instalación

```bash
git clone <repo>
cd chilean-legal-mcp
pip install -e .                    # base: httpx, mcp, python-docx, reportlab
pip install -e ".[semantic]"        # opcional: sentence-transformers para embeddings reales
pip install -e ".[pdf]"             # opcional: weasyprint (requiere libgobject)
python -m chilean_legal_mcp.ingest          # 545 normas iniciales
python -m chilean_legal_mcp.ingest --bulk   # 360k completo (~2h, 150MB)
```

## Uso — cualquier cliente MCP (stdio)

```bash
python -m chilean_legal_mcp.server          # stdio (default)
python -m chilean_legal_mcp.server --http   # HTTP streamable :8000
```

Claude Code: `claude mcp add chilean-legal -- python -m chilean_legal_mcp.server`
Claude Desktop / OpenCode / Cursor / VS Code / Antigravity: `mcpServers: {"chilean-legal": {"command":"python","args":["-m","chilean_legal_mcp.server"]}}`

## Estructura

```
src/chilean_legal_mcp/
  sparql_client.py   # BCN SPARQL + filtros fecha/tipo
  db.py              # SQLite FTS5 (normas, textos, dictamenes)
  jpl/db.py          # Corpus JPL (53 leyes + 5939 ordenanzas 344 comunas) — auto-activo
  jpl/generator.py   # Generador de documentos JPL
  texto.py           # LeyChile obtxml XML
  contraloria.py     # CGR Domino POST
  fuentes_externas.py # SciELO, DT, Diario Oficial
  exportar.py        # docx/pdf
  ingest.py          # incremental + bulk OFFSET
  server.py          # FastMCP 93 tools (base + JPL + corpus CGR/TC + conectores FNE/TA/SMA)
  expediente.py      # Expedientes locales (indexar/preguntar/timeline/partes/citas/vigencia/plazos)
  citas.py           # Extracción de citas normativas (art/inciso) + corte forense de articulado
  plazos.py          # Cómputo procesal chileno (feriados, feriado judicial, arts. 38/40 CPC)
  workflow.py        # Prompt multi-etapa
  semantico.py       # Embeddings locales
scripts/
  install_jpl.py     # Instalador JPL (descarga corpus privado a data/jpl/)
data/
  normas.db          # 29k normas (se genera / se descarga)
  jpl/
    corpus.db.zlib   # 15 MB comprimido JPL (no va a git, se instala)
    corpus.db        # 58 MB descomprimido + FTS (se genera al primer jpl_*)
```

## Fuentes (100% públicas, sin registro)

- **BCN** `datos.bcn.cl/sparql` (Virtuoso)
- **LeyChile** `leychile.cl/Consulta/obtxml?opt=7&idNorma=...`
- **CGR** `contraloria.cl/appinf/...` + BCN Oficio
- **PJUD** `pjud.cl/portal-unificado-sentencias` (Playwright verificado, sin api.pjud.cl)
- **SciELO**, **DT**, **Diario Oficial** — buscadores públicos

## Licencia

MIT
