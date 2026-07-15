"""Testes de integração do POST /draft/llm — JWT + cota + HALT.

Mocka `gerar_minuta`, `avaliar_qualidade` e `validar_feito_hbm` para
evitar chamada à Anthropic API. Cobertura:
- Sem JWT → 401
- Sem assinatura → 402 (impossível na prática: signup cria trial; teste
  defensivo construindo User manualmente sem subscription)
- Quota esgotada → 402 e não chama LLM
- Período expirado → 402
- HALT (fato sem fonte) → 422 e NÃO consome peça
- Sucesso → 200, consome peça, retorna billing info
- Feito não catalogado → 404 antes da cota
"""

from __future__ import annotations

from dataclasses import dataclass


from nexus.billing.service import find_subscription
from nexus.db.models import SubscriptionStatus
from nexus.quality import GateResult, QualityReport
from tests.conftest import signup_and_login


@dataclass
class _FakeMinuta:
    texto: str = "minuta de teste"
    modelo: str = "mock-model"
    input_tokens: int = 100
    cache_read_tokens: int = 0
    cache_creation_tokens: int = 0
    output_tokens: int = 50


def _payload_valido() -> dict:
    return {
        "feito_id": "Feito-HBM",
        "peca_tipo": "HC",
        "fatos": [
            {
                "id": "f1",
                "proposto": "Fato proposto",
                "verificado": "Fato verificado",
                "fonte": {"uri": "certidao://feito-hbm/fls-1"},
            }
        ],
    }


def _mock_llm_pipeline(monkeypatch, falhas: list[str] | None = None) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setattr("nexus.api.gerar_minuta", lambda *a, **kw: _FakeMinuta(), raising=False)
    monkeypatch.setattr(
        "nexus.api.avaliar_qualidade",
        lambda *a, **kw: QualityReport(score=80, gates=[GateResult("g", True, "ok")]),
        raising=False,
    )
    monkeypatch.setattr("nexus.api.validar_feito_hbm", lambda texto: falhas or [], raising=False)
    # As importações em api.py são lazy (dentro da função). Para o patch
    # alcançá-las, fazemos um eager-import no namespace de nexus.api:
    import nexus.llm
    import nexus.quality
    monkeypatch.setattr(nexus.llm, "gerar_minuta", lambda *a, **kw: _FakeMinuta())
    monkeypatch.setattr(
        nexus.quality, "avaliar_qualidade",
        lambda *a, **kw: QualityReport(score=80, gates=[GateResult("g", True, "ok")]),
    )
    monkeypatch.setattr(nexus.llm, "validar_feito_hbm", lambda texto: falhas or [])


async def test_draft_llm_sem_jwt_401(client, monkeypatch):
    _mock_llm_pipeline(monkeypatch)
    r = client.post("/draft/llm", json=_payload_valido())
    assert r.status_code == 401


async def test_draft_llm_sem_anthropic_key_503(client, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    _, token = signup_and_login(client)
    r = client.post(
        "/draft/llm",
        headers={"Authorization": f"Bearer {token}"},
        json=_payload_valido(),
    )
    assert r.status_code == 503


async def test_draft_llm_feito_inexistente_404(client, monkeypatch):
    _mock_llm_pipeline(monkeypatch)
    _, token = signup_and_login(client)
    payload = _payload_valido()
    payload["feito_id"] = "Feito-Inexistente"
    r = client.post(
        "/draft/llm",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert r.status_code == 404


async def test_draft_llm_halt_nao_consome_peca(client, monkeypatch, db_session):
    _mock_llm_pipeline(monkeypatch)
    user, token = signup_and_login(client)

    # fato sem fonte (e sem verificado) → HALT deve disparar
    payload = _payload_valido()
    payload["fatos"] = [{"id": "f1", "proposto": "X aconteceu"}]
    r = client.post(
        "/draft/llm",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert r.status_code == 422

    sub = await find_subscription(db_session, user["id"])
    assert sub.pecas_consumidas_no_periodo == 0


async def test_draft_llm_quota_esgotada_402(client, monkeypatch, db_session):
    _mock_llm_pipeline(monkeypatch)
    user, token = signup_and_login(client)

    sub = await find_subscription(db_session, user["id"])
    sub.pecas_consumidas_no_periodo = sub.pecas_incluidas
    await db_session.commit()

    r = client.post(
        "/draft/llm",
        headers={"Authorization": f"Bearer {token}"},
        json=_payload_valido(),
    )
    assert r.status_code == 402
    assert "esgotada" in r.json()["detail"].lower()


async def test_draft_llm_assinatura_canceled_402(client, monkeypatch, db_session):
    _mock_llm_pipeline(monkeypatch)
    user, token = signup_and_login(client)

    sub = await find_subscription(db_session, user["id"])
    sub.status = SubscriptionStatus.CANCELED
    await db_session.commit()

    r = client.post(
        "/draft/llm",
        headers={"Authorization": f"Bearer {token}"},
        json=_payload_valido(),
    )
    assert r.status_code == 402
    assert "canceled" in r.json()["detail"].lower()


async def test_draft_llm_sucesso_consome_uma_peca(client, monkeypatch, db_session):
    _mock_llm_pipeline(monkeypatch)
    user, token = signup_and_login(client)

    r = client.post(
        "/draft/llm",
        headers={"Authorization": f"Bearer {token}"},
        json=_payload_valido(),
    )
    assert r.status_code == 200
    body = r.json()
    # texto vem com disclaimer obrigatório no topo + minuta original embaixo
    assert "MINUTA AUTOMATIZADA, NÃO PROTOCOLAR SEM REVISÃO" in body["texto"]
    assert "minuta de teste" in body["texto"]
    assert body["modelo"] == "mock-model"
    assert body["billing"]["pecas_consumidas_no_periodo"] == 1
    assert body["billing"]["pecas_incluidas"] == 3

    sub = await find_subscription(db_session, user["id"])
    assert sub.pecas_consumidas_no_periodo == 1


async def test_draft_llm_default_modo_pertinaz(client, monkeypatch):
    """Payload sem modo_redacional ecoa PERTINAZ (default)."""
    _mock_llm_pipeline(monkeypatch)
    _, token = signup_and_login(client)
    r = client.post(
        "/draft/llm",
        headers={"Authorization": f"Bearer {token}"},
        json=_payload_valido(),
    )
    assert r.status_code == 200
    assert r.json()["modo_redacional"] == "PERTINAZ"


async def test_draft_llm_propaga_modo_ate_gerar_minuta(client, monkeypatch):
    """modo_redacional do payload chega a gerar_minuta e ecoa na resposta."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    capturado: dict = {}

    def _captura(*a, **kw):
        capturado.update(kw)
        return _FakeMinuta()

    import nexus.llm
    import nexus.quality
    monkeypatch.setattr(nexus.llm, "gerar_minuta", _captura)
    monkeypatch.setattr(
        nexus.quality, "avaliar_qualidade",
        lambda *a, **kw: QualityReport(score=80, gates=[GateResult("g", True, "ok")]),
    )
    monkeypatch.setattr(nexus.llm, "validar_feito_hbm", lambda texto: [])

    _, token = signup_and_login(client)
    payload = _payload_valido()
    payload["modo_redacional"] = "CUSTODIA"
    r = client.post(
        "/draft/llm",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert r.status_code == 200
    assert r.json()["modo_redacional"] == "CUSTODIA"
    assert capturado.get("modo") == "CUSTODIA"


async def test_draft_llm_modo_invalido_422(client, monkeypatch):
    _mock_llm_pipeline(monkeypatch)
    _, token = signup_and_login(client)
    payload = _payload_valido()
    payload["modo_redacional"] = "TURBO"
    r = client.post(
        "/draft/llm",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert r.status_code == 422


async def test_draft_llm_tres_chamadas_esgotam_trial(client, monkeypatch, db_session):
    """Trial = 3 peças. Três chamadas OK, quarta retorna 402."""
    _mock_llm_pipeline(monkeypatch)
    user, token = signup_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}

    for i in range(3):
        r = client.post("/draft/llm", headers=headers, json=_payload_valido())
        assert r.status_code == 200, f"chamada {i+1} falhou: {r.json()}"
        assert r.json()["billing"]["pecas_consumidas_no_periodo"] == i + 1

    # 4ª chamada → 402
    r = client.post("/draft/llm", headers=headers, json=_payload_valido())
    assert r.status_code == 402
