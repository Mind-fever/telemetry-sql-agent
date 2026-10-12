"""Carga los PDF de data/docs/ en la tabla doc_chunks: extrae el texto por pagina, lo fragmenta,
calcula los embeddings y lo guarda con el archivo y la pagina de origen.

Uso: python scripts/ingest_docs.py            (embeddings reales de Gemini, requiere GEMINI_API_KEY)
     python scripts/ingest_docs.py --fake     (embeddings falsos, solo para pruebas sin API key)
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

DOCS_DIR = ROOT / "data" / "docs"
MAX_CHARS = 900

# Cada pagina de los PDF trae un pie ("MAN-001 | Documento ficticio ..." y "Pagina N"). Se descarta
# para que no contamine todos los fragmentos.
_FOOTER = re.compile(r"^(?:[A-Z]{3}-\d{3} \| Documento ficticio.*|Pagina \d+)$")


def clean_page_text(text: str) -> list[str]:
    lines = [ln.strip() for ln in text.splitlines()]
    return [ln for ln in lines if ln and not _FOOTER.match(ln)]


def chunk_lines(lines: list[str], max_chars: int = MAX_CHARS) -> list[str]:
    """Agrupa lineas consecutivas hasta max_chars. Conserva la primera linea (el titulo de la
    seccion) como encabezado de cada fragmento para que no pierda contexto."""
    if not lines:
        return []
    heading = lines[0]
    body = lines[1:]
    chunks: list[str] = []
    current = [heading]
    size = len(heading)
    for ln in body:
        if size + len(ln) + 1 > max_chars and len(current) > 1:
            chunks.append("\n".join(current))
            current = [heading]
            size = len(heading)
        current.append(ln)
        size += len(ln) + 1
    if len(current) > 1 or not chunks:
        chunks.append("\n".join(current))
    return chunks


def chunks_from_pdf(path: Path) -> list[dict]:
    reader = PdfReader(str(path))
    out: list[dict] = []
    for page_number, page in enumerate(reader.pages, start=1):
        lines = clean_page_text(page.extract_text() or "")
        for order, text in enumerate(chunk_lines(lines), start=1):
            out.append({"archivo": path.name, "pagina": page_number, "orden": order, "texto": text})
    return out


def vector_literal(values: list[float]) -> str:
    return "[" + ",".join(f"{v:.7f}" for v in values) + "]"


def main() -> None:
    from telemetry_agent.db import connect_admin
    from telemetry_agent.embeddings import HashEmbedder, get_embedder

    fake = "--fake" in sys.argv
    embedder = HashEmbedder() if fake else get_embedder()
    if fake:
        print("AVISO: se usan embeddings falsos. Sirve para probar el flujo, no para respuestas reales.")

    pdfs = sorted(DOCS_DIR.glob("*.pdf"))
    if len(pdfs) < 2:
        raise SystemExit("Se necesitan al menos 2 PDF en data/docs/ (correr scripts/build_pdfs.py).")

    chunks: list[dict] = []
    for pdf in pdfs:
        chunks.extend(chunks_from_pdf(pdf))
    print(f"{len(pdfs)} PDF, {len(chunks)} fragmentos.")

    vectors = embedder.embed_documents([(c["archivo"], c["texto"]) for c in chunks])

    with connect_admin() as conn:
        with conn.cursor() as cur:
            cur.execute("truncate doc_chunks restart identity")
            # strict: si faltara un vector, falla en vez de descartar fragmentos sin avisar.
            for c, v in zip(chunks, vectors, strict=True):
                cur.execute(
                    "insert into doc_chunks (archivo, pagina, orden, texto, embedding) "
                    "values (%s, %s, %s, %s, %s::vector)",
                    (c["archivo"], c["pagina"], c["orden"], c["texto"], vector_literal(v)),
                )
            stored = cur.execute("select count(*) from doc_chunks").fetchone()[0]
        conn.commit()
    print(f"{stored} fragmentos cargados en doc_chunks.")


if __name__ == "__main__":
    main()
