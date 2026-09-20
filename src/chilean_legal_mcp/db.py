"""Base de datos SQLite con búsqueda de texto completo (FTS5) para normas chilenas."""

from __future__ import annotations

import sqlite3
from pathlib import Path

DEFAULT_DB = Path(__file__).resolve().parent.parent.parent / "data" / "normas.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS normas (
    uri TEXT PRIMARY KEY,
    titulo TEXT NOT NULL,
    numero TEXT,
    fecha_publicacion TEXT,
    leychile_id TEXT,
    tipo TEXT
);

CREATE VIRTUAL TABLE IF NOT EXISTS normas_fts USING fts5(
    titulo, numero, content='normas', content_rowid='rowid',
    tokenize='unicode61 remove_diacritics 2'
);

CREATE TRIGGER IF NOT EXISTS normas_ai AFTER INSERT ON normas BEGIN
    INSERT INTO normas_fts(rowid, titulo, numero) VALUES (new.rowid, new.titulo, new.numero);
END;

CREATE TRIGGER IF NOT EXISTS normas_ad AFTER DELETE ON normas BEGIN
    INSERT INTO normas_fts(normas_fts, rowid, titulo, numero)
    VALUES ('delete', old.rowid, old.titulo, old.numero);
END;

CREATE TABLE IF NOT EXISTS textos (
    leychile_id TEXT PRIMARY KEY,
    texto TEXT NOT NULL,
    actualizado TEXT DEFAULT (datetime('now'))
);

CREATE VIRTUAL TABLE IF NOT EXISTS textos_fts USING fts5(
    texto, content='textos', content_rowid='rowid',
    tokenize='unicode61 remove_diacritics 2'
);
CREATE TRIGGER IF NOT EXISTS textos_ai AFTER INSERT ON textos BEGIN
    INSERT INTO textos_fts(rowid, texto) VALUES (new.rowid, new.texto);
END;
CREATE TRIGGER IF NOT EXISTS textos_ad AFTER DELETE ON textos BEGIN
    INSERT INTO textos_fts(textos_fts, rowid, texto) VALUES ('delete', old.rowid, old.texto);
END;

CREATE TABLE IF NOT EXISTS dictamenes (
    id TEXT PRIMARY KEY,
    numero TEXT,
    titulo TEXT,
    fecha TEXT,
    url TEXT
);
CREATE VIRTUAL TABLE IF NOT EXISTS dictamenes_fts USING fts5(
    titulo, numero, content='dictamenes', content_rowid='rowid',
    tokenize='unicode61 remove_diacritics 2'
);
CREATE TRIGGER IF NOT EXISTS dictamenes_ai AFTER INSERT ON dictamenes BEGIN
    INSERT INTO dictamenes_fts(rowid, titulo, numero) VALUES (new.rowid, new.titulo, new.numero);
END;

-- SII separados
CREATE TABLE IF NOT EXISTS sii_oficios (id TEXT PRIMARY KEY, numero TEXT, titulo TEXT, url TEXT);
CREATE VIRTUAL TABLE IF NOT EXISTS sii_oficios_fts USING fts5(titulo, numero, content='sii_oficios', content_rowid='rowid', tokenize='unicode61 remove_diacritics 2');
CREATE TRIGGER IF NOT EXISTS sii_oficios_ai AFTER INSERT ON sii_oficios BEGIN INSERT INTO sii_oficios_fts(rowid, titulo, numero) VALUES (new.rowid, new.titulo, new.numero); END;
CREATE TABLE IF NOT EXISTS sii_circulares (id TEXT PRIMARY KEY, numero TEXT, titulo TEXT, url TEXT);
CREATE VIRTUAL TABLE IF NOT EXISTS sii_circulares_fts USING fts5(titulo, numero, content='sii_circulares', content_rowid='rowid', tokenize='unicode61 remove_diacritics 2');
CREATE TRIGGER IF NOT EXISTS sii_circulares_ai AFTER INSERT ON sii_circulares BEGIN INSERT INTO sii_circulares_fts(rowid, titulo, numero) VALUES (new.rowid, new.titulo, new.numero); END;
CREATE TABLE IF NOT EXISTS sii_resoluciones (id TEXT PRIMARY KEY, numero TEXT, titulo TEXT, url TEXT);
CREATE VIRTUAL TABLE IF NOT EXISTS sii_resoluciones_fts USING fts5(titulo, numero, content='sii_resoluciones', content_rowid='rowid', tokenize='unicode61 remove_diacritics 2');
CREATE TRIGGER IF NOT EXISTS sii_resoluciones_ai AFTER INSERT ON sii_resoluciones BEGIN INSERT INTO sii_resoluciones_fts(rowid, titulo, numero) VALUES (new.rowid, new.titulo, new.numero); END;
CREATE TABLE IF NOT EXISTS sii_fallos (id TEXT PRIMARY KEY, numero TEXT, titulo TEXT, url TEXT);
CREATE VIRTUAL TABLE IF NOT EXISTS sii_fallos_fts USING fts5(titulo, numero, content='sii_fallos', content_rowid='rowid', tokenize='unicode61 remove_diacritics 2');
CREATE TRIGGER IF NOT EXISTS sii_fallos_ai AFTER INSERT ON sii_fallos BEGIN INSERT INTO sii_fallos_fts(rowid, titulo, numero) VALUES (new.rowid, new.titulo, new.numero); END;
-- TGR separados
CREATE TABLE IF NOT EXISTS tgr_dictamenes (id TEXT PRIMARY KEY, numero TEXT, titulo TEXT, url TEXT, resultado TEXT);
CREATE VIRTUAL TABLE IF NOT EXISTS tgr_dictamenes_fts USING fts5(titulo, numero, content='tgr_dictamenes', content_rowid='rowid', tokenize='unicode61 remove_diacritics 2');
CREATE TRIGGER IF NOT EXISTS tgr_dictamenes_ai AFTER INSERT ON tgr_dictamenes BEGIN INSERT INTO tgr_dictamenes_fts(rowid, titulo, numero) VALUES (new.rowid, new.titulo, new.numero); END;
CREATE TABLE IF NOT EXISTS tgr_resoluciones (id TEXT PRIMARY KEY, numero TEXT, titulo TEXT, url TEXT);
CREATE VIRTUAL TABLE IF NOT EXISTS tgr_resoluciones_fts USING fts5(titulo, numero, content='tgr_resoluciones', content_rowid='rowid', tokenize='unicode61 remove_diacritics 2');
CREATE TRIGGER IF NOT EXISTS tgr_resoluciones_ai AFTER INSERT ON tgr_resoluciones BEGIN INSERT INTO tgr_resoluciones_fts(rowid, titulo, numero) VALUES (new.rowid, new.titulo, new.numero); END;
CREATE TABLE IF NOT EXISTS tgr_circulares (id TEXT PRIMARY KEY, numero TEXT, titulo TEXT, url TEXT);
CREATE VIRTUAL TABLE IF NOT EXISTS tgr_circulares_fts USING fts5(titulo, numero, content='tgr_circulares', content_rowid='rowid', tokenize='unicode61 remove_diacritics 2');
CREATE TRIGGER IF NOT EXISTS tgr_circulares_ai AFTER INSERT ON tgr_circulares BEGIN INSERT INTO tgr_circulares_fts(rowid, titulo, numero) VALUES (new.rowid, new.titulo, new.numero); END;
CREATE TABLE IF NOT EXISTS tgr_fallos (id TEXT PRIMARY KEY, numero TEXT, titulo TEXT, url TEXT, resultado TEXT);
CREATE VIRTUAL TABLE IF NOT EXISTS tgr_fallos_fts USING fts5(titulo, numero, content='tgr_fallos', content_rowid='rowid', tokenize='unicode61 remove_diacritics 2');
CREATE TRIGGER IF NOT EXISTS tgr_fallos_ai AFTER INSERT ON tgr_fallos BEGIN INSERT INTO tgr_fallos_fts(rowid, titulo, numero) VALUES (new.rowid, new.titulo, new.numero); END;
-- INAPI / TDPI
CREATE TABLE IF NOT EXISTS inapi_marcas (id TEXT PRIMARY KEY, numero TEXT, titulo TEXT, url TEXT, titular TEXT, estado TEXT);
CREATE VIRTUAL TABLE IF NOT EXISTS inapi_marcas_fts USING fts5(titulo, numero, titular, content='inapi_marcas', content_rowid='rowid', tokenize='unicode61 remove_diacritics 2');
CREATE TRIGGER IF NOT EXISTS inapi_marcas_ai AFTER INSERT ON inapi_marcas BEGIN INSERT INTO inapi_marcas_fts(rowid, titulo, numero, titular) VALUES (new.rowid, new.titulo, new.numero, new.titular); END;
CREATE TABLE IF NOT EXISTS tdpi_juris (id TEXT PRIMARY KEY, numero TEXT, titulo TEXT, url TEXT);
CREATE VIRTUAL TABLE IF NOT EXISTS tdpi_juris_fts USING fts5(titulo, numero, content='tdpi_juris', content_rowid='rowid', tokenize='unicode61 remove_diacritics 2');
CREATE TRIGGER IF NOT EXISTS tdpi_juris_ai AFTER INSERT ON tdpi_juris BEGIN INSERT INTO tdpi_juris_fts(rowid, titulo, numero) VALUES (new.rowid, new.titulo, new.numero); END;
CREATE TABLE IF NOT EXISTS superir_boletin (id TEXT PRIMARY KEY, numero TEXT, titulo TEXT, url TEXT);
CREATE VIRTUAL TABLE IF NOT EXISTS superir_boletin_fts USING fts5(titulo, numero, content='superir_boletin', content_rowid='rowid', tokenize='unicode61 remove_diacritics 2');
CREATE TRIGGER IF NOT EXISTS superir_boletin_ai AFTER INSERT ON superir_boletin BEGIN INSERT INTO superir_boletin_fts(rowid, titulo, numero) VALUES (new.rowid, new.titulo, new.numero); END;
CREATE TABLE IF NOT EXISTS sma_sancionatorio (id TEXT PRIMARY KEY, numero TEXT, titulo TEXT, url TEXT);
CREATE VIRTUAL TABLE IF NOT EXISTS sma_sancionatorio_fts USING fts5(titulo, numero, content='sma_sancionatorio', content_rowid='rowid', tokenize='unicode61 remove_diacritics 2');
CREATE TRIGGER IF NOT EXISTS sma_sancionatorio_ai AFTER INSERT ON sma_sancionatorio BEGIN INSERT INTO sma_sancionatorio_fts(rowid, titulo, numero) VALUES (new.rowid, new.titulo, new.numero); END;
-- Cache de vigencia de normas (cambia raramente; TTL 7 días)
CREATE TABLE IF NOT EXISTS vigencias (
    leychile_id TEXT PRIMARY KEY,
    estado_json TEXT NOT NULL,
    consultado TEXT DEFAULT (datetime('now'))
);
-- Casos reales extraídos de documentos oficiales (para "casos parecidos")
CREATE TABLE IF NOT EXISTS casos (
    id TEXT PRIMARY KEY,
    identificacion TEXT,
    organismo TEXT,
    tipo TEXT,
    hechos TEXT,
    resolucion TEXT,
    url TEXT,
    fecha TEXT
);
CREATE VIRTUAL TABLE IF NOT EXISTS casos_fts USING fts5(
    identificacion, organismo, hechos, resolucion,
    content='casos', content_rowid='rowid',
    tokenize='unicode61 remove_diacritics 2'
);
CREATE TRIGGER IF NOT EXISTS casos_ai AFTER INSERT ON casos BEGIN
    INSERT INTO casos_fts(rowid, identificacion, organismo, hechos, resolucion)
    VALUES (new.rowid, new.identificacion, new.organismo, new.hechos, new.resolucion);
END;
-- Memoria persistente del abogado (cache circular: máx 500 mensajes, limpieza >30 días)
CREATE TABLE IF NOT EXISTS memoria_mensajes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sesion_id TEXT,
    rol TEXT NOT NULL,
    contenido TEXT NOT NULL,
    herramientas TEXT,
    fecha TEXT DEFAULT (datetime('now', 'localtime'))
);
CREATE VIRTUAL TABLE IF NOT EXISTS memoria_mensajes_fts USING fts5(
    contenido, content='memoria_mensajes', content_rowid='id',
    tokenize='unicode61 remove_diacritics 2'
);
CREATE TRIGGER IF NOT EXISTS memoria_msg_ai AFTER INSERT ON memoria_mensajes BEGIN
    INSERT INTO memoria_mensajes_fts(rowid, contenido) VALUES (new.id, new.contenido);
END;
CREATE TRIGGER IF NOT EXISTS memoria_msg_ad AFTER DELETE ON memoria_mensajes BEGIN
    INSERT INTO memoria_mensajes_fts(memoria_mensajes_fts, rowid, contenido)
    VALUES ('delete', old.id, old.contenido);
END;
-- Expedientes del abogado (estilo análisis de caso Magnar): carpeta → texto indexado FTS5
CREATE TABLE IF NOT EXISTS expedientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT UNIQUE NOT NULL,
    carpeta TEXT NOT NULL,
    creado TEXT DEFAULT (datetime('now', 'localtime')),
    num_documentos INTEGER DEFAULT 0,
    total_caracteres INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS expediente_docs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    expediente_id INTEGER NOT NULL REFERENCES expedientes(id),
    ruta TEXT,
    titulo TEXT,
    tipo TEXT,
    texto TEXT NOT NULL,
    fecha_doc TEXT
);
CREATE VIRTUAL TABLE IF NOT EXISTS expediente_docs_fts USING fts5(
    titulo, texto, content='expediente_docs', content_rowid='id',
    tokenize='unicode61 remove_diacritics 2'
);
CREATE TRIGGER IF NOT EXISTS expediente_docs_ai AFTER INSERT ON expediente_docs BEGIN
    INSERT INTO expediente_docs_fts(rowid, titulo, texto) VALUES (new.id, new.titulo, new.texto);
END;
CREATE TRIGGER IF NOT EXISTS expediente_docs_ad AFTER DELETE ON expediente_docs BEGIN
    INSERT INTO expediente_docs_fts(expediente_docs_fts, rowid, titulo, texto)
    VALUES ('delete', old.id, old.titulo, old.texto);
END;
-- Embeddings semánticos (Fase 3): búsqueda vectorial para normas, jurisprudencia, expedientes
CREATE TABLE IF NOT EXISTS embeddings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fuente_tipo TEXT NOT NULL,
    fuente_id TEXT NOT NULL,
    chunk_idx INTEGER NOT NULL,
    texto TEXT NOT NULL,
    vector BLOB NOT NULL,
    created_at TEXT DEFAULT (datetime('now', 'localtime'))
);
CREATE UNIQUE INDEX IF NOT EXISTS embeddings_unique ON embeddings(fuente_tipo, fuente_id, chunk_idx);
-- Vigilancias legales automáticas (estilo Monitor): condición en lenguaje natural + fuentes
CREATE TABLE IF NOT EXISTS vigilancias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT UNIQUE NOT NULL,
    condicion TEXT NOT NULL,
    fuentes TEXT NOT NULL,
    activa INTEGER DEFAULT 1,
    creada TEXT DEFAULT (datetime('now', 'localtime')),
    ultima_ejecucion TEXT
);
CREATE TABLE IF NOT EXISTS vigilancia_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vigilancia_id INTEGER NOT NULL REFERENCES vigilancias(id),
    fuente TEXT,
    identificador TEXT,
    titulo TEXT,
    resumen TEXT,
    url TEXT,
    fecha_publicacion TEXT,
    estado TEXT DEFAULT 'nuevo',
    fecha_deteccion TEXT DEFAULT (datetime('now', 'localtime'))
);
CREATE UNIQUE INDEX IF NOT EXISTS vigilancia_items_unicos
    ON vigilancia_items(vigilancia_id, identificador);
CREATE TABLE IF NOT EXISTS memoria_notas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo TEXT DEFAULT 'nota',
    nombre TEXT,
    contenido TEXT NOT NULL,
    fecha TEXT DEFAULT (datetime('now', 'localtime'))
);
CREATE VIRTUAL TABLE IF NOT EXISTS memoria_notas_fts USING fts5(
    nombre, contenido, content='memoria_notas', content_rowid='id',
    tokenize='unicode61 remove_diacritics 2'
);
CREATE TRIGGER IF NOT EXISTS memoria_nota_ai AFTER INSERT ON memoria_notas BEGIN
    INSERT INTO memoria_notas_fts(rowid, nombre, contenido) VALUES (new.id, new.nombre, new.contenido);
END;
-- Corpus K-LegalChile — dictámenes CGR con texto completo
CREATE TABLE IF NOT EXISTS cgr_dictamenes (
    id TEXT PRIMARY KEY,
    numero TEXT,
    anio INTEGER,
    fecha TEXT,
    organismo_consultante TEXT,
    sumario TEXT,
    source_url TEXT,
    unid TEXT,
    materia TEXT
);
CREATE VIRTUAL TABLE IF NOT EXISTS cgr_dictamenes_fts USING fts5(
    numero, organismo_consultante, sumario, content='cgr_dictamenes', content_rowid='rowid',
    tokenize='unicode61 remove_diacritics 2'
);
CREATE TRIGGER IF NOT EXISTS cgr_dictamenes_ai AFTER INSERT ON cgr_dictamenes BEGIN
    INSERT INTO cgr_dictamenes_fts(rowid, numero, organismo_consultante, sumario)
    VALUES (new.rowid, new.numero, new.organismo_consultante, new.sumario);
END;
CREATE TRIGGER IF NOT EXISTS cgr_dictamenes_ad AFTER DELETE ON cgr_dictamenes BEGIN
    INSERT INTO cgr_dictamenes_fts(cgr_dictamenes_fts, rowid, numero, organismo_consultante, sumario)
    VALUES ('delete', old.rowid, old.numero, old.organismo_consultante, old.sumario);
END;
CREATE INDEX IF NOT EXISTS cgr_dictamenes_anio ON cgr_dictamenes(anio, fecha);
CREATE INDEX IF NOT EXISTS cgr_dictamenes_numero ON cgr_dictamenes(numero, anio);
-- Grafo de citaciones (aplica/funda/cita) entre sentencias, dictámenes y normas
CREATE TABLE IF NOT EXISTS citas_legales (
    id INTEGER PRIMARY KEY,
    source_kind TEXT NOT NULL,
    source_id TEXT NOT NULL,
    target_kind TEXT,
    target_id TEXT,
    target_external_ref TEXT,
    tipo TEXT,
    confidence REAL
);
CREATE INDEX IF NOT EXISTS citas_legales_src ON citas_legales(source_kind, source_id);
CREATE INDEX IF NOT EXISTS citas_legales_tgt ON citas_legales(target_kind, target_id);
CREATE INDEX IF NOT EXISTS citas_legales_tipo ON citas_legales(tipo);
-- Estado del criterio por dictamen (vigencia/superación en la línea jurisprudencial)
CREATE TABLE IF NOT EXISTS criterios_estado (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dictamen_id TEXT NOT NULL,
    numero TEXT,
    anio INTEGER,
    estado TEXT NOT NULL,
    descripcion TEXT,
    fuente TEXT,
    fecha TEXT DEFAULT (datetime('now','localtime'))
);
CREATE INDEX IF NOT EXISTS criterios_estado_d ON criterios_estado(dictamen_id);
CREATE UNIQUE INDEX IF NOT EXISTS criterios_estado_u ON criterios_estado(dictamen_id, estado);
"""


class NormasDB:
    def __init__(self, db_path: Path | str | None = None):
        self.db_path = Path(db_path) if db_path else DEFAULT_DB
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(SCHEMA)
        self._conn.commit()

    def upsert_norma(self, uri: str, titulo: str, numero: str | None,
                     fecha: str | None, leychile_id: str | None) -> bool:
        cur = self._conn.execute(
            "SELECT 1 FROM normas WHERE uri = ?", (uri,))
        if cur.fetchone():
            return False
        self._conn.execute(
            "INSERT INTO normas (uri, titulo, numero, fecha_publicacion, leychile_id, tipo) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (uri, titulo, numero, fecha, leychile_id, "norma"))
        self._conn.commit()
        return True

    def search(self, query: str, limit: int = 10) -> list[dict]:
        fts_query = _fts_prefix_query(query)
        rows = self._conn.execute(
            """
            SELECT n.uri, n.titulo, n.numero, n.fecha_publicacion AS fecha,
                   n.leychile_id, bm25(normas_fts) AS score
            FROM normas_fts f
            JOIN normas n ON n.rowid = f.rowid
            WHERE normas_fts MATCH ?
            ORDER BY score LIMIT ?
            """,
            (fts_query, limit)).fetchall()
        return [dict(r) for r in rows]

    def count(self) -> int:
        return self._conn.execute("SELECT COUNT(*) FROM normas").fetchone()[0]

    # Cache de textos completos
    def get_texto(self, leychile_id: str) -> str | None:
        row = self._conn.execute(
            "SELECT texto FROM textos WHERE leychile_id = ?", (leychile_id,)).fetchone()
        return row[0] if row else None

    def save_texto(self, leychile_id: str, texto: str) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO textos (leychile_id, texto) VALUES (?, ?)",
            (leychile_id, texto))
        self._conn.commit()

    def search_textos(self, query: str, limit: int = 10) -> list[dict]:
        try:
            q = _fts_prefix_query(query)
        except ValueError:
            return []
        rows = self._conn.execute(
            "SELECT t.leychile_id, substr(t.texto,1,300) as preview, bm25(textos_fts) as score "
            "FROM textos_fts f JOIN textos t ON t.rowid=f.rowid WHERE textos_fts MATCH ? ORDER BY score LIMIT ?",
            (q, limit)).fetchall()
        return [dict(r) for r in rows]

    def upsert_dictamen(self, id: str, numero: str, titulo: str, fecha: str | None, url: str) -> bool:
        cur = self._conn.execute("SELECT 1 FROM dictamenes WHERE id=?", (id,))
        if cur.fetchone():
            return False
        self._conn.execute("INSERT INTO dictamenes (id, numero, titulo, fecha, url) VALUES (?,?,?,?,?)",
                           (id, numero, titulo, fecha, url))
        self._conn.commit()
        return True

    def search_dictamenes(self, query: str, limit: int = 10) -> list[dict]:
        try:
            q = _fts_prefix_query(query)
        except ValueError:
            return []
        rows = self._conn.execute(
            "SELECT d.id, d.numero, d.titulo, d.fecha, d.url, bm25(dictamenes_fts) as score "
            "FROM dictamenes_fts f JOIN dictamenes d ON d.rowid=f.rowid WHERE dictamenes_fts MATCH ? ORDER BY score LIMIT ?",
            (q, limit)).fetchall()
        return [dict(r) for r in rows]

    def _upsert_generic(self, table: str, fts: str, id: str, numero: str, titulo: str, url: str, resultado: str | None = None) -> bool:
        cur = self._conn.execute(f"SELECT 1 FROM {table} WHERE id=?", (id,))
        if cur.fetchone():
            return False
        if "resultado" in self._conn.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table}'").fetchone()[0]:
            self._conn.execute(f"INSERT INTO {table} (id, numero, titulo, url, resultado) VALUES (?,?,?,?,?)", (id, numero, titulo, url, resultado or ""))
        else:
            self._conn.execute(f"INSERT INTO {table} (id, numero, titulo, url) VALUES (?,?,?,?)", (id, numero, titulo, url))
        self._conn.commit()
        return True

    def _search_generic(self, table: str, fts: str, query: str, limit: int = 10, offset: int = 0) -> list[dict]:
        try:
            q = _fts_prefix_query(query)
        except ValueError:
            return []
        rows = self._conn.execute(
            f"SELECT t.id, t.numero, t.titulo, t.url, bm25({fts}) as score FROM {fts} f JOIN {table} t ON t.rowid=f.rowid WHERE {fts} MATCH ? ORDER BY score LIMIT ? OFFSET ?",
            (q, limit, offset)).fetchall()
        return [dict(r) for r in rows]

    def close(self) -> None:
        self._conn.close()

    # --- Embeddings semánticos (Fase 3) ---
    def upsert_embedding(self, fuente_tipo: str, fuente_id: str, chunk_idx: int,
                         texto: str, vector: bytes) -> None:
        self._conn.execute(
            """INSERT OR REPLACE INTO embeddings
               (fuente_tipo, fuente_id, chunk_idx, texto, vector)
               VALUES (?, ?, ?, ?, ?)""",
            (fuente_tipo, fuente_id, chunk_idx, texto, vector))
        self._conn.commit()

    def search_embeddings(self, query_vector: bytes, top_k: int = 10,
                          fuente_tipo: str | None = None) -> list[dict]:
        import numpy as np
        q = np.frombuffer(query_vector, dtype=np.float32)
        q_norm = np.linalg.norm(q)
        if q_norm > 0:
            q = q / q_norm

        sql = """SELECT id, fuente_tipo, fuente_id, chunk_idx, texto, vector
                 FROM embeddings"""
        params: list = []
        if fuente_tipo:
            sql += " WHERE fuente_tipo = ?"
            params.append(fuente_tipo)
        sql += " LIMIT ?"
        params.append(top_k * 3)

        rows = self._conn.execute(sql, params).fetchall()
        results = []
        for r in rows:
            v = np.frombuffer(r["vector"], dtype=np.float32)
            if len(v) != len(q):  # vectores de otra dimensión se omiten
                continue
            v_norm = np.linalg.norm(v)
            if v_norm > 0:
                v = v / v_norm
            score = float(q @ v)
            results.append({
                "id": r["id"],
                "fuente_tipo": r["fuente_tipo"],
                "fuente_id": r["fuente_id"],
                "chunk_idx": r["chunk_idx"],
                "texto": r["texto"],
                "score": score
            })
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def count_embeddings(self) -> int:
        return self._conn.execute("SELECT COUNT(*) FROM embeddings").fetchone()[0]

    # --- Casos reales ---
    def upsert_caso(self, id: str, identificacion: str, organismo: str, tipo: str,
                    hechos: str, resolucion: str, url: str, fecha: str | None) -> bool:
        cur = self._conn.execute("SELECT 1 FROM casos WHERE id=?", (id,))
        if cur.fetchone():
            return False
        self._conn.execute(
            "INSERT INTO casos (id, identificacion, organismo, tipo, hechos, resolucion, url, fecha) VALUES (?,?,?,?,?,?,?,?)",
            (id, identificacion, organismo, tipo, hechos, resolucion, url, fecha))
        self._conn.commit()
        return True

    def search_casos(self, query: str, limit: int = 5, offset: int = 0) -> list[dict]:
        try:
            q = _fts_prefix_query(query)
        except ValueError:
            return []
        rows = self._conn.execute(
            "SELECT c.id, c.identificacion, c.organismo, c.tipo, substr(c.hechos,1,300) AS hechos, "
            "substr(c.resolucion,1,300) AS resolucion, c.url, c.fecha, bm25(casos_fts) AS score "
            "FROM casos_fts f JOIN casos c ON c.rowid=f.rowid "
            "WHERE casos_fts MATCH ? ORDER BY score LIMIT ? OFFSET ?",
            (q, limit, offset)).fetchall()
        return [dict(r) for r in rows]

    # --- Cache de vigencia ---
    def get_vigencia(self, leychile_id: str) -> dict | None:
        import json as _json
        row = self._conn.execute(
            "SELECT estado_json, consultado FROM vigencias WHERE leychile_id = ?",
            (leychile_id,)).fetchone()
        if not row:
            return None
        try:
            return _json.loads(row[0])
        except Exception:
            return None

    def save_vigencia(self, leychile_id: str, estado: dict) -> None:
        import json as _json
        self._conn.execute(
            "INSERT OR REPLACE INTO vigencias (leychile_id, estado_json, consultado) VALUES (?, ?, datetime('now'))",
            (leychile_id, _json.dumps(estado, ensure_ascii=False)))
        self._conn.commit()

    # --- Corpus K-LegalChile: dictámenes CGR ---
    def upsert_dictamen_cgr(self, id: str, numero: str, anio: int | None, fecha: str | None,
                            organismo_consultante: str | None, sumario: str | None,
                            source_url: str | None, unid: str | None, materia: str | None) -> bool:
        cur = self._conn.execute("SELECT 1 FROM cgr_dictamenes WHERE id=?", (str(id),))
        if cur.fetchone():
            return False
        self._conn.execute(
            "INSERT INTO cgr_dictamenes (id, numero, anio, fecha, organismo_consultante, sumario, source_url, unid, materia) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (str(id), numero, anio, fecha, organismo_consultante, sumario, source_url, unid, materia))
        self._conn.commit()
        return True

    def search_dictamenes_cgr(self, query: str, limit: int = 10, anio: int | None = None,
                              offset: int = 0) -> list[dict]:
        try:
            q = _fts_prefix_query(query)
        except ValueError:
            return []
        sql = """SELECT d.id, d.numero, d.anio, d.fecha, d.organismo_consultante,
                        substr(d.sumario,1,400) AS sumario_preview, d.source_url, d.unid, d.materia,
                        bm25(cgr_dictamenes_fts) AS score
                 FROM cgr_dictamenes_fts f JOIN cgr_dictamenes d ON d.rowid=f.rowid
                 WHERE cgr_dictamenes_fts MATCH ?"""
        params: list = [q]
        if anio:
            sql += " AND d.anio = ?"
            params.append(int(anio))
        sql += " ORDER BY score LIMIT ? OFFSET ?"
        params += [limit, offset]
        rows = self._conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]

    def consultar_dictamen_cgr(self, dictamen_id: str | None = None,
                               numero: str | None = None, anio: int | None = None,
                               unid: str | None = None) -> dict | None:
        sql = "SELECT * FROM cgr_dictamenes WHERE 1=1"
        params: list = []
        if dictamen_id:
            sql += " AND id = ?"
            params.append(str(dictamen_id))
        if unid:
            sql += " AND unid = ?"
            params.append(str(unid).upper())
        if numero:
            sql += " AND numero = ?"
            params.append(str(numero))
        if anio:
            sql += " AND anio = ?"
            params.append(int(anio))
        sql += " ORDER BY fecha DESC LIMIT 1"
        row = self._conn.execute(sql, params).fetchone()
        return dict(row) if row else None

    def count_dictamenes_cgr(self) -> int:
        return self._conn.execute("SELECT COUNT(*) FROM cgr_dictamenes").fetchone()[0]

    def listar_dictamenes_cgr(self, anio: int | None = None, limit: int = 20,
                              offset: int = 0, recientes: bool = True) -> list[dict]:
        sql = "SELECT id, numero, anio, fecha, organismo_consultante, substr(sumario,1,200) AS sumario_preview, source_url, unid FROM cgr_dictamenes WHERE 1=1"
        params: list = []
        if anio:
            sql += " AND anio = ?"
            params.append(int(anio))
        sql += f" ORDER BY fecha {'DESC' if recientes else 'ASC'} LIMIT ? OFFSET ?"
        params += [limit, offset]
        rows = self._conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]

    # --- Grafo de citaciones ---
    def upsert_cita(self, id: int, source_kind: str, source_id: str, target_kind: str | None,
                    target_id: str | None, target_external_ref: str | None, tipo: str | None,
                    confidence: float | None) -> bool:
        cur = self._conn.execute("SELECT 1 FROM citas_legales WHERE id=?", (id,))
        if cur.fetchone():
            return False
        self._conn.execute(
            "INSERT INTO citas_legales (id, source_kind, source_id, target_kind, target_id, target_external_ref, tipo, confidence) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (id, source_kind, source_id, target_kind, target_id, target_external_ref, tipo, confidence))
        self._conn.commit()
        return True

    def get_citas(self, source_kind: str | None = None, source_id: str | None = None,
                  target_kind: str | None = None, target_id: str | None = None,
                  tipo: str | None = None, limit: int = 50) -> list[dict]:
        sql = "SELECT * FROM citas_legales WHERE 1=1"
        params: list = []
        if source_kind:
            sql += " AND source_kind = ?"
            params.append(source_kind)
        if source_id:
            sql += " AND source_id = ?"
            params.append(str(source_id))
        if target_kind:
            sql += " AND target_kind = ?"
            params.append(target_kind)
        if target_id:
            sql += " AND target_id = ?"
            params.append(str(target_id))
        if tipo:
            sql += " AND tipo = ?"
            params.append(tipo)
        sql += " ORDER BY confidence DESC, id LIMIT ?"
        params.append(limit)
        rows = self._conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]

    def count_citas_legales(self) -> int:
        return self._conn.execute("SELECT COUNT(*) FROM citas_legales").fetchone()[0]

    def get_cadena_dictamen(self, dictamen_id: str) -> list[dict]:
        """Citas que un dictamen hace a otros (salida) y citas que otros hacen hacia él (entrada)."""
        rows = self._conn.execute(
            "SELECT * FROM citas_legales WHERE (source_kind='dictamen' AND source_id=?) "
            "OR (target_kind='dictamen' AND target_id=?) ORDER BY id", (str(dictamen_id), str(dictamen_id))
        ).fetchall()
        return [dict(r) for r in rows]

    # --- Estado del criterio ---
    def upsert_criterio(self, dictamen_id: str, numero: str | None, anio: int | None,
                        estado: str, descripcion: str | None, fuente: str | None) -> bool:
        self._conn.execute(
            "INSERT OR REPLACE INTO criterios_estado (dictamen_id, numero, anio, estado, descripcion, fuente) "
            "VALUES (?,?,?,?,?,?)",
            (str(dictamen_id), numero, anio, estado, descripcion, fuente))
        self._conn.commit()
        return True

    def get_criterios(self, dictamen_id: str) -> list[dict]:
        rows = self._conn.execute(
            "SELECT * FROM criterios_estado WHERE dictamen_id=? ORDER BY id", (str(dictamen_id),)
        ).fetchall()
        return [dict(r) for r in rows]

    def count_criterios(self) -> int:
        return self._conn.execute("SELECT COUNT(*) FROM criterios_estado").fetchone()[0]


def _fts_prefix_query(query: str) -> str:
    words = [w for w in query.replace('"', " ").split() if w]
    if not words:
        raise ValueError("Consulta vacía")
    return " ".join(f'"{w}"*' for w in words)


_db_singleton: NormasDB | None = None


def get_db() -> NormasDB:
    """Singleton lazy — compartido entre módulos (casos_reales, vigencia, etc.)."""
    global _db_singleton
    if _db_singleton is None:
        _db_singleton = NormasDB()
    return _db_singleton
