"""Descarga y cache de texto completo de normas desde LeyChile obtxml (XML oficial)."""

from __future__ import annotations

import html
import re
import xml.etree.ElementTree as ET

import httpx

OBTXML = "https://www.leychile.cl/Consulta/obtxml?opt=7&idNorma={id}"
NS = {"lc": "http://www.leychile.cl/esquemas"}


def _strip_ns(tag: str) -> str:
    return tag.split("}", 1)[-1] if "}" in tag else tag


def fetch_texto(leychile_id: str, timeout: float = 30.0, max_chars: int = 14_000) -> str | None:
    """`max_chars` acota el cuerpo para no saturar el contexto del modelo.
    La precarga forense (scripts/precargar_codigos.py) usa un tope mucho mayor
    para tener el cuerpo ÍNTEGRO en caché (necesario para obtener_articulo_texto)."""
    url = OBTXML.format(id=leychile_id)
    try:
        r = httpx.get(url, timeout=timeout,
                      headers={"User-Agent": "chilean-legal-mcp/0.1"},
                      follow_redirects=True)
        r.raise_for_status()
    except Exception:
        return None

    if "No se encontr" in r.text or r.status_code != 200:
        return None

    # Parse XML
    try:
        root = ET.fromstring(r.text.encode("utf-8") if isinstance(r.text, str) else r.content)
    except ET.ParseError:
        return _fallback_text(r.text, leychile_id, max_chars)

    # Extraer metadatos
    titulo_el = root.find(".//lc:TituloNorma", NS)
    titulo = (titulo_el.text or "").strip() if titulo_el is not None else ""
    materias = [e.text.strip() for e in root.findall(".//lc:Materia", NS) if e.text]

    # Extraer todos los bloques de texto
    textos: list[str] = []
    for el in root.iter():
        if _strip_ns(el.tag) == "Texto" and el.text and el.text.strip():
            t = html.unescape(el.text.strip())
            if len(t) > 30:
                textos.append(t)

    cuerpo = "\n\n".join(textos)
    # Limpiar
    cuerpo = re.sub(r"\n{3,}", "\n\n", cuerpo)
    if len(cuerpo) > max_chars:
        cuerpo = cuerpo[:max_chars] + "\n\n…[texto truncado, ver fuente oficial]"

    url_oficial = f"https://www.bcn.cl/leychile/navegar?idNorma={leychile_id}"
    header = f"{titulo}\n"
    if materias:
        header += f"Materias: {', '.join(materias)}\n"
    header += f"Fuente oficial: {url_oficial}\n"
    header += "—" * 40 + "\n\n"

    full = header + cuerpo
    return full if len(cuerpo) > 200 else _fallback_text(r.text, leychile_id, max_chars)


def _fallback_text(raw: str, leychile_id: str, max_chars: int = 14_000) -> str | None:
    t = re.sub(r"<[^>]+>", " ", raw)
    t = html.unescape(t)
    t = re.sub(r"\s+", " ", t).strip()
    if len(t) > max_chars:
        t = t[:max_chars] + " …[truncado]"
    t += f"\n\nFuente oficial: https://www.bcn.cl/leychile/navegar?idNorma={leychile_id}"
    return t if len(t) > 300 else None
