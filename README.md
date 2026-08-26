# chilean-legal-mcp

Servidor MCP de investigación legal chilena — 15 herramientas, fuentes oficiales verificables, sin registro ni créditos. Mejor que Trifolia: local, ilimitado, con cuerpo FTS, semántica híbrida y export Word/PDF.

## Qué hace (15 tools)

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
| `buscar_todo` | Paralelo real `ThreadPoolExecutor(4)` | Multi-fuente en 1 llamada |
| `ayuda_acceso_abogado` | — | 6 links oficiales |

Todas las respuestas incluyen **cita y enlace a la fuente oficial**. Fechas chilenas `DD-MM-AAAA` en entrada y salida.

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
  sparql_client.py  # BCN SPARQL + filtros fecha/tipo
  db.py             # SQLite FTS5 (normas, textos, dictamenes) + check_same_thread=False
  texto.py          # LeyChile obtxml XML
  contraloria.py    # CGR Domino POST
  fuentes_externas.py # SciELO, DT, Diario Oficial
  exportar.py       # docx/pdf
  ingest.py         # incremental + bulk OFFSET
  server.py         # FastMCP 15 tools, paralelo real
data/
  normas.db (545)
  jpl/README.md     # reservado Ley 18.287
```

## Fuentes (100% públicas, sin registro)

- **BCN** `datos.bcn.cl/sparql` (Virtuoso)
- **LeyChile** `leychile.cl/Consulta/obtxml?opt=7&idNorma=...`
- **CGR** `contraloria.cl/appinf/...` + BCN Oficio
- **PJUD** `pjud.cl/portal-unificado-sentencias` (Playwright verificado, sin api.pjud.cl)
- **SciELO**, **DT**, **Diario Oficial** — buscadores públicos

## Licencia

MIT
