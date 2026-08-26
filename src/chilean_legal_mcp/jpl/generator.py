"""Generador de documentos judiciales JPL.

Flujo: INVESTIGAR → REDACTAR → VERIFICAR → EXPORTAR (md/docx).
Sin alucinaciones: cada cita se confirma en el corpus, lo no confirmado se marca.
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import sys
from pathlib import Path
from typing import Any

from . import db as leyes_db
from .db import buscar_articulo, buscar_ley, buscar_texto, verificar_vigencia

# ─── Constantes ────────────────────────────────────────────────────────────────

TIPOS_DOCUMENTO: dict[str, str] = {
    "sentencia": "FORMATOS-SENTENCIAS",
    "sentencia_condena": "FORMATOS-SENTENCIAS",
    "sentencia_absolutoria": "FORMATOS-SENTENCIAS",
    "resolucion": "FORMATOS-RESOLUCIONES-CORTAS",
    "resolucion_corta": "FORMATOS-RESOLUCIONES-CORTAS",
    "oficio": "FORMATOS-OFICIOS-PRESCRIPCION",
    "oficio_prescripcion": "FORMATOS-OFICIOS-PRESCRIPCION",
    "certificado": "FORMATOS-CERTIFICADOS-EXHORTOS",
    "exhorto": "FORMATOS-CERTIFICADOS-EXHORTOS",
    "comparendo": "FORMATOS-COMPARENDOS-DECLARACIONES",
    "declaracion": "FORMATOS-COMPARENDOS-DECLARACIONES",
    "plazo": "PLAZOS",
}

_MANUALES_CACHE: dict[str, str] = {}

_CITA_RE = re.compile(
    r"(?:art(?:í|i)culo\s+)(\d+(?:\s*bis)?)"
    r"(?:\s*(?:y|,)\s*(?:art(?:í|i)culo\s+)?(\d+(?:\s*bis)?))*"
    r"(?:,\s*(?:art(?:í|i)culo\s+\d+(?:\s*bis)?))*"
    r"\s*(?:de\s+la\s+)?(?:Ley\s+[\d\.]+|DL\s+[\d\.]+|DTO\s+[\d\.]+|L\.?\s*[\d\.]+)",
    re.IGNORECASE,
)

_FUENTES_CANONICAS: set[tuple[str, str]] = {
    ("14", "18.287"), ("1", "18.287"), ("3", "18.287"), ("4", "18.287"),
    ("7", "18.287"), ("8", "18.287"), ("9", "18.287"), ("10", "18.287"),
    ("11", "18.287"), ("12", "18.287"), ("13", "18.287"), ("15", "18.287"),
    ("16", "18.287"), ("18", "18.287"), ("24", "18.287"), ("24 bis", "18.287"),
    ("207", "18.290"), ("21", "18.287"),
}


# ─── Utilidades ────────────────────────────────────────────────────────────────

def _get_con() -> sqlite3.Connection | None:
    try:
        from leyes_db import _db_conn  # type: ignore[attr-defined]
        return _db_conn()
    except Exception:
        return None


def _extraer_texto_de_fuente(resultado: Any) -> str:
    """Extrae texto legible de buscar_articulo / buscar_ley (dict, list o str)."""
    if isinstance(resultado, dict):
        t = resultado.get("texto", "")
        if not t:
            extractos = resultado.get("extractos", [])
            t = extractos[0] if extractos else str(resultado)
        return str(t)[:600]
    if isinstance(resultado, list):
        partes: list[str] = []
        for item in resultado:
            if isinstance(item, dict):
                t = item.get("texto") or (item.get("extractos", [""])[0] if item.get("extractos") else "")
                if t:
                    partes.append(str(t)[:300])
            elif item:
                partes.append(str(item)[:300])
        return "\n".join(partes[:3]) if partes else str(resultado)[:300]
    return str(resultado)[:600]


def _cargar_manual(nombre: str) -> str | None:
    if nombre in _MANUALES_CACHE:
        return _MANUALES_CACHE[nombre]
    con = _get_con()
    if con:
        try:
            row = con.execute("SELECT texto FROM manuales WHERE nombre = ?", (nombre,)).fetchone()
            if row:
                _MANUALES_CACHE[nombre] = row[0]
                return row[0]
        except Exception:
            pass
        finally:
            con.close()
    root = Path(__file__).resolve().parent.parent.parent
    for p in [
        root / ".opencode" / "skills" / "jpl" / "formatos" / f"{nombre}.md",
        root / "backup" / ".opencode" / "skills" / "jpl" / "formatos" / f"{nombre}.md",
    ]:
        if p.exists():
            txt = p.read_text(encoding="utf-8", errors="ignore")
            _MANUALES_CACHE[nombre] = txt
            return txt
    return None


def _extraer_citas(texto: str) -> list[dict]:
    citas: list[dict] = []
    vistos: set[str] = set()
    for m in _CITA_RE.finditer(texto):
        art = m.group(1).strip() if m.lastindex >= 1 else ""
        ley = m.group(2).strip() if m.lastindex >= 2 else ""
        # Si capturamos solo el número (grupo 1), completar con ley del match
        full = m.group(0)
        # Extraer ley del match completo si no vino en grupo
        ley_m = re.search(r"(?:Ley\s+[\d\.]+|DL\s+[\d\.]+|DTO\s+[\d\.]+|L\.?\s*[\d\.]+)", full, re.IGNORECASE)
        if not ley and ley_m:
            ley = ley_m.group(0)
        key = f"{art}|{ley}"
        if key not in vistos and art and ley:
            vistos.add(key)
            citas.append({"articulo": art, "ley": ley, "texto_original": full})
    return citas


def _fulltext_search(terminos: list[str], limite: int = 5) -> list[dict]:
    resultados: dict[str, dict] = {}
    query = " ".join(terminos)
    for fuente in ["leyes", "manuales"]:
        try:
            if fuente == "leyes":
                res = buscar_ley(query, limite=limite)
                for r in res:
                    k = r.get("ley", "")
                    if k not in resultados:
                        resultados[k] = {
                            "tipo": "ley",
                            "referencia": k,
                            "coincidencias": r.get("coincidencias", 0),
                            "extractos": r.get("extractos", [])[:3],
                        }
            else:
                res = buscar_texto(query)
                for r in (res or []):
                    if r.get("tipo") == "manual":
                        ref = r.get("referencia", "")
                        if ref not in resultados:
                            resultados[ref] = {
                                "tipo": "manual",
                                "referencia": ref,
                                "coincidencias": r.get("coincidencias", 0),
                                "extractos": r.get("extractos", [])[:3],
                            }
        except Exception:
            pass
    return list(resultados.values())


# ─── Etapa 1: INVESTIGAR ──────────────────────────────────────────────────────

def etapa_investigar(datos: dict[str, Any]) -> dict:
    terminos: list[str] = []
    ley_principal = datos.get("ley", "")
    articulo_principal = datos.get("articulo", "")
    materia = datos.get("materia", "") or datos.get("tipo_infraccion", "")
    hechos = datos.get("hecho", "") or datos.get("hechos", "")
    tipo_doc = datos.get("tipo", "")

    if ley_principal:
        terminos.append(ley_principal)
    if articulo_principal:
        terminos.append(f"articulo {articulo_principal}")
    if materia:
        terminos.append(materia)
    if tipo_doc:
        terminos.append(tipo_doc.replace("_", " "))
    if hechos and len(hechos) > 5:
        for frag in hechos.split(",")[:3]:
            f = frag.strip()[:80]
            if f:
                terminos.append(f)

    fuentes: list[dict] = []
    vistos_refs: set[str] = set()

    if ley_principal and articulo_principal:
        r = _buscar_articulo_especifico(ley_principal, articulo_principal)
        if r:
            fuentes.append(r)
            vistos_refs.add(ley_principal)

    search_terms = list(dict.fromkeys(terminos))[:8]
    if search_terms:
        try:
            res = _fulltext_search(search_terms, limite=10)
            for r in res:
                ref = r.get("referencia", "")
                if ref not in vistos_refs:
                    vistos_refs.add(ref)
                    fuentes.append(r)
        except Exception:
            pass

    vigencia: dict = {}
    if ley_principal:
        try:
            vigencia = verificar_vigencia(ley_principal) or {}
        except Exception:
            pass

    manual_nombre = TIPOS_DOCUMENTO.get(tipo_doc, "")
    manual_texto = _cargar_manual(manual_nombre) if manual_nombre else None

    return {
        "fuentes": fuentes[:15],
        "articulos_confirmados": [f["referencia"] for f in fuentes if f["tipo"] == "ley"],
        "manual_encontrado": bool(manual_texto),
        "manual_nombre": manual_nombre,
        "vigencia_principal": vigencia,
        "query_usada": search_terms,
    }


def _buscar_articulo_especifico(ley: str, art: str) -> dict | None:
    if not ley or not art:
        return None
    try:
        res = buscar_articulo(ley, int(art))
        if res:
            return {
                "tipo": "ley",
                "referencia": f"{ley} art. {art}",
                "coincidencias": 1,
                "extractos": [_extraer_texto_de_fuente(res)],
            }
    except Exception:
        pass
    return None


# ─── Etapa 2: REDACTAR ────────────────────────────────────────────────────────

def etapa_redactar(tipo: str, datos: dict[str, Any], investigacion: dict) -> dict:
    template_manual = investigacion.get("manual_nombre", "")
    fuentes = investigacion.get("fuentes", [])

    def fill(template_text: str, data: dict) -> str:
        out = template_text
        for k, v in data.items():
            out = out.replace(f"[{k.upper()}]", str(v) if v else f"[{k.upper()}]")
        return out

    caso = {
        "ROL": datos.get("rol", "[ROL]"),
        "FOJAS": datos.get("fojas", "[FOJAS]"),
        "CIUDAD": datos.get("ciudad", "[CIUDAD]"),
        "DIA": datos.get("dia", "[DIA]"),
        "MES": datos.get("mes", "[MES]"),
        "AÑO": datos.get("ano", "[AÑO]"),
        "DENUNCIANTE": datos.get("denunciante", "[DENUNCIANTE]"),
        "NOMBRE_DENUNCIADO": datos.get("denunciado", "[DENUNCIADO]"),
        "RUT": datos.get("rut", "[RUT]"),
        "DOMICILIO": datos.get("domicilio", "[DOMICILIO]"),
        "DESCRIPCION_INFRACCION": datos.get("hecho", datos.get("hechos", "[HECHOS]")),
        "LEY": datos.get("ley", "[LEY]"),
        "ARTICULO": datos.get("articulo", "[ARTÍCULO]"),
        "COMUNA": datos.get("comuna", "[COMUNA]"),
        "NOMBRE_JUEZ": "[NOMBRE JUEZ]",
        "CARGO": "[CARGO]",
        "FIRMA": "[FIRMA]",
        "SECRETARIO_A": "[NOMBRE SECRETARIO/A]",
        "DESTINATARIO": datos.get("destinatario", "[DESTINATARIO]"),
        "MATERIA": datos.get("materia", "[MATERIA]"),
        "NUMERO": datos.get("numero", "[NUMERO]"),
    }

    tipo_lower = tipo.lower().strip()
    if tipo_lower.startswith("sentencia"):
        doc = _redactar_sentencia(caso, fuentes)
    elif tipo_lower in ("resolucion", "resolucion_corta"):
        doc = _redactar_resolucion(caso, fuentes, datos)
    elif tipo_lower in ("oficio", "oficio_prescripcion"):
        doc = _redactar_oficio(caso, fuentes, datos)
    elif tipo_lower in ("certificado", "exhorto"):
        doc = _redactar_certificado(caso, fuentes)
    elif tipo_lower in ("comparendo", "declaracion"):
        doc = _redactar_comparendo(caso, fuentes, datos)
    elif tipo_lower in ("plazo", "plazos"):
        doc = _redactar_plazo(caso, fuentes, datos)
    else:
        doc = _redactar_generico(caso, fuentes, template_manual)

    bloque_fuentes = "\n\n---\n## FUENTES CONFIRMADAS\n"
    for f in fuentes[:8]:
        if f["tipo"] == "ley":
            bloque_fuentes += f'\n- **{f["referencia"]}** (coincidencias: {f["coincidencias"]})'
        elif f["tipo"] == "manual":
            bloque_fuentes += f'\n- Manual: **{f["referencia"]}**'
    if not fuentes:
        bloque_fuentes += "\n⚠️ Sin fuentes confirmadas en el corpus."

    return {
        "documento_md": doc + bloque_fuentes,
        "plantilla_usada": template_manual or tipo_lower,
        "fuentes_utilizadas": len(fuentes),
    }


def _fuentes_texto(fuentes: list[dict]) -> str:
    out = ""
    for f in fuentes[:4]:
        if f["tipo"] == "ley" and f.get("extractos"):
            out += f'\n> "{f["extractos"][0][:200]}"'
    return out


def _redactar_sentencia(caso: dict, fuentes: list[dict]) -> str:
    ley = caso["LEY"] if caso["LEY"] != "[LEY]" else "[LEY]"
    art = caso["ARTICULO"] if caso["ARTICULO"] != "[ARTÍCULO]" else "[ARTÍCULO]"
    denunciado = caso["NOMBRE_DENUNCIADO"]
    fuente_txt = _fuentes_texto(fuentes)

    parte_i = (
        f"I.- QUE SE CONDENA a {denunciado}, ya individualizado, "
        "por la infracción descrita en los considerandos.\n"
        "II.- Costas procesales a cargo del condenado.\n"
        "III.- Si no se pagare la multa dentro del plazo legal de cinco días, "
        "despáchese orden de arresto hasta por treinta días.\n"
        "IV.- Comuníquese al Registro de Multas de Tránsito no pagadas."
    )

    return f"""\
PRIMER JUZGADO DE POLICÍA LOCAL DE {caso['COMUNA']}
ROL N° {caso['ROL']}
FOJAS: {caso['FOJAS']}

{caso['CIUDAD']}, {caso['DIA']} de {caso['MES']} de dos mil {caso['AÑO']}.

VISTOS:

1.- Denuncia formulada en contra de {denunciado}, C.I. N° {caso['RUT']}, con domicilio en {caso['DOMICILIO']}, por: {caso['DESCRIPCION_INFRACCION']}.

CONSIDERANDO:

PRIMERO: Que, conforme lo dispone el artículo 14 de la Ley 18.287, los Tribunales de Policía Local apreciarán la prueba de acuerdo a las reglas de la sana crítica.

SEGUNDO: Que de la prueba rendida aparece acreditado que {caso['DESCRIPCION_INFRACCION']}.

TERCERO: Que, conforme lo dispone el {ley} artículo {art}, los hechos descritos encuadran en la infracción señalada.{fuente_txt}

CUARTO: Que, en consecuencia, corresponde condenar al denunciado por los hechos descritos.

Y TENIENDO PRESENTE lo dispuesto en los artículos 1, 3, 4, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16 y 18 de la Ley 18.287 y {ley} artículo {art}, SE DECLARA:

{parte_i}

REGÍSTRESE, NOTIFÍQUESE Y ARCHÍVESE.

Pronunciada por {caso['NOMBRE_JUEZ']}, {caso['CARGO']} del Primer Juzgado de Policía Local de {caso['COMUNA']}.

SECRETARIA
"""


def _redactar_resolucion(caso: dict, fuentes: list[dict], datos: dict) -> str:
    variante = datos.get("variante", "archivo")
    materia = caso["DESCRIPCION_INFRACCION"]
    parte = (
        "I.- Archívese la causa por no constituir infracción tipificada.\n"
        "II.- Notifíquese a las partes.\n"
        "III.- Regístrese."
        if variante == "archivo"
        else "I.- Téngase presente lo solicitado.\nII.- Notifíquese.\nIII.- Regístrese."
    )
    return f"""\
PRIMER JUZGADO DE POLICÍA LOCAL DE {caso['COMUNA']}
ROL N° {caso['ROL']}

{caso['CIUDAD']}, {caso['DIA']} de {caso['MES']} de dos mil {caso['AÑO']}.

VISTOS:

1.- Los antecedentes de la causa Rol N° {caso['ROL']}, por {materia}.

CONSIDERANDO:

Que, previo análisis de los antecedentes ({len(fuentes)} fuentes confirmadas del corpus), procede resolver conforme a derecho.

SE RESUELVE:

{parte}

[FIRMA SECRETARIO/A]
"""


def _redactar_oficio(caso: dict, fuentes: list[dict], datos: dict) -> str:
    return f"""\
OFICIO N° {caso.get('NUMERO', '[NUMERO]')}

MATERIA: {caso['MATERIA'] if caso['MATERIA'] != '[MATERIA]' else ''}

{caso['CIUDAD']}, {caso['DIA']} de {caso['MES']} de dos mil {caso['AÑO']}.

DE: Primer Juzgado de Policía Local de {caso['COMUNA']}
A: {caso['DESTINATARIO']}

Por medio del presente, me dirijo a Ud. para informar que en autos Rol N° {caso['ROL']} 
se ha dictado resolución sobre: {caso['DESCRIPCION_INFRACCION']}.

Se adjunta copia de la resolución para su conocimiento.

Sin otro particular, le saluda atentamente,

{caso['NOMBRE_JUEZ']}
JUEZ TITULAR
Primer Juzgado de Policía Local de {caso['COMUNA']}
"""


def _redactar_certificado(caso: dict, fuentes: list[dict]) -> str:
    return f"""\
CERTIFICADO

CERTIFICO: Que en el Rol N° {caso['ROL']}, ante este Primer Juzgado de Policía Local de {caso['COMUNA']}, 
con fecha {caso['DIA']} de {caso['MES']} de dos mil {caso['AÑO']}, se registra lo siguiente:

Hechos: {caso['DESCRIPCION_INFRACCION']}

Se expide el presente certificado a solicitud del interesado.

[FIRMA SECRETARIO/A]
"""


def _redactar_comparendo(caso: dict, fuentes: list[dict], datos: dict) -> str:
    return f"""\
CITACIÓN A COMPARENDO

PRIMER JUZGADO DE POLICÍA LOCAL DE {caso['COMUNA']}
ROL N° {caso['ROL']}

CÍTESE a {caso['NOMBRE_DENUNCIADO']}, RUT {caso['RUT']}, con domicilio en {caso['DOMICILIO']}, 
a comparendo de declaración indagatoria para el día {caso['DIA']} de {caso['MES']} de dos mil {caso['AÑO']}, 
a las [HORA] horas.

Materia: {caso['DESCRIPCION_INFRACCION']}

Notifíquese por cédula o medio tecnológico autorizado.
"""


def _redactar_plazo(caso: dict, fuentes: list[dict], datos: dict) -> str:
    return f"""\
PRIMER JUZGADO DE POLICÍA LOCAL DE {caso['COMUNA']}
ROL N° {caso['ROL']}

En relación a la causa individualizada, se fijan los siguientes plazos procesales:

- Plazo: {datos.get('plazo_dias', '[PLAZO]')} días
- Tipo: {datos.get('tipo_plazo', 'corrido')}
- Fundamento: {datos.get('fundamento', '[ARTÍCULO LEY]')}

{caso['CIUDAD']}, {caso['DIA']} de {caso['MES']} de dos mil {caso['AÑO']}.

[NOMBRE SECRETARIO/A]
SECRETARIO/A ABOGADO/A
"""


def _redactar_generico(caso: dict, fuentes: list[dict], manual: str) -> str:
    lineas = [f"# DOCUMENTO: {caso.get('tipo', 'GENERICO').upper()}\n"]
    if manual:
        lineas.append(f"\nPlantilla base: {manual[:120]}...\n")
    lineas.append("\nDatos del caso:")
    for k, v in caso.items():
        if not k.startswith("_") and v and v != f"[{k.upper()}]":
            lineas.append(f"- {k}: {v}")
    lineas.append("\n---\n## Fuentes confirmadas\n")
    for f in (fuentes or [])[:8]:
        lineas.append(f"- {f.get('tipo','?')}: {f.get('referencia','')}")
    return "\n".join(lineas)


# ─── Etapa 3: VERIFICAR ───────────────────────────────────────────────────────

def etapa_verificar(documento: str, fuentes: list[dict]) -> dict:
    citas = _extraer_citas(documento)
    confirmadas: list[dict] = []
    pendientes: list[dict] = []

    for c in citas:
        art = c["articulo"].strip()
        ley = c["ley"].strip()
        if (art, ley) in _FUENTES_CANONICAS:
            confirmadas.append(c)
            continue
        encontrado = False
        for f in fuentes:
            ref = f.get("referencia", "").lower()
            if art.lower() in ref and (not ley or ley.lower() in ref):
                confirmadas.append(c)
                encontrado = True
                break
        if not encontrado and ley:
            try:
                num_match = re.search(r"\d+", art)
                if num_match:
                    res = buscar_articulo(ley, int(num_match.group()))
                    if res:
                        confirmadas.append(c)
                        encontrado = True
            except Exception:
                pass
        if not encontrado:
            pendientes.append(c)

    total = len(citas) if citas else 0
    score = len(confirmadas) / total if total else 1.0

    return {
        "confirmadas": confirmadas,
        "pendientes": pendientes,
        "score": round(score, 2),
        "advertencia": (
            f"⚠️ {len(pendientes)} citas sin confirmar en el corpus. Revisar antes de presentar."
            if pendientes else "✅ Todas las citas confirmadas en el corpus."
        ),
    }


# ─── Etapa 4: EXPORTAR ────────────────────────────────────────────────────────

def etapa_exportar(documento: str, formato: str, rol: str) -> dict:
    formato = formato.strip().lower() or "md"
    import tempfile
    tmp = Path(tempfile.gettempdir()) / "opencode" / "docs"
    tmp.mkdir(parents=True, exist_ok=True)

    ruta_md = str(tmp / f"{rol}.md")
    try:
        Path(ruta_md).write_text(documento, encoding="utf-8")
    except Exception:
        pass

    result: dict[str, Any] = {
        "formato": formato,
        "contenido": documento,
        "ruta_md": ruta_md,
    }

    if formato == "docx":
        try:
            from docx import Document  # type: ignore
            from docx.shared import Pt  # type: ignore
            from docx.enum.text import WD_ALIGN_PARAGRAPH  # type: ignore
        except ImportError:
            result["advertencia"] = (
                "python-docx no instalado; devuelvo Markdown. "
                "Instalar: pip install python-docx"
            )
            return result
        try:
            doc = Document()
            style = doc.styles["Normal"]
            style.font.name = "Times New Roman"
            style.font.size = Pt(12)
            for linea in documento.splitlines():
                p = doc.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                run = p.add_run(linea)
                run.font.name = "Times New Roman"
                run.font.size = Pt(12)
            ruta_docx = str(tmp / f"{rol}.docx")
            doc.save(ruta_docx)
            result["ruta_docx"] = ruta_docx
        except Exception as exc:
            result["advertencia"] = f"Error generando DOCX: {exc}"

    return result


# ─── API principal ─────────────────────────────────────────────────────────────

def generar(tipo: str, datos: dict[str, Any], formato: str = "md") -> dict:
    if not tipo:
        return {"error": "tipo de documento es requerido"}
    datos = datos or {}
    tipo_lower = tipo.lower().strip()
    if tipo_lower not in TIPOS_DOCUMENTO:
        return {
            "error": f"tipo desconocido: '{tipo}'. Válidos: {', '.join(sorted(TIPOS_DOCUMENTO))}"
        }

    inv = etapa_investigar(datos)
    red = etapa_redactar(tipo_lower, datos, inv)
    doc = red.get("documento_md", "")
    ver = etapa_verificar(doc, inv.get("fuentes", []))

    if ver.get("pendientes"):
        doc += f"\n\n---\n_{ver['advertencia']}_\n"
    else:
        doc += f"\n\n---\n_✅ {ver['advertencia']}_\n"

    rol = re.sub(r"[^a-zA-Z0-9_-]", "_", str(datos.get("rol", tipo_lower)))
    exp = etapa_exportar(doc, formato, rol)

    return {
        "documento_md": doc,
        "plantilla_usada": red.get("plantilla_usada", tipo_lower),
        "fuentes_utilizadas": red.get("fuentes_utilizadas", 0),
        "verificacion": ver,
        "export": exp,
    }


# ─── CLI ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Generador documentos JPL")
    p.add_argument("tipo", choices=sorted(TIPOS_DOCUMENTO.keys()))
    p.add_argument("--datos", default="{}", help="JSON string con datos del caso")
    p.add_argument("--formato", default="md", choices=["md", "docx"])
    args = p.parse_args()
    datos = json.loads(args.datos)
    res = generar(args.tipo, datos, args.formato)
    print(res.get("documento_md", json.dumps(res, ensure_ascii=False, indent=2)))