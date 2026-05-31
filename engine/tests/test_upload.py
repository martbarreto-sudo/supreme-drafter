import hashlib

from fastapi.testclient import TestClient

from nexus.api import app

client = TestClient(app)
PDF = b"%PDF-1.4 conteudo fake"


def _wire(monkeypatch, tmp_path):
    monkeypatch.setenv("NEXUS_TOKEN", "test-token")
    monkeypatch.setenv("CASO_DATA_DIR", str(tmp_path))


def _post(headers=None, **fields):
    files = {"arquivo": fields.pop("arquivo", ("a.pdf", PDF, "application/pdf"))}
    data = {"feito_id": fields.pop("feito_id", "Feito-HBM")}
    return client.post("/autos", headers=headers or {}, data=data, files=files)


def test_upload_sem_auth_401(monkeypatch, tmp_path):
    _wire(monkeypatch, tmp_path)
    assert _post().status_code == 401


def test_upload_token_invalido_403(monkeypatch, tmp_path):
    _wire(monkeypatch, tmp_path)
    assert _post(headers={"Authorization": "Bearer wrong"}).status_code == 403


def test_upload_pdf_valido_grava_e_devolve_hash(monkeypatch, tmp_path):
    _wire(monkeypatch, tmp_path)
    r = _post(headers={"Authorization": "Bearer test-token"})
    assert r.status_code == 200
    body = r.json()
    esperado = hashlib.sha256(PDF).hexdigest()
    assert body["sha256"] == esperado
    assert body["fonte_uri"] == f"hash://Feito-HBM/{esperado}"
    salvo = tmp_path / "Feito-HBM" / f"{esperado}.pdf"
    assert salvo.read_bytes() == PDF


def test_fonte_uri_compatible_with_dado_liquido(monkeypatch, tmp_path):
    # O fonte_uri produzido tem que casar com o validador do Dado Líquido
    from nexus.dado_liquido import fonte_valida
    from nexus.models import Fato, FontePrimaria

    _wire(monkeypatch, tmp_path)
    body = _post(headers={"Authorization": "Bearer test-token"}).json()
    fato = Fato(
        id="f1",
        proposto="X",
        verificado="X confirmado",
        fonte=FontePrimaria(uri=body["fonte_uri"]),
    )
    assert fonte_valida(fato)


def test_upload_tipo_invalido_415(monkeypatch, tmp_path):
    _wire(monkeypatch, tmp_path)
    r = _post(
        headers={"Authorization": "Bearer test-token"},
        arquivo=("a.txt", b"plain", "text/plain"),
    )
    assert r.status_code == 415


def test_upload_arquivo_grande_413(monkeypatch, tmp_path):
    _wire(monkeypatch, tmp_path)
    big = b"X" * (20 * 1024 * 1024 + 1)
    r = _post(
        headers={"Authorization": "Bearer test-token"},
        arquivo=("a.pdf", big, "application/pdf"),
    )
    assert r.status_code == 413


def test_upload_feito_id_invalido_400(monkeypatch, tmp_path):
    _wire(monkeypatch, tmp_path)
    r = _post(
        headers={"Authorization": "Bearer test-token"},
        feito_id="../etc/passwd",
    )
    assert r.status_code == 400


def test_upload_sem_caso_data_dir_503(monkeypatch, tmp_path):
    monkeypatch.setenv("NEXUS_TOKEN", "test-token")
    monkeypatch.delenv("CASO_DATA_DIR", raising=False)
    r = _post(headers={"Authorization": "Bearer test-token"})
    assert r.status_code == 503


def test_upload_sem_nexus_token_503(monkeypatch, tmp_path):
    monkeypatch.delenv("NEXUS_TOKEN", raising=False)
    monkeypatch.setenv("CASO_DATA_DIR", str(tmp_path))
    r = _post(headers={"Authorization": "Bearer anything"})
    assert r.status_code == 503
