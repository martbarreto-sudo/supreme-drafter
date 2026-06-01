from fastapi.testclient import TestClient

from nexus.api import app

client = TestClient(app)


def test_healthz():
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_vulnerabilidades_feito_existente():
    r = client.get("/casos/Feito-HBM/vulnerabilidades")
    assert r.status_code == 200
    body = r.json()
    # Feito-HBM tem 3 vulnerabilidades (reconhecimento-inicial LIQUIDO +
    # termo-ausente e reconhecimento-em-juizo-viciado PENDENTE)
    assert len(body) == 3
    fato_ids = {v["fato_id"] for v in body}
    assert {
        "reconhecimento-inicial",
        "termo-ausente",
        "reconhecimento-em-juizo-viciado",
    } == fato_ids
    # A primeira vulnerabilidade (com fonte primária ancorada) é LIQUIDO
    primeira = next(v for v in body if v["fato_id"] == "reconhecimento-inicial")
    assert primeira["status"] == "LIQUIDO"


def test_vulnerabilidades_feito_inexistente():
    r = client.get("/casos/Feito-XYZ/vulnerabilidades")
    assert r.status_code == 404


def test_draft_halt_sem_fonte():
    r = client.post(
        "/draft",
        json={
            "feito_id": "Feito-HBM",
            "peca_tipo": "HC",
            "fatos": [{"id": "f1", "proposto": "X aconteceu"}],
        },
    )
    assert r.status_code == 422
    body = r.json()
    assert body["halt"] is True
    assert "Módulo 11" in body["motivo"]


def test_draft_minuta_com_fato_liquido():
    r = client.post(
        "/draft",
        json={
            "feito_id": "Feito-HBM",
            "peca_tipo": "HC",
            "fatos": [
                {
                    "id": "f1",
                    "proposto": "Reconhecimento por foto",
                    "verificado": "Reconhecimento por foto isolada, sem fila",
                    "fonte": {"uri": "certidao://feito-hbm/fls-12"},
                }
            ],
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["halt"] is False
    assert "HABEAS CORPUS" in body["texto"]
    assert "Tema 1.258" in body["texto"]
