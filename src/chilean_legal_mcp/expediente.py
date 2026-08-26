"""Análisis de expedientes — estilo análisis de caso de Magnar, 100% local y gratuito.

El abogado indexa una carpeta (PDF, DOCX, TXT, MD): el servidor extrae el texto,
lo indexa en SQLite FTS5 y queda listo para:
  - preguntar sobre el caso (búsqueda con fragmentos contextuales)
  - construir una línea de tiempo (fechas extraídas del texto)
  - identificar partes (RUT y nombres con fórmula don/doña/Sr./Sra.)
Todo local: los documentos nunca salen del computador.

Extracción: pypdf (PDF), python-docx (Word), texto plano (txt/md).
"""

from __future__ import annotations

import re
import unicodedata
from datetime import datetime
from pathlib import Path

from .db import get_db, _fts_prefix_query

EXTENSIONES = {".pdf", ".docx", ".txt", ".md"}
MAX_CHARS_DOC = 400_000          # tope por documento (≈100 págs) para no saturar la BD
FRAGMENTO_CONTEXTO = 350         # caracteres alrededor de cada coincidencia
MESES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "setiembre": 9, "octubre": 10,
    "noviembre": 11, "diciembre": 12,
}


def _hoy() -> str:
    return datetime.now().strftime("%d-%m-%Y %H:%M")


# --- Extracción de texto -----------------------------------------------------

def _extraer_pdf(ruta: Path) -> str:
    from pypdf import PdfReader
    lector = PdfReader(str(ruta))
    paginas = []
    for pag in lector.pages[:400]:  # tope de seguridad 400 páginas
        try:
            paginas.append(pag.extract_text() or "")
        except Exception:  # noqa: BLE001
            paginas.append("")
    return "\n".join(paginas)


def _extraer_docx(ruta: Path) -> str:
    import docx  # python-docx
    d = docx.Document(str(ruta))
    return "\n".join(p.text for p in d.paragraphs if p.text.strip())


def _extraer_texto_plano(ruta: Path) -> str:
    for enc in ("utf-8", "latin-1"):
        try:
            return ruta.read_text(encoding=enc, errors="replace")
        except Exception:  # noqa: BLE001
            continue
    return ""


def extraer_texto(ruta: Path) -> tuple[str, str]:
    """Devuelve (texto, tipo). Tipo: pdf|docx|texto."""
    ext = ruta.suffix.lower()
    try:
        if ext == ".pdf":
            return _extraer_pdf(ruta)[:MAX_CHARS_DOC], "pdf"
        if ext == ".docx":
            return _extraer_docx(ruta)[:MAX_CHARS_DOC], "docx"
        return _extraer_texto_plano(ruta)[:MAX_CHARS_DOC], "texto"
    except Exception as exc:  # noqa: BLE001
        return f"[ERROR DE EXTRACCIÓN: {exc}]", "error"


# --- Indexación ---------------------------------------------------------------

def indexar_carpeta(nombre: str, carpeta: str, reemplazar: bool = True) -> dict:
    """Indexa todos los documentos soportados de una carpeta (recursivo)."""
    nombre = nombre.strip()
    ruta_base = Path(carpeta).expanduser().resolve()
    if not ruta_base.is_dir():
        return {"ok": False, "error": f"La carpeta no existe: {ruta_base}"}
    db = get_db()
    existe = db._conn.execute("SELECT id FROM expedientes WHERE nombre=?", (nombre,)).fetchone()
    if existe:
        if not reemplazar:
            return {"ok": False, "error": f"Ya existe expediente '{nombre}'."}
        eliminar_expediente(nombre)

    eid_cur = db._conn.execute(
        "INSERT INTO expedientes (nombre, carpeta) VALUES (?,?)",
        (nombre, str(ruta_base)))
    eid = eid_cur.lastrowid

    docs, errores, total_chars = [], [], 0
    archivos = sorted(p for p in ruta_base.rglob("*")
                      if p.is_file() and p.suffix.lower() in EXTENSIONES)
    for archivo in archivos:
        texto, tipo = extraer_texto(archivo)
        if tipo == "error" or not texto.strip():
            errores.append({"archivo": archivo.name, "problema": "sin texto extraíble"
                            if tipo != "error" else texto[:120]})
            continue
        db._conn.execute(
            "INSERT INTO expediente_docs (expediente_id, ruta, titulo, tipo, texto) "
            "VALUES (?,?,?,?,?)",
            (eid, str(archivo), archivo.stem, tipo, texto))
        total_chars += len(texto)
        docs.append(archivo.name)
    db._conn.execute(
        "UPDATE expedientes SET num_documentos=?, total_caracteres=? WHERE id=?",
        (len(docs), total_chars, eid))
    db._conn.commit()
    return {"ok": True, "expediente": nombre, "carpeta": str(ruta_base),
            "documentos_indexados": docs, "num_documentos": len(docs),
            "errores": errores, "indexado": _hoy()}


def listar_expedientes() -> list[dict]:
    db = get_db()
    rows = db._conn.execute(
        "SELECT id, nombre, carpeta, creado, num_documentos, total_caracteres "
        "FROM expedientes ORDER BY id DESC").fetchall()
    out = []
    for r in rows:
        paginas_aprox = r["total_caracteres"] // 2500
        out.append({"id": r["id"], "nombre": r["nombre"], "carpeta": r["carpeta"],
                    "creado": r["creado"], "num_documentos": r["num_documentos"],
                    "paginas_aprox": paginas_aprox})
    return out


def eliminar_expediente(nombre: str) -> dict:
    db = get_db()
    row = db._conn.execute("SELECT id FROM expedientes WHERE nombre=?", (nombre.strip(),)).fetchone()
    if not row:
        return {"ok": False, "error": f"No existe expediente '{nombre}'."}
    db._conn.execute("DELETE FROM expediente_docs WHERE expediente_id=?", (row["id"],))
    db._conn.execute("DELETE FROM expedientes WHERE id=?", (row["id"],))
    db._conn.commit()
    return {"ok": True, "eliminada": nombre}


# --- Consulta ------------------------------------------------------------------

def preguntar(nombre: str, pregunta: str, limite: int = 6) -> dict:
    """Búsqueda FTS sobre todo el expediente; devuelve fragmentos con contexto.

    Estrategia en dos pasos: primero busca TODAS las palabras (precisión);
    si no hay resultados, reintenta con CUALQUIERA de ellas (recall).
    """
    db = get_db()
    row = db._conn.execute("SELECT id FROM expedientes WHERE nombre=?", (nombre.strip(),)).fetchone()
    if not row:
        return {"ok": False, "error": f"No existe expediente '{nombre}'. Indexe primero con expediente_indexar."}
    try:
        q_and = _fts_prefix_query(pregunta)
    except ValueError:
        return {"ok": False, "error": "La pregunta no contiene palabras utilizables."}
    palabras = [w for w in pregunta.replace('"', " ").split() if w]

    def _buscar(fts_q: str) -> list:
        sql = """
            SELECT d.id, d.titulo, d.ruta, d.tipo,
                   bm25(expediente_docs_fts) AS score,
                   substr(d.texto, max(1, instr(lower(d.texto), lower(?)) - ?), ?) AS fragmento
            FROM expediente_docs_fts f
            JOIN expediente_docs d ON d.id = f.rowid
            WHERE expediente_docs_fts MATCH ? AND d.expediente_id = ?
            ORDER BY score LIMIT ?
        """
        ancla = palabras[0] if palabras else ""
        return db._conn.execute(sql, (ancla, FRAGMENTO_CONTEXTO // 2,
                                      FRAGMENTO_CONTEXTO * 2,
                                      fts_q, row["id"], max(1, min(limite, 20)))).fetchall()

    rows = _buscar(q_and)
    modo = "todas las palabras"
    if not rows and len(palabras) > 1:
        try:
            q_or = " OR ".join(f'"{w}"*' for w in palabras)
        except ValueError:
            q_or = q_and
        rows = _buscar(q_or)
        modo = "alguna palabra (fallback)"

    hits = []
    for r in rows:
        frag = (r["fragmento"] or "").replace("\n", " ").strip()
        # recorte limpio al inicio/fin de palabra
        if len(frag) > FRAGMENTO_CONTEXTO:
            frag = frag[:FRAGMENTO_CONTEXTO].rsplit(" ", 1)[0] + "…"
        hits.append({"documento": r["titulo"], "ruta": r["ruta"], "tipo": r["tipo"],
                     "relevancia": round(-r["score"], 2), "fragmento": frag})
    return {"ok": True, "expediente": nombre, "pregunta": pregunta, "coincidencias": hits,
            "modo_busqueda": modo}


# --- Línea de tiempo -------------------------------------------------------------

_RE_FECHA_NUM = re.compile(r"\b(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})\b")
_RE_FECHA_PALABRAS = re.compile(
    r"\b(\d{1,2})\s+(?:de\s+)?([a-záéíóúñ]+)\s+(?:del\s+|de\s+)?(20\d{2})\b",
    re.IGNORECASE)


def _normalizar(texto: str) -> str:
    return unicodedata.normalize("NFC", texto)


def _fechas_de_texto(texto: str):
    """Genera (fecha_iso, contexto) para cada fecha detectada."""
    texto = _normalizar(texto).replace("\n", " ")
    vistos: set[str] = set()
    for m in _RE_FECHA_NUM.finditer(texto):
        d, mes, anio = m.group(1).zfill(2), m.group(2).zfill(2), m.group(3)
        iso = f"{anio}-{mes}-{d}"
        if not (1 <= int(mes) <= 12 and 1 <= int(d) <= 31):
            continue
        if iso in vistos:
            continue
        ini, fin = max(0, m.start() - 90), min(len(texto), m.end() + 90)
        vistos.add(iso)
        yield iso, texto[ini:fin].strip()
    for m in _RE_FECHA_PALABRAS.finditer(texto):
        mes_nombre = m.group(2).lower()
        mes = MESES.get(mes_nombre.rstrip("."))
        if not mes:
            continue
        iso = f"{m.group(3)}-{str(mes).zfill(2)}-{m.group(1).zfill(2)}"
        if iso in vistos:
            continue
        ini, fin = max(0, m.start() - 90), min(len(texto), m.end() + 90)
        vistos.add(iso)
        yield iso, texto[ini:fin].strip()


def timeline(nombre: str, limite: int = 40) -> dict:
    """Fechas ordenadas cronológicamente con su contexto dentro del expediente."""
    db = get_db()
    row = db._conn.execute("SELECT id FROM expedientes WHERE nombre=?", (nombre.strip(),)).fetchone()
    if not row:
        return {"ok": False, "error": f"No existe expediente '{nombre}'."}
    eventos = []
    docs = db._conn.execute(
        "SELECT titulo, texto FROM expediente_docs WHERE expediente_id=?",
        (row["id"],)).fetchall()
    for d in docs:
        for iso, ctx in _fechas_de_texto(d["texto"]):
            eventos.append({"fecha": iso, "fecha_cl": iso[8:10] + "-" + iso[5:7] + "-" + iso[:4],
                            "documento": d["titulo"], "contexto": ctx})
    eventos.sort(key=lambda e: e["fecha"])
    return {"ok": True, "expediente": nombre, "total_eventos": len(eventos),
            "eventos": eventos[:max(1, min(limite, 200))]}


# --- Partes -----------------------------------------------------------------------

_RE_RUT = re.compile(r"\b(\d{1,2}\.\d{3}\.\d{3}-[\dkK])\b")
_RE_NOMBRE_FORMULA = re.compile(
    r"\b(?:don|doña|don\s|doña\s)?((?:[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)(?:\s+(?:[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)){1,3})\b")


def partes(nombre: str) -> dict:
    """RUTs y nombres candidatos detectados en el expediente, con frecuencia."""
    db = get_db()
    row = db._conn.execute("SELECT id FROM expedientes WHERE nombre=?", (nombre.strip(),)).fetchone()
    if not row:
        return {"ok": False, "error": f"No existe expediente '{nombre}'."}
    rut_ctx: dict[str, list[str]] = {}
    nombres: dict[str, int] = {}
    docs = db._conn.execute(
        "SELECT titulo, texto FROM expediente_docs WHERE expediente_id=?",
        (row["id"],)).fetchall()
    for d in docs:
        texto = _normalizar(d["texto"]).replace("\n", " ")
        for m in _RE_RUT.finditer(texto):
            rut = m.group(1)
            ini, fin = max(0, m.start() - 80), min(len(texto), m.end() + 80)
            rut_ctx.setdefault(rut, [d["titulo"], texto[ini:fin].strip()])
        for m in _RE_NOMBRE_FORMULA.finditer(texto):
            cand = m.group(1)
            # heurística: excluir frases comunes que empiezan con mayúscula pero no son personas
            if any(w in cand.lower() for w in ("ley ", "código", "codigo", "contraloría",
                                               "tribunal ", "corte ", "ministerio")):
                continue
            nombres[cand] = nombres.get(cand, 0) + 1
    top_nombres = sorted(nombres.items(), key=lambda kv: -kv[1])[:25]
    return {"ok": True, "expediente": nombre,
            "ruts": [{"rut": r, "aparece_en": v[0], "contexto": v[1]}
                     for r, v in list(rut_ctx.items())[:25]],
            "nombres_frecuentes": [{"nombre": n, "apariciones": c} for n, c in top_nombres],
            "nota": ("Los RUT son confiables. Los nombres son CANDIDATOS por patrón "
                     "capitalización; verifique manualmente contra los documentos.")}


# --- Formato narrativo -----------------------------------------------------------

def formatear_indexacion(res: dict) -> str:
    if not res.get("ok"):
        return f"ERROR: {res.get('error', 'desconocido')}"
    lineas = [
        f"EXPEDIENTE INDEXADO — '{res['expediente']}'",
        f"Carpeta analizada: {res['carpeta']}",
        f"Documentos indexados: {res['num_documentos']}",
        f"Fecha de indexación: {res['indexado']}",
        "",
    ]
    if res["documentos_indexados"]:
        lineas.append("Documentos incluidos:")
        for doc in res["documentos_indexados"]:
            lineas.append(f"• {doc}")
        lineas.append("")
    if res["errores"]:
        lineas.append(f"ADVERTENCIA: {len(res['errores'])} archivo(s) sin texto extraíble:")
        for err in res["errores"][:10]:
            lineas.append(f"• {err['archivo']}: {err['problema'][:100]}")
        lineas.append("")
    lineas.append(
        "Qué puede hacer ahora: expediente_preguntar para consultar el caso con citas al "
        "documento fuente, expediente_timeline para la línea de tiempo, o expediente_partes "
        "para identificar RUTs y nombres.")
    return "\n".join(lineas)


def formatear_respuesta(res: dict) -> str:
    if not res.get("ok"):
        return f"ERROR: {res.get('error', 'desconocido')}"
    hits = res["coincidencias"]
    if not hits:
        return (f"Sobre '{res['pregunta']}' en el expediente '{res['expediente']}': no hay "
                "coincidencias textuales. Esto NO significa que el tema no esté en los "
                "documentos: pruebe con otras palabras o revise expediente_timeline/partes.")
    lineas = [
        f"RESPUESTA DESDE EL EXPEDIENTE — '{res['expediente']}'",
        f"Pregunta: \"{res['pregunta']}\"",
        f"{len(hits)} fragmento(s) relevante(s) (búsqueda por {res.get('modo_busqueda', 'todas las palabras')}), cada uno citando su documento fuente:",
        "",
    ]
    for i, h in enumerate(hits, 1):
        lineas.append(f"{i}. Documento: «{h['documento']}» ({h['tipo']})")
        lineas.append(f"   Texto encontrado: \"…{h['fragmento']}…\"")
        lineas.append(f"   Archivo original: {h['ruta']}")
        lineas.append("")
    lineas.append(
        "IMPORTANTE: estos son extractos textuales del expediente, no interpretaciones. "
        "Use las citas entre comillas como base fáctica; el análisis jurídico debe "
        "conectarlos con normas y jurisprudencia (buscar_normas / buscar_tc / buscar_dictamenes).")
    return "\n".join(lineas)


def formatear_timeline(res: dict) -> str:
    if not res.get("ok"):
        return f"ERROR: {res.get('error', 'desconocido')}"
    eventos = res["eventos"]
    lineas = [
        f"LÍNEA DE TIEMPO DEL EXPEDIENTE — '{res['expediente']}'",
        f"{len(eventos)} evento(s) de {res['total_eventos']} fechas detectadas (orden cronológico):",
        "",
    ]
    if not eventos:
        lineas.append("No se detectaron fechas con formato reconocible (DD-MM-AAAA, DD/MM/AAAA "
                      "o '15 de enero de 2026'). Revise si los documentos son escaneados sin OCR.")
    prev_anio = None
    for ev in eventos:
        if ev["fecha"][:4] != prev_anio:
            prev_anio = ev["fecha"][:4]
            lineas.append(f"—— AÑO {prev_anio} ——")
        lineas.append(f"• {ev['fecha_cl']} (en «{ev['documento']}»)")
        lineas.append(f"  Contexto: \"…{ev['contexto']}…\"")
        lineas.append("")
    lineas.append(
        "NOTA: las fechas se extrajeron automáticamente del texto; el CONTEXTO indica qué "
        "ocurría según el documento. Verifique las críticas para la estrategia procesal "
        "(plazos, notificaciones, caducidad).")
    return "\n".join(lineas)


def formatear_partes(res: dict) -> str:
    if not res.get("ok"):
        return f"ERROR: {res.get('error', 'desconocido')}"
    lineas = [f"PARTES DEL EXPEDIENTE — '{res['expediente']}'", ""]
    if res["ruts"]:
        lineas.append(f"RUTs identificados ({len(res['ruts'])}):")
        for r in res["ruts"]:
            lineas.append(f"• {r['rut']} — aparece en «{r['aparece_en']}»")
            lineas.append(f"  Contexto: \"…{r['contexto']}…\"")
            lineas.append("")
    else:
        lineas.append("No se detectaron RUTs con formato válido (XX.XXX.XXX-X).")
        lineas.append("")
    if res["nombres_frecuentes"]:
        lineas.append("Nombres CANDIDATOS más frecuentes (verificar manualmente):")
        for n in res["nombres_frecuentes"][:15]:
            lineas.append(f"• {n['nombre']} — {n['apariciones']} aparición(es)")
        lineas.append("")
    lineas.append(res.get("nota", ""))
    return "\n".join(lineas)


def formatear_listado(exps: list[dict]) -> str:
    if not exps:
        return ("No tienes expedientes indexados.\n"
                "Ejemplo: expediente_indexar(nombre='maffet', carpeta='/ruta/a/carpeta')")
    lineas = [f"TUS EXPEDIENTES ({len(exps)}):", ""]
    for e in exps:
        lineas.append(f"• '{e['nombre']}' — {e['num_documentos']} documento(s), "
                      f"~{e['paginas_aprox']} páginas (creado {e['creado']})")
        lineas.append(f"  Carpeta: {e['carpeta']}")
        lineas.append("")
    return "\n".join(lineas)
