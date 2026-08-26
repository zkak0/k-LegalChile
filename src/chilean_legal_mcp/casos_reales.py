"""Pipeline de casos reales: descarga documentos oficiales y extrae el caso completo.

Para cada documento recupera: identificación (N°/organismo/fecha), hechos, consulta/cuestión,
resolución y fundamento legal — desde el texto REAL del documento, no inventado.
"""

from __future__ import annotations

import io
import re
import html as html_lib
import urllib.parse
from datetime import datetime

import httpx

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36", "Accept-Language": "es-CL,es;q=0.9"}


def _persistir_caso(caso: dict, origen: str) -> dict:
    """Guarda el caso en la base local (tabla casos + FTS) para buscar casos parecidos luego."""
    try:
        from .db import get_db
        id_ = f"{origen}:{caso.get('identificacion','')[:50]}"
        get_db().upsert_caso(
            id=id_,
            identificacion=caso.get("identificacion", ""),
            organismo=caso.get("organismo", ""),
            tipo=caso.get("tipo", ""),
            hechos=caso.get("hechos", ""),
            resolucion=caso.get("resolucion", ""),
            url=caso.get("fuente_url", caso.get("url", "")),
            fecha=caso.get("fecha"),
        )
    except Exception:
        pass
    return caso


def normalizar_texto(texto: str) -> str:
    """Normaliza texto extraído de PDFs oficiales para que los párrafos queden limpios.

    - Une palabras cortadas por tilde/justificación: 'patró n' → 'patrón', 'má s' → 'más'
    - Colapsa saltos de línea simples en espacios (párrafo fluido); dobles saltos = párrafo nuevo
    - Colapsa espacios múltiples
    - Limpia guiones bajos de nombres de archivo
    """
    if not texto:
        return texto
    t = texto
    # 1. Palabras cortadas por tilde + espacio + resto corto: 'patró n', 'má s', 'código n'...
    t = re.sub(r"([a-záéíóúñA-ZÁÉÍÓÚÑ])([áéíóúñ])\s+([a-z]{1,3})\b", r"\1\2\3", t)
    # Variante: consonante + espacio + 1-2 letras minúsculas al final de palabra (menos agresivo)
    t = re.sub(r"\b([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)\s+([a-z]{1,2})(?=[\s,.;:])", r"\1\2", t)
    # 2. Saltos simples dentro de párrafo → espacio; dobles/múltiples → marcador de párrafo
    t = re.sub(r"\n{2,}", "\u2029", t)
    t = re.sub(r"\n+", " ", t)
    t = t.replace("\u2029", "\n\n")
    # 3. Espacios múltiples
    t = re.sub(r"[ \t]{2,}", " ", t)
    # 4. Guiones bajos de nombres de archivo en títulos
    t = t.replace("_", " ")
    # 5. Espacios antes de puntuación
    t = re.sub(r"\s+([,.;:!?)\]])", r"\1", t)
    t = re.sub(r"([(])\s+", r"\1", t)
    return t.strip()


def limpiar_titulo_archivo(titulo: str) -> str:
    """Limpia títulos derivados de nombres de archivo: 'Resolucion_Ex_N_3530' → 'Resolucion Ex N 3530'."""
    t = titulo.replace("_", " ").strip()
    t = re.sub(r"\s+", " ", t)
    # Expandir abreviaturas comunes
    t = re.sub(r"\bEx\b\.?", "Exenta", t)
    t = re.sub(r"\bResolucion\b", "Resolución", t)
    t = re.sub(r"\bN\b(?=\s*\d)", "N°", t)
    return t


def descargar_pdf(url: str) -> str | None:
    """Descarga un PDF oficial y extrae su texto (máx ~6 páginas)."""
    try:
        r = httpx.get(url, timeout=30, headers=HEADERS, follow_redirects=True)
        if r.status_code != 200 or len(r.content) < 500:
            return None
        if PdfReader is None:
            return None
        reader = PdfReader(io.BytesIO(r.content))
        texto = "\n".join(p.extract_text() or "" for p in reader.pages[:6])
        texto = re.sub(r"[ \t]+", " ", texto)
        texto = re.sub(r"\n{3,}", "\n\n", texto).strip()
        texto = normalizar_texto(texto)
        return texto if len(texto) > 200 else None
    except Exception:
        return None


def descargar_html(url: str) -> str | None:
    try:
        r = httpx.get(url, timeout=25, headers=HEADERS, follow_redirects=True)
        if r.status_code != 200 or len(r.text) < 500:
            return None
        text = re.sub(r"<script.*?</script>|<style.*?</style>", " ", r.text, flags=re.S | re.I)
        text = re.sub(r"<[^>]+>", " ", text)
        text = html_lib.unescape(text)
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n\s*\n+", "\n\n", text).strip()
        text = normalizar_texto(text)
        return text if len(text) > 300 else None
    except Exception:
        return None


def extraer_caso_de_oficio_sii(item: dict) -> dict | None:
    """Descarga el PDF oficial de un oficio SII y extrae el caso estructurado."""
    from .sii import _oficio_download_url  # reusar constructor de URL oficial
    url_pdf = _oficio_download_url(item)
    texto = descargar_pdf(url_pdf)
    if not texto:
        return None
    caso = {
        "identificacion": f"Oficio N° {item.get('pubNumOficio','s/n')} de {item.get('pubFechaPubli','s/f')} — Dirección de Impuestos Indirectos / Subdirección, SII",
        "fuente_url": url_pdf,
        "materia": item.get("pubResumen", ""),
        "fundamento_legal": item.get("pubLegal", ""),
        "hechos": "",
        "consulta": "",
        "resolucion": "",
    }
    # El formato estándar de los oficios SII: "De acuerdo con su presentación... [hechos].
    # Consulta... [cuestión]. ... se informa que... [resolución]."
    # Normalizar saltos para regex (el PDF tiene líneas cortas)
    plano = re.sub(r"\s*\n\s*", " ", texto)
    low = plano.lower()
    # Hechos
    m = re.search(r"(de acuerdo con su (?:presentaci\w*|carta|solicitud).{0,1200}?)(?=consulta|consultan|solicita)", plano, re.I | re.S)
    if m:
        caso["hechos"] = m.group(1).strip()[:900]
    # Consulta
    m = re.search(r"((?:consulta|consultan|solicita(?:n|r) opinar).{0,600}?)(?=al respecto|sobre el particular|en consecuencia)", plano, re.I | re.S)
    if m:
        caso["consulta"] = m.group(1).strip()[:600]
    # Resolución
    m = re.search(r"((?:al respecto|sobre el particular|en consecuencia).{0,1600})", plano, re.I | re.S)
    if m:
        caso["resolucion"] = m.group(1).strip()[:1400]
    # Fallback: si no matcheó la estructura, tomar bloques
    if not caso["hechos"] and not caso["resolucion"]:
        parrafos = [p.strip() for p in texto.split("\n") if len(p.strip()) > 120]
        if len(parrafos) >= 2:
            caso["hechos"] = parrafos[1][:800]
            caso["resolucion"] = parrafos[-1][:1000]
    return _persistir_caso(caso, "sii_oficio") if (caso["hechos"] or caso["resolucion"]) else None


def extraer_caso_de_pdf_generico(url: str, organismo: str, tipo: str) -> dict | None:
    """Descarga un PDF oficial genérico (TGR, TDPI, circular) y extrae el caso."""
    texto = descargar_pdf(url)
    if not texto:
        return None
    caso = {
        "identificacion": f"{tipo} — {organismo}",
        "fuente_url": url,
        "materia": "",
        "fundamento_legal": "",
        "hechos": "",
        "consulta": "",
        "resolucion": "",
    }
    # Título = primera línea significativa
    for linea in texto.split("\n"):
        linea = linea.strip()
        if len(linea) > 20:
            caso["materia"] = linea[:150]
            break
    low = texto.lower()
    m = re.search(r"(antecedentes|hechos|de acuerdo con|por medio de la presente|vino en solicitar)(.{0,1200}?)(?=resoluci|se resuelve|dictamina|inform[ae]|concluye)", texto, re.I | re.S)
    if m:
        caso["hechos"] = m.group(0).strip()[:1000]
    m = re.search(r"((?:se resuelve|resoluci[oó]n|dictamina|concluye|se informa que)(.{0,1400}))", texto, re.I | re.S)
    if m:
        caso["resolucion"] = m.group(0).strip()[:1200]
    # Fundamento: buscar artículos citados
    arts = re.findall(r"art[íi]culo\s+\d+[^\s,.;]{0,10}|Ley\s+N?°?\s*[\d.]+|DL\s+N?°?\s*[\d.]+|DFL\s+N?°?\s*[\d.]+", texto)
    if arts:
        caso["fundamento_legal"] = ", ".join(dict.fromkeys(arts))[:300]
    if not caso["hechos"] and not caso["resolucion"]:
        parrafos = [p.strip() for p in texto.split("\n") if len(p.strip()) > 120]
        if parrafos:
            caso["hechos"] = parrafos[0][:900]
            if len(parrafos) > 1:
                caso["resolucion"] = parrafos[-1][:900]
    return _persistir_caso(caso, "pdf_generico") if (caso["hechos"] or caso["resolucion"]) else None


def extraer_caso_de_dictamen_bcn(url_documento: str, titulo: str = "") -> dict | None:
    """Descarga un dictamen CGR desde datos.bcn.cl (HTML) y extrae el caso."""
    texto = descargar_html(url_documento)
    if not texto:
        return None
    caso = {
        "identificacion": titulo or f"Dictamen — {url_documento.rsplit('/',1)[-1]}",
        "fuente_url": url_documento,
        "materia": titulo[:150],
        "fundamento_legal": "",
        "hechos": "",
        "consulta": "",
        "resolucion": "",
    }
    low = texto.lower()
    idx = low.find("dictamen")
    cuerpo = texto[max(0, idx):idx+6000] if idx >= 0 else texto[:6000]
    m = re.search(r"((?:hechos|antecedentes|de acuerdo con|vino en)(.{0,1200}?))(?=resoluci|dictamina|concluye)", cuerpo, re.I | re.S)
    if m:
        caso["hechos"] = m.group(0).strip()[:1000]
    m = re.search(r"((?:se resuelve|resolvi(?:ó|o)|dictamina|concluye)(.{0,1200}))", cuerpo, re.I | re.S)
    if m:
        caso["resolucion"] = m.group(0).strip()[:1000]
    arts = re.findall(r"art[íi]culo\s+\d+[^\s,.;]{0,10}|Ley\s+N?°?\s*[\d.]+|DF\s+N?°?\s*[\d.]+", cuerpo)
    if arts:
        caso["fundamento_legal"] = ", ".join(dict.fromkeys(arts))[:300]
    if not caso["hechos"] and not caso["resolucion"]:
        parrafos = [p.strip() for p in cuerpo.split("\n") if len(p.strip()) > 150]
        if parrafos:
            caso["hechos"] = parrafos[0][:900]
            if len(parrafos) > 1:
                caso["resolucion"] = parrafos[-1][:900]
    return _persistir_caso(caso, "dictamen_bcn") if (caso["hechos"] or caso["resolucion"]) else None
