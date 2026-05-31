"""Testes do POST /autos — agora via JWT (não mais NEXUS_TOKEN bearer)."""

from __future__ import annotations

import hashlib

from tests.conftest import signup_and_login

PDF = b"%PDF-1.4 conteudo fake"


def _post(client, token=None, **fields):
    files = {"arquivo": fields.pop("arquivo", ("a.pdf", PDF, "application/pdf"))}
    data = {"feito_id": fields.pop("feito_id", "Feito-HBM")}
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    return client.post("/autos", headers=headers, data=data, files=files)


async def test_upload_sem_jwt_401(monkeypatch, tmp_path, client):
    monkeypatch.setenv("CASO_DATA_DIR", str(tmp_path))
    assert _post(client).status_code == 401


async def test_upload_jwt_invalido_401(monkeypatch, tmp_path, client):
    monkeypatch.setenv("CASO_DATA_DIR", str(tmp_path))
    assert _post(client, token="not-a-jwt").status_code == 401


async def test_upload_pdf_valido_grava_em_dir_do_user(monkeypatch, tmp_path, client):
    monkeypatch.setenv("CASO_DATA_DIR", str(tmp_path))
    user, token = signup_and_login(client)

    r = _post(client, token=token)
    assert r.status_code == 200
    body = r.json()
    esperado = hashlib.sha256(PDF).hexdigest()
    assert body["sha256"] == esperado
    assert body["fonte_uri"] == f"hash://Feito-HBM/{esperado}"

    # Isolamento por user_id: arquivo vai para tmp_path/{user_id}/{feito_id}/{sha}.pdf
    salvo = tmp_path / user["id"] / "Feito-HBM" / f"{esperado}.pdf"
    assert salvo.read_bytes() == PDF


async def test_fonte_uri_compativel_com_dado_liquido(monkeypatch, tmp_path, client):
    from nexus.dado_liquido import fonte_valida
    from nexus.models import Fato, FontePrimaria

    monkeypatch.setenv("CASO_DATA_DIR", str(tmp_path))
    _, token = signup_and_login(client)
    body = _post(client, token=token).json()

    fato = Fato(
        id="f1", proposto="X", verificado="X confirmado",
        fonte=FontePrimaria(uri=body["fonte_uri"]),
    )
    assert fonte_valida(fato)


async def test_upload_tipo_invalido_415(monkeypatch, tmp_path, client):
    monkeypatch.setenv("CASO_DATA_DIR", str(tmp_path))
    _, token = signup_and_login(client)
    r = _post(client, token=token, arquivo=("a.txt", b"plain", "text/plain"))
    assert r.status_code == 415


async def test_upload_arquivo_grande_413(monkeypatch, tmp_path, client):
    monkeypatch.setenv("CASO_DATA_DIR", str(tmp_path))
    _, token = signup_and_login(client)
    big = b"X" * (20 * 1024 * 1024 + 1)
    r = _post(client, token=token, arquivo=("a.pdf", big, "application/pdf"))
    assert r.status_code == 413


async def test_upload_feito_id_invalido_400(monkeypatch, tmp_path, client):
    monkeypatch.setenv("CASO_DATA_DIR", str(tmp_path))
    _, token = signup_and_login(client)
    r = _post(client, token=token, feito_id="../etc/passwd")
    assert r.status_code == 400


async def test_upload_sem_caso_data_dir_503(monkeypatch, client):
    monkeypatch.delenv("CASO_DATA_DIR", raising=False)
    _, token = signup_and_login(client)
    r = _post(client, token=token)
    assert r.status_code == 503


async def test_upload_isolamento_entre_users(monkeypatch, tmp_path, client):
    """User A não vê pasta de User B — confirma isolamento físico."""
    monkeypatch.setenv("CASO_DATA_DIR", str(tmp_path))
    user_a, token_a = signup_and_login(client, email="a@x.com")
    user_b, token_b = signup_and_login(client, email="b@x.com")

    _post(client, token=token_a).status_code  # noqa: B018
    _post(client, token=token_b).status_code  # noqa: B018

    assert (tmp_path / user_a["id"]).exists()
    assert (tmp_path / user_b["id"]).exists()
    assert user_a["id"] != user_b["id"]
