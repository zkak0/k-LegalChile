from __future__ import annotations
import sqlite3
import os, re, glob
from pathlib import Path
from typing import Optional

_KB_ROOT = Path(__file__).resolve().parents[2] / "kb"
_DB_PATH = Path(__file__).resolve().parents[2] / "kb" / "kb_index.db"

def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(_DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def ensure_indexed() -> tuple[int, int]:
    """Index all .md files in kb/ into FTS5 if needed. Returns (new_docs, total_docs)."""
    conn = _connect()
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='kb_fts'")
    has_fts = cur.fetchone() is not None
    if not has_fts:
        cur.execute("CREATE VIRTUAL TABLE IF NOT EXISTS kb_fts USING fts5(title, body, path)")
    cur.execute("SELECT COUNT(*) FROM kb_fts")
    existing = cur.fetchone()[0]
    md_files = sorted(_KB_ROOT.rglob("*.md"))
    new = 0
    for f in md_files:
        rel = str(f.relative_to(_KB_ROOT))
        cur.execute("SELECT path FROM kb_fts WHERE path=?", (rel,))
        if cur.fetchone():
            continue
        with open(f) as fh:
            text = fh.read()
        title = f.stem.replace('_',' ').replace('-',' ')
        body = re.sub(r'#{1,6}\s*', '', text)
        body = re.sub(r'\*\*(.+?)\*\*', r'\1', body)
        body = re.sub(r'`(.+?)`', r'\1', body)
        cur.execute("INSERT INTO kb_fts(title, body, path) VALUES(?, ?, ?)", (title, body, rel))
        new += 1
    conn.commit()
    conn.close()
    return (new, existing + new) if new else (0, existing)

def search_kb(query: str, limit: int = 10) -> list[dict]:
    """Full-text search over indexed kb documents using FTS5 ranking."""
    conn = _connect()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM kb_fts")
    total = cur.fetchone()[0]
    if total == 0:
        ensure_indexed()
    tokens = query.split()
    safe_tokens = []
    for t in tokens:
        t = t.replace('.', '').replace('"', '').replace("'", "")
        if t:
            safe_tokens.append(f'"{t}"' if len(t) > 2 else t)
    match_expr = " ".join(safe_tokens)
    cur.execute("""
        SELECT path, title, snippet(kb_fts, 0, '**', '**', '…', 15) as snippet, rank as score
        FROM kb_fts
        WHERE kb_fts MATCH ?
        ORDER BY rank DESC
        LIMIT ?
    """, (match_expr, limit))
    rows = cur.fetchall()
    conn.close()
    return [{"path": r["path"], "title": r["title"], "snippet": r["snippet"], "score": r["score"]} for r in rows]

def get_document(path: str) -> Optional[str]:
    """Retrieve full content of a document by its kb/ relative path."""
    full_path = _KB_ROOT / path
    if not full_path.exists():
        return None
    with open(full_path) as f:
        return f.read()

def kb_status() -> dict:
    """Return index statistics."""
    conn = _connect()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM kb_fts")
    docs = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM kb_fts")
    chunks = cur.fetchone()[0]
    cur.execute("SELECT path FROM kb_fts ORDER BY path")
    paths = [r["path"] for r in cur.fetchall()]
    conn.close()
    return {"docs": docs, "chunks": chunks, "paths": len(paths)}
