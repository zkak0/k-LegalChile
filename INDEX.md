# ÍNDICE GENERAL — K-LegalChile MCP

Fecha de construcción: 2026-09-04. Fuente: `corpus.db`, `server.py`, `jpl/`, `fuentes_externas.py`.

---

## 1. CORPUS JPL LOCAL (`data/jpl/corpus.db`, 85 MB)

Base de datos SQLite con FTS5, auto-activa. Contiene tres bloques:

### 1.1 Ordenanzas municipales — **5.925 ordenanzas** con texto íntegro

**Top comunas por volumen:**
| Comuna | Ordenanzas |
|---|---|
| Providencia | 281 |
| Santiago | 139 |
| Las Condes | 110 |
| Rancagua | 102 |
| San Bernardo | 89 |
| Peñalolén | 82 |
| Lo Prado | 78 |
| La Granja | 74 |
| La Florida | 73 |
| La Serena | 73 |
| Iquique | 64 |
| La Reina | 63 |
| Vitacura | 62 |
| Villa Alemana | 60 |
| Conchalí | 59 |
| Concepción | 58 |
| Ovalle | 58 |
| Ñuñoa | 55 |
| Vallenar | 55 |
| Recoleta | 48 |

**Materias principales con conteo (totales vigentes):**
| Materia | Cantidad |
|---|---|
| DerechosMunicipales | 1.946 |
| Aseo | 358 |
| Alcoholes | 209 |
| Estacionamiento | 123 |
| Mercado | 106 |
| Publicidad | 79 |
| ParticipaciónCiudadana | 72 |
| Subvenciones | 71 |
| ComercioViaPublica | 69 |
| TenenciaResponsable | 69 |
| FeriasLibres | 67 |
| Locomocion | 81 |
| Ruidos | 51 |
| Residuos | 52 |
| MedioAmbiente | 49 |
| OcupacionBNUP | 35 |
| Transito | 40 |
| CierreCalles | 43 |
| Aridos | 46 |
| Patentes | 24 |
| Parquimetros | 6 |
| TerminalLocomocion | 17 |
| OcupacionViaPublica | 21 |
| ParquesJardines | 5 |
| Humedales | 3 |
| Salud | 7 |

*Total comunas: 344. Total ordenanzas no derogadas: 5.657; derogadas: 266.*

### 1.2 Leyes JPL — **53 leyes** con texto completo

**Leyes principales del JPL (identificador + referencia rápida):**
| Ley | idNorma | Contenido |
|---|---|---|
| Ley 18.287 | 29705 | Procedimiento ante los Juzgados de Policía Local |
| DTO 307 (Ley 15.231) | 12193 | Organización y atribuciones de los JPL |
| DFL 1 18.290 | 1007469 | Ley de Tránsito |
| Ley 19.925 | 220208 | Expendio y consumo de bebidas alcohólicas |
| Ley 19.496 | 61438 | Protección de derechos de los consumidores |
| Ley 21.020 | 1106037 | Tenencia responsable de mascotas |
| CPC Ley 1552 | 22740 | Código de Procedimiento Civil |
| Constitución Política | 242302 | Texto refundido de la CN |
| Ley 13937 | 27575 | Letreros y esquinas |
| Ley 21100 | 1121380 | Prohibición de bolsas plásticas |
| Ley 21368 | 1163603 | Plásticos de un solo uso |
| Ley 21600 | 1195666 | Servicio de biodiversidad y áreas protegidas |
| Ley 19419 | 30786 | Actividades relacionadas con tabaco |
| Ley 19866 | 209169 | Arrendamientos urbanos |
| Ley 21554 | 1191333 | Facilidades de pago derechos de aseo |
| DFL 725 | 5595 | Código Sanitario |
| DFL 850 | 97993 | Ley General de Urbanismo y Construcciones |
| DFL 1 (Medio Ambiente) | 21100 | Base general del medio ambiente |
| Ley 21020 | 1106037 | Tenencia responsable mascotas |

*Completo: 53 leyes de 22 ministerios/organismos, desde DFLs de salud y urbanismo hasta leyes de tránsito, alcoholes, consumidor, medio ambiente, tenencia responsable, propiedad intelectual.*

### 1.3 Manuales internos — **6 manuales**

| # | Nombre | Cat. | Documentos que genera |
|---|---|---|---|
| 1 | FORMATOS-CERTIFICADOS-EXHORTOS | formatos | Certificados, exhortos |
| 2 | FORMATOS-COMPARENDOS-DECLARACIONES | formatos | Comparendos, declaraciones |
| 3 | FORMATOS-OFICIOS-PRESCRIPCION | formatos | Oficios, solicitudes de prescripción |
| 4 | FORMATOS-RESOLUCIONES-CORTAS | formatos | Resoluciones cortas |
| 5 | FORMATOS-SENTENCIAS | formatos | Sentencias (condenatoria, absolutoria) |
| 6 | PLAZOS | plazos | Tabla maestra de plazos JPL (cómputo procesal) |

*Contenido: estructuras exactas con campos, redacción en lenguaje jurídico formal chileno, verificación de cita contra el corpus.*

---

## 2. HERRAMIENTAS JPL (9 tools MCP)

Activas automáticamente si `data/jpl/corpus.db` existe.

| Tool | Qué hace | Cuándo usarla | Parámetros |
|---|---|---|---|
| `jpl_buscar_ley` | Busca término en las 53 leyes del corpus | Quién cite una ley JPL, artículo, concepto | `consulta: str`, `limite: int=10` |
| `jpl_buscar_articulo` | Extrae texto exacto de un artículo de una ley | Necesita citar literal un artículo | `ley: str`, `articulo: int` |
| `jpl_verificar_vigencia` | Devuelve vigencia, versión BCN, estado (derogado/no derogado) | Antes de citar cualquier ley | `ley: str` |
| `jpl_listar_leyes` | Lista todas las 53 leyes con metadatos | Panorama de marcos legales disponibles | sin parámetros |
| `jpl_listar_ordenanzas` | Lista municipalidades con conteo; o ordenanzas de una comuna | Saber qué ordenanzas hay en una comuna | `municipalidad: str\|None` |
| `jpl_buscar_ordenanza` | Busca materia dentro de ordenanzas de una municipalidad | Necesita normativa local de una comuna | `municipalidad: str`, `materia: str`, `limite: int=10` |
| `jpl_buscar_texto` | Búsqueda FTS en TODO el corpus (leyes + 5.925 ordenanzas + manuales) | Búsqueda transversal sin saber dónde está | `consulta: str`, `limite: int=10` |
| `jpl_generar_documento` | Genera documento judicial JPL desde formatos internos | Necesita sentencia, resolución, comparendo, oficio, certificado, exhorto o plazo | `tipo: str`, `datos: str (JSON)`, `formato: str="md"` |
| `jpl_estado` | Diagnóstico del corpus: tamaño, leyes, ordenanzas, FTS | Verificar que JPL está instalado y listo | sin parámetros |

**Tipos de documento válidos para `jpl_generar_documento`:**
`sentencia`, `sentencia_condena`, `sentencia_absolutoria`, `resolucion`, `oficio`, `certificado`, `exhorto`, `comparendo`, `declaracion`, `plazo`

**Datos requeridos (JSON):** `rol`, `comuna`, `denunciado`, `rut`, `domicilio`, `hecho`, `ley`, `articulo`, `dia`, `mes`, `ano`

**Salida:** `.md` (por defecto) o `.docx`. Exporta a disco con verificación de citas contra el corpus.

---

## 3. BÚSQUEDA TRANSVERSAL (`buscar_todo`)

| Tool | Qué hace | Alcance |
|---|---|---|
| `buscar_todo` | Búsqueda paralela en 5 frentes: normas (BCN), dictámenes (CGR), jurisprudencia (PJUD), doctrina, semántico | Consulta general, sin saber la fuente |
| `buscar_todo_fuentes_externas` | Similar pero solo fuentes externas (no corpus interno) | Fuentes gubernamentales |
| `buscar_semantico` | Búsqueda por embeddings (requiere índice previo) | Documentos propios indexados |
| `indexar_semantico` | Construye índice de embeddings por fuente | Primera vez o tras agregar documentos |
| `analizar_consulta` | Analiza consulta del usuario y sugiere herramientas | Antes de ejecutar búsqueda |

---

## 4. HERRAMIENTAS POR ENTIDAD GUBERNAMENTAL

### 4.1 BCN (Biblioteca del Congreso Nacional)
| Tool | Qué entrega |
|---|---|
| `buscar_normas` | Normas legislativas: ley, decreto, DFL con metadados, filtros por fecha/tipo/materia |
| `citar_norma` | Citación formal en formato legal chileno |
| `citar_json` | Citación en JSON estructurado |
| `exportar_norma` | Exporta norma a `.docx` |
| `obtener_texto_norma` | Texto íntegro de la norma (chunked) |
| `historial_norma` | Historial de modificaciones de una norma |
| `estado_vigencia` | Estado de vigencia de una norma |

### 4.2 CGR (Contraloría General de la República)
| Tool | Qué entrega |
|---|---|
| `buscar_dictamenes` | Dictámenes de la CGR con texto completo extraído vía agente Domino (`CompletoDictamenJSON?OpenAgent`) |

### 4.3 PJUD (Jurisprudencia — juris.pjud.cl)
| Tool | Qué entrega |
|---|---|
| `buscar_jurisprudencia` | Sentencias en vivo con texto completo + URL oficial. 10 categorías: corte_suprema (528), corte_apelaciones (168), civiles (328), penales (268), laborales (271), familia (270), cobranza (269), salud_cs (127), lineas_jurisprudenciales (628), compendio_extranjeria (648) |

### 4.4 CPLT (Comisión Parlamentaria de Libertad de Información)
| Tool | Qué entrega |
|---|---|
| `buscar_cplt` | Jurisprudencia administrativa. **BLOQUEO POR IP**: funciona desde otras redes o desplegando `scripts/cplt_worker.js` (Cloudflare Worker gratis) y seteando `CPLT_PROXY` |

### 4.5 TC (Tribunal Constitucional)
| Tool | Qué entrega |
|---|---|
| `buscar_tc` | Sentencias del Tribunal Constitucional |

### 4.6 TDPI (Tribunal de Defensa de la Competencia / TDPC)
| Tool | Qué entrega |
|---|---|
| `tdpi_jurisprudencia` | Jurisprudencia del TDPI (WordPress sin API; boletines PDF de jurisprudencia marcaria) |

### 4.7 SII (Servicio de Impuestos Internos)
| Tool | Qué entrega |
|---|---|
| `buscar_sii` | Búsqueda general SII |
| `sii_buscar_oficio` | Oficios SII |
| `sii_buscar_circular` | Circulares SII |
| `sii_buscar_resolucion` | Resoluciones SII |
| `sii_buscar_fallo` | Fallos SII |

### 4.8 TGR (Tesorería General de la República)
| Tool | Qué entrega |
|---|---|
| `tgr_buscar_dictamen` | Dictámenes TGR |
| `tgr_buscar_resolucion` | Resoluciones TGR |
| `tgr_buscar_circular` | Circulares TGR |
| `tgr_buscar_fallo` | Fallos TGR |

### 4.9 INAPI (Instituto Nacional de Propiedad Industrial)
| Tool | Qué entrega |
|---|---|
| `inapi_buscar_marca` | Búsqueda de marcas registradas |
| `inapi_estados_diarios` | Estados diarios de marcas |

### 4.10 SMA (Superintendencia de Medio Ambiente)
| Tool | Qué entrega |
|---|---|
| `sma_buscar_sancionatorio` | Sanciones ambientales |

### 4.11 SUPERIR (Superintendencia de Insolvencia y Reemprendimiento)
| Tool | Qué entrega |
|---|---|
| `superir_buscar_boletin` | Boletines SUPERIR |

### 4.12 CMF (Comisión para el Mercado Financiero)
| Tool | Qué entrega |
|---|---|
| `buscar_cmf` | Información del mercado financiero |

### 4.13 TDLC (Tribunal de Defensa de la Libre Competencia)
| Tool | Qué entrega |
|---|---|
| `buscar_tdlc` | Decisiones del TDLC |

### 4.14 SUSESO (Superintendencia de Seguridad Social)
| Tool | Qué entrega |
|---|---|
| `buscar_suseso` | Normativa y jurisprudencia SUSESO |

### 4.15 Fiscalía
| Tool | Qué entrega |
|---|---|
| `buscar_casos` | **Sin consulta pública** (reserva art. 260 CPP). Funciona solo con datos del expediente proporcionados |

### 4.16 Diario Oficial
| Tool | Qué entrega |
|---|---|
| `buscar_diario_oficial` | Publicaciones oficiales del Diario Oficial de la República de Chile |

### 4.17 Salud Fuentes
| Tool | Qué entrega |
|---|---|
| `salud_fuentes` | Fuentes normativas y jurisprudenciales en materia de salud |

### 4.18 Doctrina / SCIELO / Datos Gob
| Tool | Qué entrega |
|---|---|
| `buscar_doctrina` | Doctrina jurídica (artículos académicos) |
| `buscar_scielo` | Revistas académicas SCIELO |
| `buscar_datos_gob` | Datos.go.cl (datos abiertos gobierno) |

### 4.19 Fuentes externas adicionales (no conectadas en vivo)
| Fuente | Estado |
|---|---|
| **TDPI** | WordPress sin API pública; solo boletines PDF |
| **Fiscalía** | Sin consulta pública (reserva art. 260 CPP) |
| **CPLT** | Bloqueo por IP; requiere `CPLT_PROXY` o red alternativa |

---

## 5. GENERACIÓN DE ESCRITOS

| Tool | Qué hace | Parámetros |
|---|---|---|
| `generar_escrito` | Genera escrito jurídico (demanda, contestación, etc.) | `tipo`, `datos`, `formato` |
| `generar_escrito_desde_investigacion` | Genera escrito tras investigación previa | `nombre_workflow`, datos |
| `tipos_escrito_disponibles` | Lista tipos de escritos generables | sin parámetros |

---

## 6. WORKFLOWS

| Tool | Qué hace |
|---|---|
| `iniciar_workflow` | Inicia flujo de trabajo con nombre + consulta |
| `continuar_workflow` | Continúa paso actual del workflow |
| `estado_workflow` | Estado de un workflow en curso |
| `listar_workflows` | Lista workflows existentes |

---

## 7. MAPA: QUÉ HACER SEGÚN LA PREGUNTA

| Si necesitas... | Ve a... | Tool |
|---|---|---|
| Saber si una ley JPL está vigente | Corpus local + BCN | `jpl_verificar_vigencia(ley)` |
| Leer artículo exacto de una ley JPL | Corpus local | `jpl_buscar_articulo(ley, art)` |
| Ordenanzas de una comuna específica | Corpus local (344 comunas) | `jpl_listar_ordenanzas(comuna)` o `jpl_buscar_ordenanza(comuna, materia)` |
| Búsqueda general sin saber la fuente | Todas las fuentes | `buscar_todo(query)` |
| Jurisprudencia actual (sentencias) | PJUD en vivo | `buscar_jurisprudencia(query)` |
| Dictámenes CGR | CGR en vivo | `buscar_dictamenes(query)` |
| Normas legislativas | BCN | `buscar_normas(query)` |
| Resoluciones SII | SII | `sii_buscar_resolucion(query)` |
| Marcas registradas | INAPI | `inapi_buscar_marca(query)` |
| Sanciones ambientales | SMA | `sma_buscar_sancionatorio(query)` |
| Dictámenes TGR | TGR | `tgr_buscar_dictamen(query)` |
| Jurisprudencia constitucional | TC | `buscar_tc(query)` |
| Casos de Fiscalía | Fiscalía | `buscar_casos(query)` — solo con datos del expediente |
| Generar sentencia/resolución/comparendo | Manuales internos | `jpl_generar_documento(tipo, datos_json)` |
| Generar escrito jurídico | Plantillas | `generar_escrito(tipo, datos)` |
| Saber plazos procesales JPL | Tabla maestra | `jpl_generar_documento("plazo", {...})` |
| Verificar estado del corpus JPL | Diagnóstico | `jpl_estado()` |
| Buscar doctrina o revista académica | Académico | `buscar_doctrina(query)` / `buscar_scielo(query)` |

---

## 8. ARCHIVOS CLAVE DEL PROYECTO

| Ruta | Contenido |
|---|---|
| `src/chilean_legal_mcp/server.py` | 93 tools MCP; definición de todas las herramientas |
| `src/chilean_legal_mcp/jpl/` | Módulo JPL (db.py, generator.py, __init__.py) |
| `src/chilean_legal_mcp/jpl/db.py` | Conexión corpus, FTS, búsqueda de leyes/ordenanzas/manuales |
| `src/chilean_legal_mcp/jpl/generator.py` | Generador de documentos judiciales (7 tipos) |
| `src/chilean_legal_mcp/pjud_juris.py` | PJUD en vivo (Playwright+stealth+F5 TSPD) |
| `src/chilean_legal_mcp/contraloria.py` | CGR dictámenes (agente Domino) |
| `src/chilean_legal_mcp/fuentes_externas.py` | CPLT, TC, DT, SII, CMF, TGR, INAPI, TDPI, Diario Oficial, FNE, Tribunales Ambientales |
| `src/chilean_legal_mcp/sma.py` | SMA — SNIFA (sancionatorio + procedimientos de fiscalización) |
| `src/chilean_legal_mcp/anti_waf.py` | Fallback cascada anti-bloqueo (curl_cffi → wafer → Camoufox → Playwright) |
| `data/jpl/corpus.db` | Corpus JPL (5.925 ordenanzas, 53 leyes, 6 manuales) |
| `data/normas.db` | 65.027 normas BCN + 41.845 dictámenes CGR + 859 sentencias TC + 9 textos cacheados |
| `scripts/ingest_cgr_apibusca.py` | Ingesta masiva CGR por ventanas de fecha (checkpoint + idempotencia UNID) |
| `scripts/ingest_sentencias_tc.py` | Ingesta de sentencias TC vía backend Paperless oficial |
| `scripts/cplt_worker.js` | Cloudflare Worker para relay CPLT |
| `scripts/install_jpl.py` | Instalación del corpus JPL |
| `tests/` | Suite de tests: `test_mcp.py` (93 tools), `test_jpl.py`, `test_pjud_juris.py`, `test_contraloria.py`, `test_expediente_plazos.py`, `test_indice_cobertura.py` |
| `INDEX.md` | Este archivo |

---

## 9. NOTAS TÉCNICAS

- **CPLT**: bloqueo por IP (403 global). Solución: desplegar `scripts/cplt_worker.js` en Cloudflare Workers (gratis) y setear `CPLT_PROXY`.
- **PJUD**: protegido por F5 BIG-IP ASM. Solución: Playwright + stealth + `page.evaluate(fetch(...))`.
- **CGR**: dictámenes NVA vía agente Domino `CompletoDictamenJSON?OpenAgent` — solo funciona dentro de sesión de navegador.
- **TDPI/Fiscalía**: sin API pública. TDPI solo boletines PDF; Fiscalía reserva art. 260 CPP.
- **Corpus JPL**: `.zlib` (compresión zlib-9) se descomprime a `corpus.db` en primer uso; FTS5 se construye on-demand (~2 min primera vez).
