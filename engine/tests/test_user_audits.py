"""Testes do histórico /user/audits — listagem, detalhe, isolamento."""

from __future__ import annotations

from dataclasses import dataclass

from nexus.quality import GateResult, QualityReport
from tests.conftest import signup_and_login


@dataclass
class _FakeMinuta:
    texto: str = "minuta de teste — texto completo"
    modelo: str = "mock-opus-4-8"
    input_tokens: int = 1234
    cache_read_tokens: int = 5678
    cache_creation_tokens: int = 0
    output_tokens: int = 500


def _payload() -> dict:
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
    }


def _mock_llm(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    import nexus.llm
    import nexus.quality
    monkeypatch.setattr(nexus.llm, "gerar_minuta", lambda *a, **kw: _FakeMinuta())
    monkeypatch.setattr(
        nexus.quality, "avaliar_qualidade",
        lambda *a, **kw: QualityReport(score=85, gates=[GateResult("g", True, "ok")]),
    )
    monkeypatch.setattr(nexus.llm, "validar_feito_hbm", lambda texto: [])


# ---------- /draft/llm grava Audit ----------


async def test_draft_llm_sucesso_grava_audit_e_minuta_em_disco(
    client, monkeypatch, tmp_path
):
    _mock_llm(monkeypatch)
    monkeypatch.setenv("CASO_DATA_DIR", str(tmp_path))
    user, token = signup_and_login(client)

    r = client.post(
        "/draft/llm",
        headers={"Authorization": f"Bearer {token}"},
        json=_payload(),
    )
    assert r.status_code == 200
    body = r.json()
    audit_id = body["audit_id"]
    assert audit_id is not None

    minuta_path = tmp_path / user["id"] / "audits" / f"{audit_id}.md"
    assert minuta_path.read_text(encoding="utf-8") == "minuta de teste — texto completo"


async def test_draft_llm_sem_caso_data_dir_devolve_audit_id_none(
    client, monkeypatch
):
    """Sem CASO_DATA_DIR a geração ainda responde, mas audit_id é None."""
    _mock_llm(monkeypatch)
    monkeypatch.delenv("CASO_DATA_DIR", raising=False)
    _, token = signup_and_login(client)

    r = client.post(
        "/draft/llm",
        headers={"Authorization": f"Bearer {token}"},
        json=_payload(),
    )
    assert r.status_code == 200
    assert r.json()["audit_id"] is None
    assert r.json()["texto"] == "minuta de teste — texto completo"


# ---------- GET /user/audits ----------


async def test_list_audits_sem_jwt_401(client):
    r = client.get("/user/audits")
    assert r.status_code == 401


async def test_list_audits_vazio_no_inicio(client):
    _, token = signup_and_login(client)
    r = client.get("/user/audits", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json() == []


async def test_list_audits_apos_geracoes(client, monkeypatch, tmp_path):
    _mock_llm(monkeypatch)
    monkeypatch.setenv("CASO_DATA_DIR", str(tmp_path))
    _, token = signup_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}

    # Gera 3 peças (= trial inteiro)
    for _ in range(3):
        r = client.post("/draft/llm", headers=headers, json=_payload())
        assert r.status_code == 200

    r = client.get("/user/audits", headers=headers)
    assert r.status_code == 200
    audits = r.json()
    assert len(audits) == 3
    for a in audits:
        assert a["feito_id"] == "Feito-HBM"
        assert a["peca_tipo"] == "HC"
        assert a["quality_score"] == 85
        assert a["modelo"] == "mock-opus-4-8"


async def test_list_audits_paginacao(client, monkeypatch, tmp_path):
    _mock_llm(monkeypatch)
    monkeypatch.setenv("CASO_DATA_DIR", str(tmp_path))
    _, token = signup_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}

    for _ in range(3):
        client.post("/draft/llm", headers=headers, json=_payload())

    r = client.get(
        "/user/audits?limit=2&offset=0", headers=headers
    )
    assert r.status_code == 200
    assert len(r.json()) == 2

    r = client.get(
        "/user/audits?limit=2&offset=2", headers=headers
    )
    assert r.status_code == 200
    assert len(r.json()) == 1


async def test_list_audits_retorna_todos_os_3_gerados(client, monkeypatch, tmp_path):
    """Verifica que os 3 audits aparecem na lista. Ordenação estrita por
    created_at é testada em produção (Postgres tem microsecond resolution);
    SQLite pode dar timestamps idênticos em inserts sub-ms."""
    _mock_llm(monkeypatch)
    monkeypatch.setenv("CASO_DATA_DIR", str(tmp_path))
    _, token = signup_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}

    ids = []
    for _ in range(3):
        r = client.post("/draft/llm", headers=headers, json=_payload())
        ids.append(r.json()["audit_id"])

    r = client.get("/user/audits", headers=headers)
    returned_ids = {a["id"] for a in r.json()}
    assert returned_ids == set(ids)


# ---------- GET /user/audits/{id} ----------


async def test_get_audit_detail_devolve_minuta(client, monkeypatch, tmp_path):
    _mock_llm(monkeypatch)
    monkeypatch.setenv("CASO_DATA_DIR", str(tmp_path))
    _, token = signup_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}

    r = client.post("/draft/llm", headers=headers, json=_payload())
    audit_id = r.json()["audit_id"]

    r = client.get(f"/user/audits/{audit_id}", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == audit_id
    assert body["minuta"] == "minuta de teste — texto completo"
    assert body["usage"]["input_tokens"] == 1234
    assert body["usage"]["cache_read_tokens"] == 5678
    assert body["usage"]["output_tokens"] == 500


async def test_get_audit_inexistente_404(client):
    _, token = signup_and_login(client)
    r = client.get(
        "/user/audits/nao-existe-este-id",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 404


async def test_get_audit_de_outro_user_retorna_404(client, monkeypatch, tmp_path):
    """Isolamento: user_a não consegue ver audit de user_b. 404, não 403
    (para não vazar que o ID existe)."""
    _mock_llm(monkeypatch)
    monkeypatch.setenv("CASO_DATA_DIR", str(tmp_path))

    _, token_a = signup_and_login(client, email="a@x.com")
    _, token_b = signup_and_login(client, email="b@x.com")

    r = client.post(
        "/draft/llm",
        headers={"Authorization": f"Bearer {token_b}"},
        json=_payload(),
    )
    audit_id_b = r.json()["audit_id"]

    r = client.get(
        f"/user/audits/{audit_id_b}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert r.status_code == 404


async def test_get_audit_arquivo_apagado_410(client, monkeypatch, tmp_path):
    """Se o arquivo da minuta sumiu do disco, retorna 410 Gone."""
    _mock_llm(monkeypatch)
    monkeypatch.setenv("CASO_DATA_DIR", str(tmp_path))
    user, token = signup_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}

    r = client.post("/draft/llm", headers=headers, json=_payload())
    audit_id = r.json()["audit_id"]

    # Simula arquivo apagado (operação de filesystem externa)
    (tmp_path / user["id"] / "audits" / f"{audit_id}.md").unlink()

    r = client.get(f"/user/audits/{audit_id}", headers=headers)
    assert r.status_code == 410
