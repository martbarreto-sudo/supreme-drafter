"""Testes de ingestão de PDF."""

from __future__ import annotations

import base64

import pytest

from deep_hunter.pdf_ingest import load_pdf_block


def _pdf_minimo() -> bytes:
    return b"%PDF-1.4\n%%EOF\n"


def test_carrega_pdf_valido(tmp_path):
    p = tmp_path / "autos.pdf"
    p.write_bytes(_pdf_minimo())
    block = load_pdf_block(p)
    assert block["type"] == "document"
    assert block["source"]["media_type"] == "application/pdf"
    assert base64.standard_b64decode(block["source"]["data"]) == _pdf_minimo()
    assert block["citations"]["enabled"] is True


def test_citations_desligavel(tmp_path):
    p = tmp_path / "autos.pdf"
    p.write_bytes(_pdf_minimo())
    block = load_pdf_block(p, citations=False)
    assert "citations" not in block


def test_rejeita_inexistente(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_pdf_block(tmp_path / "nao_existe.pdf")


def test_rejeita_vazio(tmp_path):
    p = tmp_path / "vazio.pdf"
    p.write_bytes(b"")
    with pytest.raises(ValueError):
        load_pdf_block(p)


def test_rejeita_nao_pdf(tmp_path):
    p = tmp_path / "fake.pdf"
    p.write_bytes(b"isto nao e um pdf")
    with pytest.raises(ValueError, match="magic bytes"):
        load_pdf_block(p)
