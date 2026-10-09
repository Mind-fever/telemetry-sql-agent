"""Pruebas de la fragmentacion de PDF: conserva archivo y pagina, y no arrastra el pie de pagina."""

from __future__ import annotations

from pathlib import Path

import ingest_docs

DOCS = Path(__file__).resolve().parents[1] / "data" / "docs"


def test_footer_lines_are_removed():
    lines = ingest_docs.clean_page_text(
        "MAN-001 | Documento ficticio elaborado con fines academicos. No debe usarse en una instalacion real.\n"
        "Pagina 4\n3. Motores electricos\nAplica a M-301 a M-310.\n"
    )
    assert lines == ["3. Motores electricos", "Aplica a M-301 a M-310."]


def test_long_pages_split_and_keep_the_heading():
    lines = ["Titulo de seccion"] + [f"linea {i} " + "x" * 120 for i in range(20)]
    chunks = ingest_docs.chunk_lines(lines, max_chars=400)
    assert len(chunks) > 1
    assert all(c.startswith("Titulo de seccion") for c in chunks)
    assert all(len(c) <= 400 + 140 for c in chunks)


def test_every_pdf_chunk_has_file_and_page():
    pdfs = sorted(DOCS.glob("*.pdf"))
    assert len(pdfs) >= 2
    for pdf in pdfs:
        chunks = ingest_docs.chunks_from_pdf(pdf)
        assert chunks
        for c in chunks:
            assert c["archivo"] == pdf.name
            assert c["pagina"] >= 1
            assert " | Documento ficticio" not in c["texto"]  # el pie de pagina no debe quedar en el texto


def test_known_fact_lands_in_the_expected_page():
    chunks = ingest_docs.chunks_from_pdf(DOCS / "manual_mantenimiento_preventivo.pdf")
    hits = [c for c in chunks if "2.500 horas" in c["texto"]]
    assert len(hits) == 1
    assert hits[0]["pagina"] == 4
