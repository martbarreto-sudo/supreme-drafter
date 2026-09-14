"""Testes da extração de texto em PDF (stdlib pura, sem rede).

Cobrem a regressão que motivou o módulo: num PDF real o texto vive em *content
streams* comprimidos, e a varredura anterior — `latin-1` sobre os bytes crus — não
encontrava nada. Consequência: autos que traziam hash, ata de plenário e portaria
eram auditados como se nada trouxessem, gerando nulidades falsas.
"""

from __future__ import annotations

from conftest import build_pdf as _build_pdf, hex_utf16 as _hex_utf16

from deep_hunter.mock_auditor import audit_pdf_bytes
from deep_hunter.pdf_text import extract_text, normalizar


# ── Extração ────────────────────────────────────────────────────────────────


def test_extrai_texto_de_stream_comprimido():
    """O caso que a varredura crua não cobria: /FlateDecode."""
    pdf = _build_pdf(b"BT /F1 12 Tf 72 720 Td (laudo com hash sha-256 verificado) Tj ET")
    assert "laudo com hash sha-256 verificado" in extract_text(pdf)


def test_extrai_texto_de_stream_nao_comprimido():
    pdf = _build_pdf(b"BT (ata de plenario juntada) Tj ET", compress=False)
    assert "ata de plenario juntada" in extract_text(pdf)


def test_remonta_palavra_partida_por_kerning_em_vector_TJ():
    """`[(cont) -20 (emporaneidade)] TJ` tem de voltar a ser uma só palavra."""
    pdf = _build_pdf(b"BT [(cont) -20 (emporan) 15 (eidade)] TJ ET")
    assert "contemporaneidade" in extract_text(pdf)


def test_remonta_palavra_partida_por_kerning_fraccionario():
    """Ajustes reais raramente são inteiros: `-12.5` não pode descartar o lote."""
    pdf = _build_pdf(b"BT [(cont) -12.5 (emporan) 7.25 (eidade)] TJ ET")
    assert "contemporaneidade" in extract_text(pdf)


def test_le_string_hexadecimal_em_utf16():
    pdf = _build_pdf(b"BT " + _hex_utf16("ata de plenário") + b" Tj ET")
    assert "plenário" in extract_text(pdf)


def test_trata_escapes_parenteses_aninhados_e_octais():
    conteudo = rb"BT (portaria \(designa\347\343o\) extraordin\341ria (aninhado)) Tj ET"
    texto = extract_text(_build_pdf(conteudo))
    assert "portaria (designação) extraordinária (aninhado)" in texto


def test_ignora_strings_que_nao_sao_exibidas():
    """Só o que passa por um operador de exibição conta como texto da página."""
    pdf = _build_pdf(b"BT [(vis) (ivel)] TJ ET (oculto) Do")
    texto = extract_text(pdf)
    assert "visivel" in texto
    assert "oculto" not in texto


def test_operadores_de_aspas_tambem_exibem():
    pdf = _build_pdf(b"BT (linha um) ' 1 2 (linha dois) \" ET")
    texto = extract_text(pdf)
    assert "linha um" in texto and "linha dois" in texto


def test_stream_binario_nao_textual_nao_rebenta():
    pdf = _build_pdf(bytes(range(256)) * 4, compress=False, filtro=b"/DCTDecode")
    extract_text(pdf)  # não deve levantar


def test_lixo_binario_entre_parenteses_nao_vira_facto_dos_autos():
    """Um stream de imagem não é texto — o que lá estiver não pode virar prova."""
    lixo = b"\xff\xd8(hash sha-256 falso vindo de um JPEG)\xff\xd9" * 3
    pdf = _build_pdf(lixo, compress=False, filtro=b"/DCTDecode")
    assert "hash" not in extract_text(pdf)
    # E o auditor mantém a custódia sinalizada: não há hash legítimo nos autos.
    assert audit_pdf_bytes(pdf).auditoria_custodia[0].possui_quebra_custodia is True


def test_resgate_cru_nao_varre_binario_de_pdf_com_streams():
    """Havendo streams, a resposta honesta a uma extração falhada é cadeia vazia."""
    pdf = _build_pdf(b"\x00\x01 sem qualquer marca de texto \x02", compress=False)
    assert extract_text(pdf) == ""


def test_extract_text_nunca_levanta_em_lixo():
    for lixo in (b"", b"%PDF-1.4\n", b"\x00\xff" * 100, b"%PDF-1.4\nstream\n"):
        assert isinstance(extract_text(lixo), str)


def test_recorre_a_varredura_crua_quando_nao_ha_stream():
    """PDFs lineares sem stream (as fixtures do gateway) continuam a ser lidos."""
    assert "hash" in extract_text(b"%PDF-1.4\nlaudo com hash sha-256\n%%EOF\n")


# ── Normalização ────────────────────────────────────────────────────────────


def test_normalizar_remove_acentos_e_colapsa_espacos():
    assert normalizar("ATA de PLENÁRIO\n  juntada") == "ata de plenario juntada"
    assert normalizar("Contemporaneidade") == "contemporaneidade"


# ── Regressão de ponta a ponta no auditor ───────────────────────────────────


def test_auditor_le_pdf_comprimido_e_nao_fabrica_nulidades():
    """Regressão: autos comprimidos COM hash/ata/portaria não podem sair sinalizados."""
    pdf = _build_pdf(
        b"BT (laudo com hash sha-256 verificado; ata de plenario juntada; portaria de "
        b"designacao extraordinaria; analise de contemporaneidade da preventiva) Tj ET"
    )
    d = audit_pdf_bytes(pdf)
    assert d.auditoria_custodia[0].possui_quebra_custodia is False
    assert d.omissao_analise_contemporaneidade is False
    assert d.ausencia_ata_plenario is False
    assert d.auditoria_magistrados[0].possui_desvio is True


def test_auditor_detecta_termos_acentuados_em_pdf_comprimido():
    """`plenário` acentuado tem de valer tanto quanto `plenario`."""
    pdf = _build_pdf(b"BT " + _hex_utf16("ata de plenário juntada aos autos") + b" Tj ET")
    assert audit_pdf_bytes(pdf).ausencia_ata_plenario is False


def test_auditor_mantem_sinalizacao_em_pdf_comprimido_seco():
    """Sem os termos, as omissões continuam a ser sinalizadas — sem falsos negativos."""
    pdf = _build_pdf(b"BT (peticao inicial sem qualquer laudo tecnico) Tj ET")
    d = audit_pdf_bytes(pdf)
    assert d.auditoria_custodia[0].possui_quebra_custodia is True
    assert d.omissao_analise_contemporaneidade is True
    assert d.ausencia_ata_plenario is True


def test_auditoria_de_pdf_comprimido_e_deterministica():
    pdf = _build_pdf(b"BT (laudo com hash sha-256) Tj ET")
    assert audit_pdf_bytes(pdf).model_dump() == audit_pdf_bytes(pdf).model_dump()
