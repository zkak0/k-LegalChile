# SETUP.md — Guía de migración y reinstalación completa

> **Objetivo**: levantar el proyecto desde cero en otro equipo sin depender de archivos locales previos.

---

## 1 · Requisitos previos

### Sistema
- **macOS** (desarrollado en Darwin; funciona en Linux y Windows con ajustes menores).
- **Python 3.14** (recomendado; soportado ≥3.10).
- **Git** para clonar el repositorio.
- **8 GB RAM** mínimo (4 GB funcionan pero compilan más lento).

### Dependencias del sistema (solo para PDF)
```bash
# macOS (Homebrew)
brew install python@3.14 gobject-introspection cairo pango gdk-pixbuf libffi

# Ubuntu/Debian
sudo apt-get install python3-dev libffi-dev libcairo2 libpango-1.0-0 libgdk-pixbuf-2.0-0
```

> **Nota**: el PDF es opcional. El proyecto funciona 100% en modo stdio con DOCX.

---

## 2 · Clonación del repositorio

```bash
git clone https://github.com/zkak0/k-LegalChile.git
cd k-LegalChile
```

### Estructura tras el clone
```
k-LegalChile/
├── src/chilean_legal_mcp/   # Código fuente (77 tools: 68 base + 9 JPL)
│   └── jpl/                 # Subpaquete JPL (auto-activo si data/jpl/corpus.db existe)
├── scripts/install_jpl.py   # Instalador JPL (requiere token acceso privado K-LegalJPL)
├── tests/                   # Suite de tests (109)
├── data/                    # Bases de datos y caché (NO versionado)
├── pyproject.toml           # Dependencias Python
└── README.md                # Resumen público
```

---

## 3 · Entorno virtual

```bash
# macOS/Linux
python3 -m venv .venv
source .venv/bin/activate

# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1
```

---

## 4 · Instalación de dependencias

```bash
# Base (siempre)
pip install --upgrade pip
pip install -e .

# Opcional: búsqueda semántica (embeddings con MiniLM)
# Descarga ~500 MB la primera vez
pip install -e ".[semantic]"

# Opcional: exportación PDF ( requiere las deps del sistema del punto 1)
pip install -e ".[pdf]"
```

---

## 5 · Generación de datos locales

> **Importante**: la base de datos `data/normas.db` (≈14 MB, 29.000+ registros) está excluida del repositorio.

### Opción A: descargar (rápido)
Pedí el archivo `data/normas.db` por canal privado. Es un SQLite listo para usar.

### Opción B: regenerar desde cero (2–4 h, sin costo)
```bash
python -m chilean_legal_mcp.ingest --bulk
```

Progreso estimado:
- Metadatos (título, número, fecha, link): 29.000+ registros.
- Textos completos: se descargan bajo demanda al consultar `obtener_texto_norma`.

### Verificación
```bash
python -c "from chilean_legal_mcp.db import get_db; db = get_db(); print(f'Normas: {db.count()}')"
# Esperado: ~29000
```

---

## 6 · Arquitectura local

```
data/
├── normas.db           # SQLite principal (FTS5, 29k normas + metadatos) — 14 MB
├── cookies/            # Cookies de sesión por dominio (auto-generadas)
└── jpl/                # Corpus JPL (privado, no versionado)
    ├── corpus.db.zlib  # 15 MB comprimido (descargado via install_jpl.py)
    └── corpus.db       # 58 MB descomprimido + índices FTS (se genera al primer uso)
```

### ¿Qué NO se versiona en Git?
- `data/*.db` y `data/**/*.db` — bases de datos locales (demasiado grandes; se regeneran / descargan).
- `data/**/*.zlib` — corpus JPL comprimido (privado).
- `data/cookies/` — sesiones temporales.
- `AUDIT.md` — documentación interna.
- `logs/` — registros de ejecución.
- `casos/` y `casos_docs/` — documentos de casos locales.

---

## 7 · Ejecución del servidor

### Modo estándar (stdio)
```bash
python -m chilean_legal_mcp.server
```

### Modo HTTP (streamable, puerto 8000)
```bash
python -m chilean_legal_mcp.server --http
# Abre http://localhost:8000
```

### Integración con clientes MCP

| Cliente | Configuración |
|---------|--------------|
| **Claude Code** | `claude mcp add chilean-legal -- python -m chilean_legal_mcp.server` |
| **Claude Desktop** | Agregar a `claude_desktop_config.json` (ver README) |
| **OpenCode / Cursor / VS Code** | Agregar a `.vscode/settings.json` o `mcp.json` del proyecto |

---

## 8 · Verificación post-instalación

```bash
# Tests (sin JPL)
pytest tests/ -v -k "not jpl"
# Esperado: 96 passed, 1 skipped

# Tests con JPL (si está instalado)
pytest tests/test_jpl.py -v
# Esperado: 13 passed

# Tests completos
pytest tests/ -v
# Esperado: 109 passed, 1 skipped (con JPL)

# Salud de fuentes
python -c "from chilean_legal_mcp.salud_fuentes import verificar_todas; print(verificar_todas())"
# Esperado: 13+ endpoints ONLINE

# Estado JPL
python -c "from chilean_legal_mcp.server import jpl_estado; print(jpl_estado())"
# Si instalado: 53 leyes, ~5939 ordenanzas, índices FTS listos
# Si no: "JPL no instalado..." con instrucción
```

---

## 9 · Instalación JPL (corpus privado, opcional)

El corpus JPL (Leyes + ordenanzas 344 comunas + manuales) está en el repo privado `K-LegalJPL` (15 MB `corpus.db.zlib`). **No se incluye** en `k-LegalChile` público. Para activarlo:

```bash
# Opción 1: instalador automático (recomendada) — pide token por entrada segura
python scripts/install_jpl.py
# → busca sibling ../K-LegalJPL/corpus.db.zlib (si ya lo clonaste)
# → si no, pide GITHUB_TOKEN y descarga via API
# → guarda en data/jpl/corpus.db.zlib (15 MB)
# → verifica al final (descomprime + construye FTS + prueba buscar_ley)

# Opción 2: token por env var
GITHUB_TOKEN=ghp_... python scripts/install_jpl.py

# Opción 3: clon hermano manual (sin token en historial)
git clone https://<token>@github.com/zkak0/K-LegalJPL.git ../K-LegalJPL
python scripts/install_jpl.py   # detecta sibling y copia local

# Verificar JPL
python -c "from chilean_legal_mcp.server import jpl_estado; print(jpl_estado())"
# → "53 leyes, 5939 ordenanzas, FTS listos, 58 MB"
```

> **Primer uso del MCP**: al llamar cualquier `jpl_*` por primera vez, el servidor descomprime `corpus.db.zlib` → `corpus.db` (58 MB) y construye índices FTS (~1s). Siguientes consultas: <10ms. El token nunca se guarda en disco.

## 10 · Migración de datos locales

Si venís usando el proyecto en otro equipo y querés llevar:

| Dato | Ruta origen | Ruta destino | Tamaño |
|------|------------|--------------|--------|
| Base de datos | `data/normas.db` | `data/normas.db` | ~14 MB |
| JPL corpus | `data/jpl/corpus.db.zlib` | `data/jpl/corpus.db.zlib` | ~15 MB |
| JPL descomprimido | `data/jpl/corpus.db` | (se regenera solo) | — |
| Cookies/sesiones | `data/cookies/` | `data/cookies/` | <1 MB |
| Memoria (notas) | Dentro de `normas.db` tabla `memoria_mensajes` | Se incluye en `.db` | — |
| Expedientes indexados | Dentro de `normas.db` tablas `expedientes`, `expediente_docs` | Se incluye en `.db` | — |
| Vigilancias creadas | Dentro de `normas.db` tablas `vigilancias`, `vigilancia_items` | Se incluye en `.db` | — |

> Basta con copiar `data/normas.db`, `data/jpl/corpus.db.zlib` y `data/cookies/` al nuevo equipo. `corpus.db` se regenera solo al primer `jpl_*`.

---

## 11 · Troubleshooting rápido

| Problema | Solución |
|----------|----------|
| `pip install sentence-transformers` falla | Usar Python 3.10–3.12; 3.14 puede requerir compilación desde source |
| `weasyprint` no instala | Instalar las dependencias del sistema del punto 1, luego `pip install weasyprint` |
| Playwright no se instala | `playwright install chromium` (descarga ~300 MB la primera vez) |
| Base de datos corrupta o vacía | Borrar `data/normas.db` y correr `python -m chilean_legal_mcp.ingest --bulk` |
| Tests fallan con "no module" | Activar `.venv`: `source .venv/bin/activate` |
| WAF bloquea sitios | Esperar 1 h o usar `--http` con timeout mayor |
| `jpl_*` dice "no instalado" | Ejecutar `python scripts/install_jpl.py` con token válido |
| `jpl_*` lento primera vez | Normal: descomprime 15→58 MB + FTS (~1s). Siguiente: <10ms |
| `corpus.db` corrupto | Borrar `data/jpl/corpus.db` y re-llamar cualquier `jpl_*` (se regenera) |

---

## 12 · Resumen de comandos (copy-paste)

```bash
# Setup completo desde cero
git clone https://github.com/zkak0/k-LegalChile.git
cd k-LegalChile
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
pip install -e ".[semantic]"   # opcional
pip install -e ".[pdf]"        # opcional

# Si tenés el .db
cp /ruta/a/normas.db data/

# Si no, a generar
python -m chilean_legal_mcp.ingest --bulk

# JPL (opcional, requiere acceso privado)
python scripts/install_jpl.py   # pide token, descarga 15 MB → data/jpl/
# o: GITHUB_TOKEN=ghp_... python scripts/install_jpl.py

# Ejecutar
python -m chilean_legal_mcp.server

# Verificar
pytest tests/ -v
python -c "from chilean_legal_mcp.server import jpl_estado; print(jpl_estado())"
```

---

## 13 · Checklist post-migración

- [ ] `pytest tests/` pasa (96 sin JPL, 109 con JPL)
- [ ] `python -c "from chilean_legal_mcp.db import get_db; print(get_db().count())"` → >20000
- [ ] `python -c "from chilean_legal_mcp.server import jpl_estado; print(jpl_estado())"` → JPL listo o mensaje de instalación
- [ ] `python -m chilean_legal_mcp.server` arranca sin errores
- [ ] Cliente MCP conecta (probar `buscar_normas("test")`, `jpl_buscar_ley("transito")` si JPL activo)
- [ ] `data/cookies/` tiene cookies generadas (si accediste a sitios con WAF)
- [ ] Memoria recuperada: `consultar_memoria("test")` devuelve notas previas

---

**Documento generado el**: 26-08-2026  
**Versión del proyecto**: 0.1.1  
**Tools**: 77 (68 base + 9 JPL) | **Tests**: 109 (96 base + 13 JPL)