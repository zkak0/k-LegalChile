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


def _ocr_disponible() -> str | None:
    """Devuelve el motor OCR disponible ('ocrmypdf' o 'tesseract') o None."""
    import shutil
    if shutil.which("ocrmypdf"):
        return "ocrmypdf"
    if shutil.which("tesseract") and shutil.which("pdftoppm"):
        return "tesseract"
    return None


def _ocr_pdf(ruta: Path, limite_paginas: int = 30) -> str | None:
    """OCR de un PDF escaneado cuando hay herramienta local.

    No instala nada ni envía el documento a ningún servicio: todo local.
    Devuelve None si no hay motor OCR o si el intento falla (honestidad).
    """
    motor = _ocr_disponible()
    if not motor:
        return None
    import subprocess
    import tempfile
    try:
        if motor == "ocrmypdf":
            with tempfile.TemporaryDirectory() as tmp:
                salida = Path(tmp) / "ocr.pdf"
                subprocess.run(
                    ["ocrmypdf", "--skip-text", "-l", "spa",
                     "--pages", f"1-{limite_paginas}", str(ruta), str(salida)],
                    check=True, capture_output=True, timeout=180)
                return _extraer_pdf(salida)
        # tesseract + pdftoppm
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run(["pdftoppm", "-l", str(limite_paginas), "-png",
                            str(ruta), str(Path(tmp) / "pag")],
                           check=True, capture_output=True, timeout=180)
            partes = []
            for img in sorted(Path(tmp).glob("pag-*.png")):
                r = subprocess.run(["tesseract", str(img), "stdout", "-l", "spa"],
                                   capture_output=True, timeout=120)
                if r.returncode == 0:
                    partes.append(r.stdout.decode("utf-8", "replace"))
            return "\n".join(partes) or None
    except Exception:  # noqa: BLE001
        return None


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
            # Segunda oportunidad honesta: OCR local si hay motor instalado
            if tipo != "error" and archivo.suffix.lower() == ".pdf":
                ocr = _ocr_pdf(archivo)
                if ocr and ocr.strip():
                    texto, tipo = ocr[:MAX_CHARS_DOC], "pdf-ocr"
            if tipo == "error" or not texto.strip():
                if tipo == "error":
                    problema = texto[:120]
                elif archivo.suffix.lower() == ".pdf":
                    problema = (
                        "sin texto extraíble (documento escaneado). Instale OCR local "
                        "para intentar leerlo: brew install ocrmypdf (o tesseract + poppler)"
                        if _ocr_disponible() is None else
                        "sin texto extraíble tras intento de OCR")
                else:
                    problema = "sin texto extraíble"
                errores.append({"archivo": archivo.name, "problema": problema})
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


# --- Citas normativas (conexión documentos locales ↔ legislación nacional) ---------

def _buscar_norma_local(referente: str) -> dict | None:
    """Busca el referente normativo ('Código Civil', 'Ley 19.966') en las normas
    nacionales indexadas localmente. Devuelve la mejor coincidencia o None."""
    db = get_db()
    m = re.search(r"(?:Ley|ley)\s+(\d{1,3}(?:\.\d{3})+|\d+)", referente)
    if m:
        digitos = m.group(1).replace(".", "")
        row = db._conn.execute(
            "SELECT titulo, numero, leychile_id FROM normas "
            "WHERE REPLACE(numero,'.','') = ? OR numero = ? LIMIT 1",
            (digitos, m.group(1))).fetchone()
        if row:
            return {"titulo": row["titulo"], "numero": row["numero"],
                    "leychile_id": row["leychile_id"]}
        row = db._conn.execute(
            "SELECT titulo, numero, leychile_id FROM normas WHERE numero LIKE ? LIMIT 1",
            (f"%{digitos}%",)).fetchone()
        if row:
            return {"titulo": row["titulo"], "numero": row["numero"],
                    "leychile_id": row["leychile_id"]}
        return None
    # por nombre del cuerpo legal (sin tildes, LIKE plano)
    plano = "".join(c for c in unicodedata.normalize("NFD", referente)
                    if unicodedata.category(c) != "Mn").upper()
    for row in db._conn.execute(
            "SELECT titulo, numero, leychile_id FROM normas WHERE UPPER(titulo) LIKE ? LIMIT 5",
            (f"%{plano}%",)).fetchall():
        return {"titulo": row["titulo"], "numero": row["numero"],
                "leychile_id": row["leychile_id"]}
    return None


def citas_normativas(nombre: str, limite: int = 50) -> dict:
    """Extrae de los documentos del expediente las citas a la legislación nacional
    (artículo / inciso / cuerpo legal), con el documento y el contexto donde
    aparecen, y verifica cada norma invocada contra la base nacional local."""
    from .citas import extraer_citas
    db = get_db()
    row = db._conn.execute("SELECT id FROM expedientes WHERE nombre=?", (nombre.strip(),)).fetchone()
    if not row:
        return {"ok": False, "error": f"No existe expediente '{nombre}'."}
    docs = db._conn.execute(
        "SELECT titulo, texto FROM expediente_docs WHERE expediente_id=?",
        (row["id"],)).fetchall()

    citas: list[dict] = []
    for d in docs:
        texto = _normalizar(d["texto"])
        plano = re.sub(r"\s+", " ", texto)
        for c in extraer_citas(plano):
            ini = max(0, c["posicion"] - 110)
            fin = min(len(plano), c["posicion"] + len(c["literal"]) + 110)
            citas.append({
                "documento": d["titulo"],
                "tipo": c["tipo"],
                "referente": c.get("cuerpo")
                    or f"{c.get('clase','').strip().capitalize()} {c.get('numero','')}".strip(),
                "articulos": c["articulos"],
                "inciso": c["inciso"],
                "literal": c["literal"],
                "contexto": plano[ini:fin].strip(),
            })
    citas = citas[:max(1, min(limite, 200))]

    # Verificación contra la base nacional local (una vez por referente)
    por_referente: dict[str, list[dict]] = {}
    for c in citas:
        por_referente.setdefault(c["referente"], []).append(c)
    normas_invocadas = []
    for referente, grupo in por_referente.items():
        hall = _buscar_norma_local(referente)
        arts = sorted({a for c in grupo for a in c["articulos"]},
                      key=lambda a: (len(a), a))
        normas_invocadas.append({
            "referente": referente,
            "veces_citada": len(grupo),
            "articulos_citados": arts,
            "verificacion": ({
                "estado": "verificada_local",
                "titulo_oficial": hall["titulo"],
                "numero": hall["numero"],
                "leychile_id": hall["leychile_id"],
                "enlace": f"https://www.bcn.cl/leychile/navegar?idNorma={hall['leychile_id']}",
            } if hall else {
                "estado": "por_verificar",
                "detalle": ("No consta en la base nacional local; confirme con "
                            "buscar_normas / obtener_texto_norma antes de citar en juicio."),
            }),
        })

    return {"ok": True, "expediente": nombre, "total_citas": len(citas),
            "citas": citas, "normas_invocadas": normas_invocadas,
            "nota": ("Las citas se detectaron por patrón terminológico. 'verificada_local' "
                     "significa que el cuerpo legal consta en la base nacional; el artículo e "
                     "inciso citados deben contrastarse con el texto oficial (obtener_texto_norma / "
                     "obtener_articulo_texto) antes de invocarlas ante el tribunal.")}


def formatear_citas(res: dict) -> str:
    if not res.get("ok"):
        return f"ERROR: {res.get('error', 'desconocido')}"
    lineas = [
        f"CITAS NORMATIVAS DEL EXPEDIENTE — '{res['expediente']}'",
        f"Atendido el examen de los documentos indexados, se advierten "
        f"{res['total_citas']} cita(s) a la legislación nacional.",
        "",
    ]
    if not res["citas"]:
        lineas.append("No se detectaron citas normativas ('artículo … del Código …', "
                      "'Ley N° …', 'Decreto …'). Esto no asegura su inexistencia: "
                      "revise los documentos manualmente.")
        return "\n".join(lineas)

    lineas.append("I. NORMAS INVOCADAS (estatus de verificación local)")
    lineas.append("")
    for n in sorted(res["normas_invocadas"], key=lambda x: -x["veces_citada"]):
        ver = n["verificacion"]
        sello = "[VERIFICADA EN BASE LOCAL]" if ver["estado"] == "verificada_local" else "[POR VERIFICAR]"
        lineas.append(f"• {n['referente']} {sello} — citada {n['veces_citada']} vez(ces)")
        if n["articulos_citados"]:
            lineas.append(f"  Artículos citados: {', '.join(n['articulos_citados'])}")
        if ver["estado"] == "verificada_local":
            lineas.append(f"  Título oficial: {ver['titulo_oficial']} (N° {ver['numero']})")
            lineas.append(f"  Fuente: {ver['enlace']}")
        else:
            lineas.append(f"  {ver['detalle']}")
        lineas.append("")
    lineas.append("II. DETALLE DE LAS CITAS CON SU UBICACIÓN EN EL EXPEDIENTE")
    lineas.append("")
    for i, c in enumerate(res["citas"], 1):
        detalle = c["literal"]
        if c["inciso"]:
            detalle += f" [inciso {c['inciso']}]"
        lineas.append(f"{i}. {detalle}")
        lineas.append(f"   Documento: «{c['documento']}»")
        lineas.append(f"   Contexto: \"…{c['contexto']}…\"")
        lineas.append("")
    lineas.append("NOTA: " + res["nota"])
    return "\n".join(lineas)


def vigencia_citas(nombre: str) -> dict:
    """Estado de vigencia de las normas invocadas por el expediente.

    Para cada norma con sello 'verificada_local' consulta estado_vigencia
    (con caché SQLite de 7 días); las 'por_verificar' se reportan sin romper.
    Añade la advertencia intertemporal obligatoria."""
    base = citas_normativas(nombre)
    if not base.get("ok"):
        return base
    from . import vigencia as _vig  # lazy: permite tests sin red y evita import circular
    items = []
    for n in base["normas_invocadas"]:
        ver = n["verificacion"]
        if ver.get("estado") != "verificada_local" or not ver.get("leychile_id"):
            items.append({**n, "vigencia": {
                "estado": "no_verificable",
                "detalle": ("La identidad de la norma no consta en la base local "
                            "[POR VERIFICAR]; primero confirme la norma y luego su vigencia."),
            }})
            continue
        try:
            est = _vig.estado_vigencia(ver["leychile_id"])
        except Exception as exc:  # noqa: BLE001
            est = {"estado": "error", "detalle": f"No fue posible consultar la vigencia: {exc}"}
        items.append({**n, "vigencia": est})
    return {
        "ok": True, "expediente": nombre, "total_normas_invocadas": len(items),
        "vigencias": items,
        "nota": ("La vigencia se consultó contra la fuente oficial a la fecha de hoy. "
                 "Si el expediente invoca una norma aplicada a hechos antiguos, recuerde el "
                 "principio de intertemporalidad: el texto aplicable es el vigente al tiempo "
                 "de los hechos o de su ocurrencia, no necesariamente el actual. Contraste con "
                 "el 'historial de la norma' antes de fundamentar."),
    }


def formatear_vigencias(res: dict) -> str:
    if not res.get("ok"):
        return f"ERROR: {res.get('error', 'desconocido')}"
    lineas = [
        f"VIGENCIA DE LAS NORMAS INVOCADAS — expediente '{res['expediente']}'",
        f"Atendido lo anterior, se verificó el estado de vigencia de "
        f"{res['total_normas_invocadas']} norma(s) citada(s).",
        "",
    ]
    for n in res["vigencias"]:
        vig = n.get("vigencia", {})
        estado = vig.get("estado", "DESCONOCIDO")
        sello = {
            "VIGENTE": "[VIGENTE]",
            "DEROGADA": "[⚠ DEROGADA]",
            "REFUNDIDA": "[⚠ REFUNDIDA]",
            "no_verificable": "[SIN IDENTIDAD VERIFICADA]",
        }.get(estado, f"[{estado}]")
        lineas.append(f"• {n['referente']} {sello} — {n['veces_citada']} cita(s)")
        if n["articulos_citados"]:
            lineas.append(f"  Artículos citados: {', '.join(n['articulos_citados'])}")
        if vig.get("derogada_por"):
            lineas.append(f"  Derogada por: {vig['derogada_por']}")
        if vig.get("refundida_por"):
            lineas.append(f"  Refundida por: {vig['refundida_por']}")
        if vig.get("ultima_modificacion"):
            lineas.append(f"  Última modificación: {vig['ultima_modificacion']}"
                          + (f" ({vig['modificada_por']})" if vig.get("modificada_por") else ""))
        if vig.get("url_oficial"):
            lineas.append(f"  Fuente oficial: {vig['url_oficial']}")
        if vig.get("detalle"):
            lineas.append(f"  {vig['detalle']}")
        lineas.append("")
    lineas.append("NOTA INTERTEMPORAL: " + res["nota"])
    return "\n".join(lineas)


# --- Plazos procesales detectados en el expediente -------------------------------

_NUM_PALABRES = {
    "primer": 1, "primero": 1, "segundo": 2, "tercer": 3, "tercero": 3,
    "cuarto": 4, "quinto": 5, "sexto": 6, "séptimo": 7, "septimo": 7,
    "octavo": 8, "noveno": 9, "décimo": 10, "decimo": 10,
}

_RE_PLAZO = re.compile(
    r"\b(?:plazo|t[ée]rmino)\s+de\s+(?P<dias>\d+|" + "|".join(_NUM_PALABRES) + r")"
    r"\s+d[íi]a(s)?"
    r"(?:\s+(?P<tipo>h[áa]biles(?:\s+judiciales)?|corridos))?"
    r"|\bdentro\s+de(?:l\s+)?(?P<dias2>\d+|" + "|".join(_NUM_PALABRES) + r")"
    r"\s+d[íi]a(s)?"
    r"(?:\s+(?P<tipo2>h[áa]biles(?:\s+judiciales)?|corridos))?",
    re.IGNORECASE)

_RE_NOTIFICACION = re.compile(
    r"notificad[oa]\w*\s+(?:el\s+|el\s+d[íi]a\s+)?", re.IGNORECASE)


def _dias_de_coincidencia(m: re.Match) -> tuple[int, str]:
    """Número de días del match; entero o palabra ('sexto' → 6)."""
    crudo = m.group("dias") or m.group("dias2") or ""
    crudo = crudo.lower().strip()
    return _NUM_PALABRES.get(crudo, int(crudo) if crudo.isdigit() else 0), crudo


def _fecha_ancla(plano: str, posicion: int) -> str | None:
    """Fecha de referencia del plazo: la del contexto cercano ANTERIOR a la cita
    ('notificado el 10-08-2026'), o la fecha más próxima anterior en el documento."""
    ventana = plano[max(0, posicion - 500):posicion]
    fechas = [iso for iso, _ in _fechas_de_texto(ventana)]
    return fechas[-1] if fechas else None


def plazos_expediente(nombre: str) -> dict:
    """Plazos procesales detectados en los documentos, computados y con estado
    (vencido / vence en N días / sin fecha de referencia)."""
    from .plazos import computar_plazo, parsear_fecha_cl  # lazy
    from datetime import date as _date
    hoy = _date.today()
    db = get_db()
    row = db._conn.execute("SELECT id FROM expedientes WHERE nombre=?", (nombre.strip(),)).fetchone()
    if not row:
        return {"ok": False, "error": f"No existe expediente '{nombre}'."}
    docs = db._conn.execute(
        "SELECT titulo, texto FROM expediente_docs WHERE expediente_id=?",
        (row["id"],)).fetchall()

    hallazgos = []
    for d in docs:
        plano = re.sub(r"\s+", " ", _normalizar(d["texto"]))
        for m in _RE_PLAZO.finditer(plano):
            dias, crudo = _dias_de_coincidencia(m)
            if not dias:
                continue
            mencion = (m.group("tipo") or m.group("tipo2") or "").lower()
            tipo = "corridos" if "corrido" in mencion else "habiles"
            ini = max(0, m.start() - 120)
            fin = min(len(plano), m.end() + 120)
            fecha_ancla = _fecha_ancla(plano, m.start())
            hallazgo = {
                "documento": d["titulo"],
                "literal": m.group(0).strip(),
                "dias": dias,
                "dias_dicho": crudo,
                "tipo": tipo,
                "contexto": plano[ini:fin].strip(),
                "fecha_referencia": fecha_ancla,
            }
            if fecha_ancla:
                base = parsear_fecha_cl(fecha_ancla)
                if base:
                    computo = computar_plazo(base, dias, tipo)
                    venc = parsear_fecha_cl(computo["vencimiento"])
                    restan = (venc - hoy).days if venc else None
                    hallazgo.update({
                        "vencimiento": computo["vencimiento"],
                        "vencimiento_cl": computo["vencimiento_cl"],
                        "dias_restantes": restan,
                        "estado": ("vencido" if restan < 0 else
                                   "vence hoy" if restan == 0 else
                                   f"vence en {restan} día(s)"),
                        "pasos": computo["pasos"],
                    })
                else:
                    hallazgo["estado"] = "fecha de referencia no interpretable"
            else:
                hallazgo["estado"] = "sin fecha de referencia en el documento"
            hallazgos.append(hallazgo)

    return {
        "ok": True, "expediente": nombre, "hoy": hoy.isoformat(),
        "total_plazos": len(hallazgos), "plazos": hallazgos,
        "nota": ("Los plazos se detectaron por patrón terminológico y se computaron con "
                 "arts. 38/40 CPC y 66 COT. El estado respecto de hoy es informativo: un "
                 "plazo judicial real puede estar interrumpido o suspendido por causales "
                 "que este análisis no conoce (art. 50 CPC, feriado especial, rebeldía)."),
    }


def formatear_plazos_expediente(res: dict) -> str:
    if not res.get("ok"):
        return f"ERROR: {res.get('error', 'desconocido')}"
    lineas = [
        f"PLAZOS DETECTADOS EN EL EXPEDIENTE — '{res['expediente']}'",
        f"Atendido el examen documental (hoy: {res['hoy']}), se advierten "
        f"{res['total_plazos']} plazo(s) procesales mencionados.",
        "",
    ]
    if not res["plazos"]:
        lineas.append("No se detectaron fórmulas de plazo ('plazo de N días', 'dentro del "
                      "sexto día'). Esto no asegura su inexistencia: revise los documentos.")
        return "\n".join(lineas)
    urgentes = [p for p in res["plazos"]
                if isinstance(p.get("dias_restantes"), int) and p["dias_restantes"] <= 5]
    for i, p in enumerate(res["plazos"], 1):
        marca = " 🔴" if p in urgentes and "venc" not in p["estado"] else ""
        lineas.append(f"{i}. \"{p['literal']}\" — {p['dias']} días {p['tipo']}{marca}")
        lineas.append(f"   Documento: «{p['documento']}»")
        lineas.append(f"   Contexto: \"…{p['contexto']}…\"")
        if p.get("vencimiento_cl"):
            lineas.append(f"   Referencia: {p['fecha_referencia']} → Vence: {p['vencimiento_cl']} "
                          f"({p['estado']})")
        else:
            lineas.append(f"   Estado: {p['estado']}")
        lineas.append("")
    if urgentes:
        lineas.append("ATENCIÓN: hay plazo(s) vencidos o a 5 días o menos del vencimiento.")
        lineas.append("")
    lineas.append("NOTA: " + res["nota"])
    return "\n".join(lineas)




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
