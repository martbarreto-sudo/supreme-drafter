from nexus.dado_liquido import avaliar, fonte_valida
from nexus.models import Fato, FontePrimaria, StatusFato


def test_fonte_valida_log_pje():
    f = Fato(id="f1", proposto="X", fonte=FontePrimaria(uri="log_pje://x/123"))
    assert fonte_valida(f)


def test_fonte_invalida_http():
    f = Fato(id="f1", proposto="X", fonte=FontePrimaria(uri="http://x"))
    assert not fonte_valida(f)


def test_avaliar_liquido():
    f = Fato(
        id="f1",
        proposto="X",
        verificado="X confirmado",
        fonte=FontePrimaria(uri="certidao://x"),
    )
    assert avaliar(f) == StatusFato.LIQUIDO


def test_avaliar_pendente_sem_verificacao():
    f = Fato(id="f1", proposto="X", fonte=FontePrimaria(uri="certidao://x"))
    assert avaliar(f) == StatusFato.PENDENTE
