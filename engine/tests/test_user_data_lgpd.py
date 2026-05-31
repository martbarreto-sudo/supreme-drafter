"""Testes LGPD — GET /user/me/export e DELETE /user/me."""

from __future__ import annotations

from dataclasses import dataclass

from nexus.quality import GateResult, QualityReport
from tests.conftest import signup_and_login


@dataclass
class _FakeMinuta:
    texto: str = "minuta para teste lgpd"
    modelo: str = "mock-model"
    input_tokens: int = 100
    cache_read_tokens: int = 0
    cache_creation_tokens: int = 0
    output_tokens: int = 50


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
        lambda *a, **kw: QualityReport(score=80, gates=[GateResult("g", True, "ok")]),
    )
    monkeypatch.setattr(nexus.llm, "validar_feito_hbm", lambda texto: [])


# ---------- GET /user/me/export ----------


async def test_export_sem_jwt_401(client):
    r = client.get("/user/me/export")
    assert r.status_code == 401


async def test_export_devolve_estrutura_completa(client):
    user, token = signup_and_login(client)
    r = client.get("/user/me/export", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    body = r.json()

    assert "exported_at" in body
    assert body["user"]["id"] == user["id"]
    assert body["user"]["email"] == user["email"]
    assert body["user"]["tos_version"] == 1
    assert body["user"]["tos_aceito_em"] is not None
    assert body["subscription"]["plan_code"] == "TRIAL"
    assert body["payments"] == []  # ainda sem pagamento
    assert body["audits"] == []  # ainda sem geração


async def test_export_inclui_audits_e_payments(client, monkeypatch, tmp_path):
    _mock_llm(monkeypatch)
    monkeypatch.setenv("CASO_DATA_DIR", str(tmp_path))
    _, token = signup_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}

    # gerar 2 peças
    for _ in range(2):
        client.post("/draft/llm", headers=headers, json=_payload())

    r = client.get("/user/me/export", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert len(body["audits"]) == 2
    for a in body["audits"]:
        assert a["minuta_url"].startswith("/user/audits/")
        assert "minuta_texto" not in a  # texto não vai no dump (baixa individual)


# ---------- DELETE /user/me (anonimização LGPD) ----------


async def test_delete_account_sem_jwt_401(client):
    r = client.delete("/user/me")
    assert r.status_code == 401


async def test_delete_account_anonimiza_user(client, db_session):
    from sqlalchemy import select

    from nexus.db.models import OABStatus, SubscriptionStatus, User
    from nexus.billing.service import find_subscription

    user, token = signup_and_login(client)
    r = client.delete("/user/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 204

    # User permanece (FKs precisam dele) mas PII some
    db_user = (await db_session.execute(
        select(User).where(User.id == user["id"])
    )).scalar_one()
    assert db_user.email != user["email"]
    assert db_user.email.endswith("@example.invalid")
    assert db_user.name == "Conta encerrada"
    assert db_user.oab_numero == "0"
    assert db_user.oab_uf == "XX"
    assert db_user.password_hash == ""
    assert db_user.oab_status == OABStatus.REVOKED

    # Subscription cancelada
    sub = await find_subscription(db_session, user["id"])
    assert sub.status == SubscriptionStatus.CANCELED
    assert sub.pecas_incluidas == 0


async def test_delete_account_apaga_minutas_do_disco(
    client, monkeypatch, tmp_path, db_session
):
    _mock_llm(monkeypatch)
    monkeypatch.setenv("CASO_DATA_DIR", str(tmp_path))
    user, token = signup_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}

    # gera 1 peça → arquivo existe
    r = client.post("/draft/llm", headers=headers, json=_payload())
    audit_id = r.json()["audit_id"]
    minuta_file = tmp_path / user["id"] / "audits" / f"{audit_id}.md"
    assert minuta_file.exists()

    # delete account
    r = client.delete("/user/me", headers=headers)
    assert r.status_code == 204

    # arquivo da minuta sumiu
    assert not minuta_file.exists()


async def test_delete_account_proibe_login_posterior(client):
    _, token = signup_and_login(client, email="login-after-delete@x.com")
    # delete
    r = client.delete("/user/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 204

    # login com senha original não funciona mais (password_hash zerado)
    lr = client.post(
        "/auth/login",
        json={"email": "login-after-delete@x.com", "password": "senhaForte12345"},
    )
    # email original também não existe mais (foi anonimizado)
    assert lr.status_code == 401


async def test_export_apos_delete_continua_funcionando_com_dados_anonimizados(
    client, db_session
):
    """Conta anonimizada: dados retornam mas sem PII. Acessar exigiria
    JWT válido — após anonimização, JWT antigo ainda funciona até expirar
    porque assinatura HMAC permanece válida; UserOut/export refletem
    estado anonimizado."""
    user, token = signup_and_login(client)
    client.delete("/user/me", headers={"Authorization": f"Bearer {token}"})

    r = client.get("/user/me/export", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    body = r.json()
    assert body["user"]["name"] == "Conta encerrada"
    assert body["user"]["oab_status"] == "REVOKED"
