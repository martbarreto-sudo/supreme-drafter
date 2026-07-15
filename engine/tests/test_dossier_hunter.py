"""Testes do DossierHunterSchema — validadores condicionais + adapter.

Cobertura:
- validadores cruzados (coerência de portaria, integridade de hash, ordem da lacuna)
- rejeição de NPU fora do padrão CNJ (ValidationError → 422 no endpoint)
- adapter dossier → fontes_silenciadas (só OMISSÕES)
- integração /draft/llm: dossiê enriquece a Auditoria de Silêncio do romaneio
- aviso LGPD quando segredo_justica

Rede isolada: nenhum teste toca PJe real; todos os dados são sintéticos.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone

import pytest
from pydantic import ValidationError

from nexus.dossier import dossier_para_fontes_silenciadas
from nexus.dossier.schema import (
    AtoProcessual,
    DadosBasicos,
    DesvioMagistrado,
    DossierHunterSchema,
    FiltrosOmissao,
    LacunaSequencial,
    MidiaPericia,
    Proveniencia,
)
from nexus.models import DraftRequest, FontePrimaria
from nexus.quality import GateResult, QualityReport
from tests.conftest import signup_and_login


# ---------- fábricas ----------


def _dados_basicos(**kw) -> DadosBasicos:
    base = dict(
        npu="1000214-45.2023.8.17.4002",
        tribunal="TJPE",
        orgao_julgador="2ª Vara Criminal",
        classe="Ação Penal",
    )
    base.update(kw)
    return DadosBasicos(**base)


def _proveniencia() -> Proveniencia:
    return Proveniencia(capturado_em=datetime(2026, 6, 1, tzinfo=timezone.utc))


# ---------- DadosBasicos / NPU ----------


def test_npu_valido_aceita():
    d = _dados_basicos()
    assert d.npu == "1000214-45.2023.8.17.4002"


@pytest.mark.parametrize(
    "npu_ruim",
    [
        "1000214-45.2023.8.17.400",   # OOOO curto
        "abc",                        # lixo
        "10002144520238174002",       # sem máscara
        "1000214-45.2023.817.4002",   # TR/J colados
    ],
)
def test_npu_invalido_rejeita(npu_ruim):
    with pytest.raises(ValidationError):
        _dados_basicos(npu=npu_ruim)


# ---------- DesvioMagistrado: coerência de portaria ----------


def test_desvio_sem_portaria_e_omissao():
    d = DesvioMagistrado(
        juiz_prolator="Juiz Substituto",
        data_ato=date(2023, 5, 10),
        ato_referencia="evt-42",
    )
    assert d.portaria_publica_localizada is False
    assert d.eh_omissao is True


def test_desvio_com_portaria_forca_booleano_true():
    """Mesmo passando o booleano errado, o validator força coerência."""
    d = DesvioMagistrado(
        juiz_prolator="Juiz Substituto",
        data_ato=date(2023, 5, 10),
        ato_referencia="evt-42",
        portaria_designacao=FontePrimaria(uri="portaria://tjpe/123-2023"),
        portaria_publica_localizada=False,  # errado de propósito
    )
    assert d.portaria_publica_localizada is True
    assert d.eh_omissao is False


def test_desvio_sem_portaria_com_booleano_true_e_forcado_false():
    d = DesvioMagistrado(
        juiz_prolator="X",
        data_ato=date(2023, 5, 10),
        ato_referencia="evt-1",
        portaria_publica_localizada=True,  # errado de propósito
    )
    assert d.portaria_publica_localizada is False


# ---------- MidiaPericia: integridade de hash ----------


def test_midia_hash_presente_exige_algoritmo_e_valor():
    with pytest.raises(ValidationError):
        MidiaPericia(
            id_documento="doc-9",
            tipo_midia="VIDEO",
            hash_presente=True,  # sem algoritmo/valor → ValueError
        )


def test_midia_hash_presente_completo_aceita():
    m = MidiaPericia(
        id_documento="doc-9",
        tipo_midia="VIDEO",
        hash_presente=True,
        hash_algoritmo="SHA-256",
        hash_valor="deadbeef",
        cadeia_custodia_integra=True,
    )
    assert m.hash_algoritmo == "SHA-256"


def test_midia_sem_hash_aceita_sem_algoritmo():
    m = MidiaPericia(id_documento="doc-9", tipo_midia="AUDIO", hash_presente=False)
    assert m.hash_presente is False


# ---------- LacunaSequencial ----------


def test_lacuna_ate_menor_que_de_rejeita():
    with pytest.raises(ValidationError):
        LacunaSequencial(de=50, ate=40)


def test_lacuna_valida_aceita():
    g = LacunaSequencial(de=40, ate=50, contexto="entre denúncia e recebimento")
    assert g.ate - g.de == 10


# ---------- AtoProcessual (AFIRMAÇÃO exige fonte) ----------


def test_ato_processual_exige_fonte():
    with pytest.raises(ValidationError):
        AtoProcessual(id_evento="e1", data=date(2023, 1, 1), tipo_documento="DESPACHO")


# ---------- adapter → fontes_silenciadas ----------


def _dossier_rico() -> DossierHunterSchema:
    return DossierHunterSchema(
        dados_basicos=_dados_basicos(),
        auditoria_magistrados=[
            DesvioMagistrado(
                juiz_prolator="Juiz Substituto A",
                data_ato=date(2023, 5, 10),
                ato_referencia="evt-42",
            ),  # OMISSÃO (sem portaria)
            DesvioMagistrado(
                juiz_prolator="Juiz Titular",
                data_ato=date(2023, 6, 1),
                ato_referencia="evt-50",
                portaria_designacao=FontePrimaria(uri="portaria://tjpe/xpto"),
            ),  # regular — NÃO é omissão
        ],
        midias_e_pericias=[
            MidiaPericia(id_documento="mid-1", tipo_midia="AUDIO", hash_presente=False),
            MidiaPericia(
                id_documento="mid-2",
                tipo_midia="VIDEO",
                hash_presente=True,
                hash_algoritmo="MD5",
                hash_valor="abc",
                cadeia_custodia_integra=True,
            ),  # íntegra — NÃO é omissão
        ],
        filtros_omissao=FiltrosOmissao(
            omissao_analise_contemporaneidade=True,
            ausencia_ata_plenario=True,
            quebra_sequencial_ids=[LacunaSequencial(de=40, ate=45, contexto="sumiço")],
            omissoes_livres=["Laudo complementar do IML não juntado"],
        ),
        proveniencia=_proveniencia(),
    )


def test_adapter_extrai_apenas_omissoes():
    linhas = dossier_para_fontes_silenciadas(_dossier_rico())

    # desvio de juiz natural (só o sem portaria)
    assert any("Juiz Substituto A" in ln for ln in linhas)
    assert not any("Juiz Titular" in ln for ln in linhas)

    # cadeia de custódia (só a mídia sem hash)
    assert any("mid-1" in ln for ln in linhas)
    assert not any("mid-2" in ln for ln in linhas)

    # filtros
    assert any("contemporaneidade" in ln for ln in linhas)
    assert any("Ata da sessão plenária" in ln for ln in linhas)
    assert any("40–45" in ln and "sumiço" in ln for ln in linhas)
    assert "Laudo complementar do IML não juntado" in linhas


def test_adapter_dossier_vazio_devolve_lista_vazia():
    d = DossierHunterSchema(dados_basicos=_dados_basicos(), proveniencia=_proveniencia())
    assert dossier_para_fontes_silenciadas(d) == []


# ---------- DraftRequest com dossier opcional ----------


def test_draftrequest_dossier_default_none():
    req = DraftRequest(
        feito_id="Feito-HBM",
        peca_tipo="HC",
        fatos=[{"id": "f1", "proposto": "X", "dispositivo": False}],
    )
    assert req.dossier is None


def test_draftrequest_aceita_dossier():
    req = DraftRequest(
        feito_id="Feito-HBM",
        peca_tipo="HC",
        fatos=[{"id": "f1", "proposto": "X", "dispositivo": False}],
        dossier=_dossier_rico(),
    )
    assert req.dossier is not None
    assert req.dossier.dados_basicos.tribunal == "TJPE"


# ---------- integração /draft/llm ----------


@dataclass
class _FakeMinuta:
    texto: str = "Excelentíssimo. minuta de teste"
    modelo: str = "mock-model"
    input_tokens: int = 100
    cache_read_tokens: int = 0
    cache_creation_tokens: int = 0
    output_tokens: int = 50


def _mock_llm(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    import nexus.llm
    import nexus.quality
    monkeypatch.setattr(nexus.llm, "gerar_minuta", lambda *a, **kw: _FakeMinuta())
    monkeypatch.setattr(
        nexus.quality, "avaliar_qualidade",
        lambda *a, **kw: QualityReport(score=80, gates=[GateResult("g", True, "ok")]),
    )
    monkeypatch.setattr(nexus.llm, "validar_feito_hbm", lambda texto: [])


def _payload_com_dossier(segredo: bool = False) -> dict:
    return {
        "feito_id": "Feito-HBM",
        "peca_tipo": "HC",
        "fatos": [
            {
                "id": "f1",
                "proposto": "X",
                "verificado": "X confirmado",
                "fonte": {"uri": "certidao://feito-hbm/fls-1"},
            }
        ],
        "dossier": {
            "dados_basicos": {
                "npu": "1000214-45.2023.8.17.4002",
                "tribunal": "TJPE",
                "orgao_julgador": "2ª Vara Criminal",
                "classe": "Ação Penal",
                "segredo_justica": segredo,
            },
            "auditoria_magistrados": [
                {
                    "juiz_prolator": "Juiz Substituto A",
                    "data_ato": "2023-05-10",
                    "ato_referencia": "evt-42",
                }
            ],
            "proveniencia": {"capturado_em": "2026-06-01T00:00:00Z"},
        },
    }


async def test_draft_llm_dossier_enriquece_romaneio(client, monkeypatch, tmp_path):
    _mock_llm(monkeypatch)
    monkeypatch.setenv("CASO_DATA_DIR", str(tmp_path))
    _, token = signup_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}

    r = client.post("/draft/llm", headers=headers, json=_payload_com_dossier())
    assert r.status_code == 200
    body = r.json()
    assert body["dossier"]["presente"] is True
    assert any(
        "Juiz Substituto A" in ln for ln in body["dossier"]["auditoria_silencio"]
    )
    assert body["dossier"]["segredo_justica_aviso"] is None

    audit_id = body["audit_id"]
    rom = client.get(f"/user/audits/{audit_id}/romaneio", headers=headers)
    assert rom.status_code == 200
    assert "Juiz Substituto A" in rom.text  # omissão do dossiê no romaneio


async def test_draft_llm_dossier_segredo_dispara_aviso(client, monkeypatch, tmp_path):
    _mock_llm(monkeypatch)
    monkeypatch.setenv("CASO_DATA_DIR", str(tmp_path))
    _, token = signup_and_login(client)

    r = client.post(
        "/draft/llm",
        headers={"Authorization": f"Bearer {token}"},
        json=_payload_com_dossier(segredo=True),
    )
    assert r.status_code == 200
    aviso = r.json()["dossier"]["segredo_justica_aviso"]
    assert aviso is not None
    assert "segredo de justiça" in aviso


async def test_draft_llm_dossier_npu_invalido_422(client, monkeypatch):
    _mock_llm(monkeypatch)
    _, token = signup_and_login(client)
    payload = _payload_com_dossier()
    payload["dossier"]["dados_basicos"]["npu"] = "formato-errado"
    r = client.post(
        "/draft/llm",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert r.status_code == 422


async def test_draft_llm_sem_dossier_segue_normal(client, monkeypatch, tmp_path):
    _mock_llm(monkeypatch)
    monkeypatch.setenv("CASO_DATA_DIR", str(tmp_path))
    _, token = signup_and_login(client)
    payload = _payload_com_dossier()
    del payload["dossier"]
    r = client.post(
        "/draft/llm",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert r.status_code == 200
    assert r.json()["dossier"]["presente"] is False
    assert r.json()["dossier"]["auditoria_silencio"] == []