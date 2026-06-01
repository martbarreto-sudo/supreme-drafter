"""Testes do AUDITOR FORENSE adversarial — os 5 gates do TIER 0 §4."""

from __future__ import annotations

from nexus.auditor.service import (
    Severity,
    auditar_adversarial,
)
from nexus.models import Fato, FontePrimaria, StatusFato


def _fato_disp(id_, proposto, verificado=None, fonte_uri=None):
    return Fato(
        id=id_,
        proposto=proposto,
        verificado=verificado,
        fonte=FontePrimaria(uri=fonte_uri) if fonte_uri else None,
        status=StatusFato.LIQUIDO if verificado else StatusFato.PENDENTE,
        dispositivo=True,
    )


_MINUTA_ENDERECAMENTO = (
    "EXCELENTÍSSIMO SENHOR DOUTOR JUIZ DE DIREITO DA VARA CRIMINAL DA "
    "COMARCA DE OLINDA/PE\n\n"
)


# ---------- Passo 1: cegueira deliberada ----------


def test_cegueira_deliberada_silencia_fato_dispositivo():
    fato = _fato_disp(
        "f1",
        "Apreensão de aparelho celular sem hash criptográfico documentado",
        verificado="O laudo pericial não registra hash MD5 ou SHA-256 do aparelho apreendido",
    )
    # Minuta NÃO menciona hash nem laudo nem pericial
    minuta = _MINUTA_ENDERECAMENTO + "Trata-se de imputação de tráfico de drogas."
    r = auditar_adversarial(minuta, [fato])
    codes = [f.code for f in r.findings]
    assert "cegueira_deliberada" in codes
    assert r.decisao == "REPROVA"


def test_cegueira_deliberada_eco_substantivo_passa():
    fato = _fato_disp(
        "f1",
        "Apreensão de celular sem hash",
        verificado="O laudo não registra hash MD5 do aparelho celular apreendido",
    )
    minuta = (
        _MINUTA_ENDERECAMENTO
        + "O laudo pericial omitiu o hash MD5 do aparelho celular apreendido, "
        "vício insuperável da cadeia de custódia."
    )
    r = auditar_adversarial(minuta, [fato])
    assert not any(f.code == "cegueira_deliberada" for f in r.findings)


def test_fato_nao_dispositivo_nao_dispara_cegueira():
    fato = Fato(
        id="f1",
        proposto="Argumento hipotético sobre estatística",
        dispositivo=False,
    )
    minuta = _MINUTA_ENDERECAMENTO + "Texto sem relação."
    r = auditar_adversarial(minuta, [fato])
    assert not any(f.code == "cegueira_deliberada" for f in r.findings)


# ---------- Passo 2: citação não verificada ----------


def test_citacao_sumula_sem_fonte_dispara_media():
    minuta = (
        _MINUTA_ENDERECAMENTO
        + "Aplica-se a Súmula 691 do STF ao caso."
    )
    r = auditar_adversarial(minuta, [])
    findings_cit = [f for f in r.findings if f.code == "citacao_nao_verificada"]
    assert len(findings_cit) >= 1
    assert findings_cit[0].severity == Severity.MEDIA


def test_citacao_com_fonte_no_dado_liquido_passa():
    fato = _fato_disp(
        "f1",
        "Reconhecimento fotográfico isolado",
        verificado="STJ HC 598.886 fixou nulidade do reconhecimento por foto isolada",
        fonte_uri="certidao://feito-x/fls-12",
    )
    minuta = (
        _MINUTA_ENDERECAMENTO
        + "O STJ no HC 598.886 fixou a nulidade do reconhecimento por foto isolada."
    )
    r = auditar_adversarial(minuta, [fato])
    citacoes = [f for f in r.findings if f.code == "citacao_nao_verificada"]
    # número 598.886 está no fato verificado → não dispara
    assert not citacoes


# ---------- Passo 3: vocabulário vetado ----------


def test_data_venia_dispara_alta():
    minuta = _MINUTA_ENDERECAMENTO + "Data venia, a decisão merece reforma."
    r = auditar_adversarial(minuta, [])
    veto = [f for f in r.findings if f.code == "vocabulario_vetado"]
    assert veto and veto[0].severity == Severity.ALTA
    assert r.decisao == "REPROVA"


def test_ousamos_dispara_alta():
    minuta = _MINUTA_ENDERECAMENTO + "Ousamos discordar do entendimento."
    r = auditar_adversarial(minuta, [])
    assert any(f.code == "vocabulario_vetado" for f in r.findings)


def test_esquizofrenia_fatica_dispara_alta():
    minuta = (
        _MINUTA_ENDERECAMENTO
        + "Há esquizofrenia fática na denúncia que merece atenção."
    )
    r = auditar_adversarial(minuta, [])
    assert any(f.code == "vocabulario_vetado" for f in r.findings)


# ---------- Passo 4: autoelogio ----------


def test_autoelogio_tese_fulminante_dispara_media():
    minuta = (
        _MINUTA_ENDERECAMENTO
        + "A presente tese é fulminante e desmonta toda a denúncia."
    )
    r = auditar_adversarial(minuta, [])
    autos = [f for f in r.findings if f.code == "autoelogio"]
    assert autos and autos[0].severity == Severity.MEDIA


def test_destruicao_cientifica_dispara_media():
    minuta = _MINUTA_ENDERECAMENTO + "Procede-se à destruição científica da denúncia."
    r = auditar_adversarial(minuta, [])
    assert any(f.code == "autoelogio" for f in r.findings)


# ---------- Passo 5: endereçamento ----------


def test_sem_enderecamento_dispara_alta():
    minuta = "Trata-se de pedido de revogação de prisão preventiva."
    r = auditar_adversarial(minuta, [])
    assert any(f.code == "enderecamento_ausente" for f in r.findings)
    assert r.decisao == "REPROVA"


def test_com_enderecamento_mm_juizo_passa():
    minuta = "Ao MM. Juízo da 1ª Vara Criminal. Trata-se de pedido."
    r = auditar_adversarial(minuta, [])
    assert not any(f.code == "enderecamento_ausente" for f in r.findings)


def test_com_enderecamento_egregio_tribunal_passa():
    minuta = "Egrégio Tribunal de Justiça. Trata-se de habeas corpus."
    r = auditar_adversarial(minuta, [])
    assert not any(f.code == "enderecamento_ausente" for f in r.findings)


# ---------- decisao agregada ----------


def test_decisao_aprova_curadoria_com_zero_findings():
    minuta = (
        _MINUTA_ENDERECAMENTO
        + "Trata-se de pedido fundamentado em precedentes verificados."
    )
    r = auditar_adversarial(minuta, [])
    assert r.decisao == "APROVA_PARA_CURADORIA"
    assert r.findings == []


def test_decisao_com_ressalvas_so_media():
    """Citação sem fonte (MEDIA) + endereçamento OK + sem fato dispositivo."""
    minuta = _MINUTA_ENDERECAMENTO + "Aplica-se a Súmula 691."
    r = auditar_adversarial(minuta, [])
    assert r.decisao == "APROVA_PARA_CURADORIA_COM_RESSALVAS"


def test_to_dict_serializa_estrutura():
    minuta = "Sem endereçamento. Data venia."
    r = auditar_adversarial(minuta, [])
    d = r.to_dict()
    assert d["decisao"] == "REPROVA"
    assert d["total_por_severidade"]["ALTA"] >= 2
    assert all("code" in f and "severity" in f for f in d["findings"])
