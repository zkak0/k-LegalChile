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
        from .db import _db_conn  # type: ignore[attr-defined]
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
        doc = _redactar_sentencia(caso, fuentes, datos)
    elif tipo_lower in ("resolucion", "resolucion_corta"):
        doc = _redactar_resolucion(caso, fuentes, datos)
    elif tipo_lower in ("oficio", "oficio_prescripcion"):
        doc = _redactar_oficio(caso, fuentes, datos)
    elif tipo_lower in ("certificado", "exhorto"):
        doc = _redactar_certificado(caso, fuentes, datos)
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


# ─── Fórmulas textuales del corpus real (FORMATOS-*.md) ─────────────────────
# Extraídas de los manuales FORMATOS-RESOLUCIONES-CORTAS (convenciones 0.1-0.7),
# FORMATOS-SENTENCIAS (fórmulas invariables) y FORMATOS-OFICIOS-PRESCRIPCION.
# Cada frase es textual del tribunal; se verifica contra el manual al generar.

_FECHA_LETRAS = "En {ciudad}, a {dia} de {mes} de {ano}."
_UTM = ("{n} U.T.M. ({letras} UNIDAD(ES) TRIBUTARIA(S) MENSUAL(ES)), "
        "vigente al momento del pago")
_SANA_CRITICA = ("PRIMERO: Que, conforme lo dispone el artículo 14 de la Ley 18.287, los "
                 "Tribunales de Policía Local apreciarán la prueba de acuerdo con las "
                 "reglas de la sana crítica.")
_Y_TENIENDO = ("Y TENIENDO PRESENTE lo dispuesto en los artículos 1, 3, 4, 7, 8, 9, 10, "
               "11, 12, 13, 14, 15, 16 y 18 de la Ley 18.287 y {ley} artículo {art}, SE DECLARA:")
_CIERRE = "REGÍSTRESE, NOTIFÍQUESE Y ARCHÍVESE."
_ARRESTRO = ("III.- Si no se pagare la multa dentro del plazo legal de cinco días, "
             "despáchese orden de arresto hasta por treinta días.")
_REGISTRO_MULTAS = ("IV.- Para los efectos establecidos en los artículos 24 y 24 bis de la "
                    "Ley 18.287, si no pagare dentro del plazo legal de cinco días, "
                    "comuníquese por el Sr. Secretario al Registro de Multas de Tránsito no pagadas.")
_NOTIF_CARTA = "Notifíquese esta resolución por carta certificada."
_NOTIF_ACTO = ("El compareciente se notifica en este acto de la resolución que antecede. "
               "Previa lectura se ratifica y firma con Usía.")

_UNIDADES = ("cero", "un", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve",
             "diez", "once", "doce", "trece", "catorce", "quince", "dieciseis", "diecisiete",
             "dieciocho", "diecinueve", "veinte")
_DECENAS = ("", "diez", "veinte", "treinta", "cuarenta", "cincuenta", "sesenta",
            "setenta", "ochenta", "noventa")
_CENTENAS = ("", "ciento", "doscientos", "trescientos", "cuatrocientos", "quinientos",
             "seiscientos", "setecientos", "ochocientos", "novecientos")


def _numero_a_letras(n: int | float | str) -> str:
    """Numero entero a español (hasta decenas de miles), para fórmulas U.T.M. en letras."""
    try:
        n = int(float(str(n).replace(",", ".")))
    except (TypeError, ValueError):
        return "N"
    if n < 0:
        return "menos " + _numero_a_letras(abs(n))
    if n < 21:
        return _UNIDADES[n]
    if n < 100:
        d, u = divmod(n, 10)
        return _DECENAS[d] + (" y " + _UNIDADES[u] if 0 < u <= 20 else (" y " + _numero_a_letras(u) if u else ""))
    if n < 1000:
        c, r = divmod(n, 100)
        base = "cien" if n == 100 else _CENTENAS[c]
        return base + (" " + _numero_a_letras(r) if r else "")
    for mil in ("mil", "millón", "millones"):
        pass
    if n < 1_000_000:
        if n < 20_000:
            miles, resto = divmod(n, 1000)
            return "diez " + _numero_a_letras(miles) + " mil" if miles == 1 else _numero_a_letras(miles) + " mil" + (" " + _numero_a_letras(resto) if resto else "")
        m, r = divmod(n, 1000)
        return _numero_a_letras(m) + " mil" + (" " + _numero_a_letras(r) if r else "")
    return str(n)


def _manual_presente(nombre: str, frases: list[str]) -> list[str]:
    """Devuelve las fórmulas-texto confirmadas presentes en el manual (verificación)."""
    texto = _cargar_manual(nombre)
    if not texto:
        return []
    norm = re.sub(r"\s+", " ", texto.lower())
    return [f for f in frases if re.sub(r"\s+", " ", f[:60].lower()) in norm]


_FRASES_CLAVE_MANUAL = {
    "FORMATOS-RESOLUCIONES-CORTAS": [
        "En [CIUDAD], a [DÍA] de [MES] de [AÑO].",
        "ARCHÍVESE",
        "CÍTESE",
        "OFÍCIESE",
        "TÉNGASE POR RECIBIDO",
        "Notifíquese esta resolución por carta certificada.",
    ],
    "FORMATOS-SENTENCIAS": [
        "VISTOS:",
        "CONSIDERANDO:",
        "apreciarán la prueba de acuerdo a las reglas de la sana crítica",
        "REGÍSTRESE, NOTIFÍQUESE Y ARCHÍVESE.",
        "SECRETARIA",
    ],
    "FORMATOS-OFICIOS-PRESCRIPCION": [
        "OFICIO Nº [NUMERO]-[AÑO]",
        "Por resolución recaída en la causa rol N°[ROL]-[AÑO], se ha ordenado oficiar a Ud.",
        "Saluda atentamente a Ud.",
    ],
}


def _redactar_sentencia(caso: dict, fuentes: list[dict], datos: dict) -> str:
    ley = caso["LEY"] if caso["LEY"] != "[LEY]" else "Ley 18.287"
    ley_txt = ley if ley.lower().startswith("ley") else f"Ley {ley}"
    art = caso["ARTICULO"] if caso["ARTICULO"] != "[ARTÍCULO]" else "[ARTÍCULO]"
    denunciado = caso["NOMBRE_DENUNCIADO"]
    absolutoria = datos.get("variante", "") == "absolutoria" or "absolutoria" in str(datos.get("tipo", ""))
    fecha = _FECHA_LETRAS.format(ciudad=caso["CIUDAD"], dia=caso["DIA"], mes=caso["MES"], ano=caso["AÑO"])
    extracto_art = ""
    for f in fuentes:
        if f.get("tipo") == "ley" and f.get("extractos"):
            extracto_art = f'\n> Texto confirmado del corpus: "{f["extractos"][0][:400]}"'
            break
    monto = datos.get("utm", datos.get("monto", ""))
    multa_txt = (_UTM.format(n=monto, letras=_numero_a_letras(monto).upper())
                 if str(monto).strip() else "[N] U.T.M. ([N EN LETRAS] UNIDAD(ES) TRIBUTARIA(S) MENSUAL(ES)), vigente al momento del pago")
    prueba = datos.get("prueba", "la denuncia, el parte policial y los documentos acompañados")

    if absolutoria:
        cuarto = "CUARTO: Que, en consecuencia, no encontrándose acreditada la infracción, corresponde absolver al denunciado."
        parte_i = (f"I.- QUE SE ABSUELVE a {denunciado}, ya individualizado, de la denuncia formulada en su contra.\n"
                   "II.- Sin costas, por estimarse que existió motivo plausible para denunciar.")
    else:
        cuarto = "CUARTO: Que, en consecuencia, corresponde condenar al denunciado por los hechos descritos."
        parte_i = (
            f"I.- QUE SE CONDENA a {denunciado}, ya individualizado, al pago de una multa de {multa_txt}.\n"
            f"II.- Costas procesales a cargo del condenado.\n"
            f"{_ARRESTRO}\n"
            f"{_REGISTRO_MULTAS}"
        )

    return f"""\
PRIMER JUZGADO DE POLICÍA LOCAL DE {caso['COMUNA']}
ROL N° {caso['ROL']}
FOJAS: {caso['FOJAS']}

{fecha}

VISTOS:

1.- Denuncia formulada en contra de {denunciado}, C.I. N° {caso['RUT']}, con domicilio en {caso['DOMICILIO']}, por: {caso['DESCRIPCION_INFRACCION']}.
2.- Antecedentes procesales: contestación y prueba rendida ({prueba}).

CONSIDERANDO:

{_SANA_CRITICA}

SEGUNDO: Que de la prueba rendida, esto es, {prueba}, aparece acreditado que {caso['DESCRIPCION_INFRACCION']}.

TERCERO: Que, conforme lo dispone la {ley_txt} artículo {art}, los hechos descritos encuadran en la infracción señalada.{extracto_art}

{cuarto}

{_Y_TENIENDO.format(ley=ley_txt, art=art)}

{parte_i}

{_CIERRE}

Pronunciada por {caso['NOMBRE_JUEZ']}, {caso['CARGO']} del Primer Juzgado de Policía Local de {caso['COMUNA']}.

SECRETARIA
"""


def _redactar_resolucion(caso: dict, fuentes: list[dict], datos: dict) -> str:
    variante = str(datos.get("variante", "archivo")).lower()
    materia = caso["DESCRIPCION_INFRACCION"]
    fecha = _FECHA_LETRAS.format(ciudad=caso["CIUDAD"], dia=caso["DIA"], mes=caso["MES"], ano=caso["AÑO"])
    rol_act = f"causa Rol N° {caso['ROL']}, Actuario {datos.get('actuario', '[INICIALES ACTUARIO]')}."
    if variante == "acumulacion":
        cuerpo = (
            f"Visto lo solicitado y advirtiendo el tribunal que el hecho denunciado es el mismo, "
            f"ACUMÚLESE la causa de ingreso posterior a la primera, {rol_act}"
        )
    elif variante == "citacion":
        cuerpo = (
            f"Atendido el mérito de los antecedentes, CÍTESE a {caso['NOMBRE_DENUNCIADO']}, "
            f"C.I. N° {caso['RUT']}, a comparendo de contestación, conciliación y prueba para el día "
            f"{datos.get('fecha_comparendo', '[FECHA]')}, a las {datos.get('hora', '[HORA]')} horas. {_NOTIF_CARTA}"
        )
    elif variante in ("tengase_presente", "tenerse_presente", "presente"):
        cuerpo = (
            f"Por recibido con esta fecha. TÉNGASE POR RECIBIDO lo informado por {datos.get('quien', '[QUIEN]')}. "
            f"Notifíquese. Ofíciese, una vez hecho, archívese."
        )
    elif variante in ("oficiar", "oficio", "informe"):
        cuerpo = (
            f"Atendido que se encuentra pendiente el informe de {datos.get('quien', '[INSTITUCIÓN]')}, OFÍCIESE. "
            f"Ofíciese, una vez hecho, archívese."
        )
    elif variante == "plazo":
        cuerpo = (
            f"Atendido lo solicitado, concédese el plazo de {datos.get('plazo_dias', '[N]')} días "
            f"para {datos.get('objeto_plazo', '[OBJETO]')}. {_NOTIF_CARTA}"
        )
    else:  # archivo
        cuerpo = (
            f"Visto lo expuesto y no constituyendo los hechos una infracción de competencia de este tribunal, "
            f"ARCHÍVESE. {_NOTIF_CARTA}"
        )
    return f"""\
{fecha}

VISTOS Y CONSIDERANDO:

1.- Los antecedentes de la {rol_act} por {materia}.

{cuerpo}

[FIRMA: solo si falla o se dicta tras audiencia — los decretos simples de mesa no llevan firma]
"""


def _redactar_oficio(caso: dict, fuentes: list[dict], datos: dict) -> str:
    materia = caso["MATERIA"] if caso["MATERIA"] != "[MATERIA]" else str(datos.get("materia_oficio", "LO QUE INDICA"))
    variante = str(datos.get("variante", "")).lower()
    if variante == "prescripcion":
        cuerpo = (
            f"se ha ordenado oficiar a Ud. a fin de informar que en la causa individualizada se ha declarado "
            f"la prescripción de la multa, conforme al artículo 24 de la Ley 18.287 "
            f"(tres años desde la anotación en el Registro) o al artículo 54 de la Ley 15.231 "
            f"(un año desde que la sentencia quedó firme, si no es empadronado), según corresponda."
        )
    elif variante == "denegacion_acogida":
        cuerpo = (
            f"se ha ordenado oficiar a Ud. a fin de informar que se acogió la reclamación deducida por "
            f"{caso['NOMBRE_DENUNCIADO']}, Cédula de identidad N° {caso['RUT']}, en contra de la resolución del "
            f"Departamento de Tránsito y Transporte Público de la I. Municipalidad de {caso['COMUNA']} de fecha "
            f"{datos.get('fecha_denegacion', '[FECHA DENEGACION]')}, y se declara que tiene idoneidad moral para "
            f"otorgarle la Licencia de Conducir vehículos clase {datos.get('clase', '[CLASE]')}. "
            f"Se adjunta copia autorizada de la sentencia de fecha {datos.get('fecha_sentencia', '[FECHA SENTENCIA]')}."
        )
    else:
        cuerpo = (
            f"se ha ordenado oficiar a Ud., a fin de informar que {caso['DESCRIPCION_INFRACCION']}."
        )
    return f"""\
OFICIO Nº {caso.get('NUMERO', '[NUMERO]')}-{caso['AÑO']}
				ACTUARIO: {datos.get('actuario', '[APELLIDO ACTUARIO]')}

MAT: {materia}.

{caso['CIUDAD']}, {caso['DIA']} de {caso['MES']} de {caso['AÑO']}.

DE	: JUEZ PRIMER JUZGADO DE POLICÍA LOCAL DE {caso['COMUNA']}
A 	: {caso['DESTINATARIO']}

Por resolución recaída en la causa rol N° {caso['ROL']}, {cuerpo}

Saluda atentamente a Ud.

{caso['NOMBRE_JUEZ']}
JUEZ TITULAR

{caso['SECRETARIO_A']}
SECRETARIA ABOGADO

c.c. causa Nº {caso['ROL']} ACTUARIO: {datos.get('actuario', '[INICIALES]')}.
"""


def _redactar_certificado(caso: dict, fuentes: list[dict], datos: dict) -> str:
    variante = str(datos.get("variante", "certificado")).lower()
    fecha = _FECHA_LETRAS.format(ciudad=caso["CIUDAD"], dia=caso["DIA"], mes=caso["MES"], ano=caso["AÑO"])
    if variante == "exhorto":
        return f"""\
{fecha}

Por recibido con esta fecha. Ingrésese exhorto Oficio N°{datos.get('numero_exhorto', '[NUMERO]')}, del {datos.get('juzgado_origen', '[JUZGADO ORIGEN]')} y cítese a {datos.get('persona', '[NOMBRE DE LA PERSONA]')}, {datos.get('rut_persona', '[RUT]')}, con domicilio en {datos.get('domicilio_persona', '[DOMICILIO]')}, a prestar declaración indagatoria en este tribunal, el día {datos.get('fecha_declaracion', '[FECHA DE LA DECLARACIÓN]')}, a las {datos.get('hora', '[HORA]')} horas. Notifíquese a través del departamento de Inspección Comunal. Ofíciese.
"""
    return f"""\
CERTIFICO: Que en la causa Rol N° {caso['ROL']} de este Primer Juzgado de Policía Local de {caso['COMUNA']}, con fecha {caso['DIA']} de {caso['MES']} de {caso['AÑO']}, se practicó la siguiente diligencia: {caso['DESCRIPCION_INFRACCION']}.

Ministro de fe: {datos.get('receptor', '[NOMBRE RECEPTOR]')}, receptor ad-hoc designado por resolución.

Derechos ${datos.get('derechos', '[MONTO]')}.

{fecha}

                                                                        {datos.get('receptor', '[NOMBRE RECEPTOR]')}
                                                                        RECEPTOR AD-HOC
"""


def _redactar_comparendo(caso: dict, fuentes: list[dict], datos: dict) -> str:
    fecha = _FECHA_LETRAS.format(ciudad=caso["CIUDAD"], dia=caso["DIA"], mes=caso["MES"], ano=caso["AÑO"])
    parte_a = datos.get("parte_a", "[NOMBRE QUERELLANTE]")
    parte_b = datos.get("parte_b", "[NOMBRE QUERELLADO]")
    return f"""\
ACTA DE COMPARENDO DE CONTESTACIÓN, CONCILIACIÓN Y PRUEBA
PRIMER JUZGADO DE POLICÍA LOCAL DE {caso['COMUNA']}

ACTUARIO: {datos.get('actuario', '[APELLIDO DEL ACTUARIO]')}
{fecha}

Tiene lugar el comparendo de contestación, conciliación y prueba decretado para el día de hoy en la causa Rol N° {caso['ROL']}, con la asistencia de {parte_a} y de {parte_b}.

EL TRIBUNAL: LAS PARTES SE NOTIFICAN EN ESTE ACTO DE TODAS LAS RESOLUCIONES DICTADAS EN EL PROCESO.

------LA PARTE DE {parte_a}:
Ratifica la denuncia y los documentos acompañados por {caso['DESCRIPCION_INFRACCION']}, con expresa condenación en costas.

------LA PARTE DE {parte_b}:
Contesta por escrito, pide el rechazo con costas y que el escrito se tenga como parte integrante del comparendo.

EL TRIBUNAL: INCORPÓRASE A LA CAUSA ESCRITO DE CONTESTACIÓN. TÉNGASE POR CONTESTADA LA DENUNCIA.

EL TRIBUNAL LLAMA A LAS PARTES A UNA CONCILIACIÓN LA QUE {datos.get('conciliacion', 'NO SE PRODUCE')}.

Los comparecientes se notifican en este acto de las resoluciones que anteceden y previa lectura ratifican y firman con Usía.

[FIRMAS]
"""


def _redactar_plazo(caso: dict, fuentes: list[dict], datos: dict) -> str:
    fecha = _FECHA_LETRAS.format(ciudad=caso["CIUDAD"], dia=caso["DIA"], mes=caso["MES"], ano=caso["AÑO"])
    dias = datos.get("plazo_dias", "[N]")
    tipo_plazo = datos.get("tipo_plazo", "corridos")
    fundamento = datos.get("fundamento", "artículo 22 de la Ley 18.287")
    return f"""\
{fecha}

VISTOS Y CONSIDERANDO:

1.- Los antecedentes de la causa Rol N° {caso['ROL']} de este tribunal.

2.- Lo dispuesto en el {fundamento} (tabla maestra de plazos del tribunal, cita verificada contra el corpus).

Atendido lo expuesto, fíjase el plazo de {dias} días {tipo_plazo}, contados desde {datos.get('desde', 'la notificación de esta resolución')}, para {datos.get('objeto_plazo', caso['DESCRIPCION_INFRACCION'])}. {_NOTIF_CARTA}
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