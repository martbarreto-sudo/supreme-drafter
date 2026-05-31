from nexum.halt import auditar
from nexum.models import DraftRequest, Fato, FontePrimaria


def _req(fato: Fato) -> DraftRequest:
    return DraftRequest(feito_id="Feito-HBM", peca_tipo="HC", fatos=[fato])


def test_halt_fato_sem_fonte():
    halt = auditar(_req(Fato(id="f1", proposto="X aconteceu")))
    assert halt is not None
    assert "PENDENTE" in halt.vicios[0]


def test_halt_fato_fonte_invalida():
    fato = Fato(
        id="f1",
        proposto="X",
        verificado="X confirmado",
        fonte=FontePrimaria(uri="http://x"),
    )
    assert auditar(_req(fato)) is not None


def test_passa_fato_liquido():
    fato = Fato(
        id="f1",
        proposto="X",
        verificado="X confirmado pelo log do PJe",
        fonte=FontePrimaria(uri="log_pje://feito-hbm/123"),
    )
    assert auditar(_req(fato)) is None


def test_argumentativo_nao_dispara_halt():
    fato = Fato(id="f1", proposto="hipótese argumentativa", dispositivo=False)
    assert auditar(_req(fato)) is None
