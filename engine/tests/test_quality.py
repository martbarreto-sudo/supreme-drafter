from nexus.casos.data import FEITOS
from nexus.models import Fato, FontePrimaria
from nexus.quality import avaliar_qualidade


def _fato() -> Fato:
    return Fato(
        id="f1",
        proposto="Reconhecimento por foto",
        verificado="Reconhecimento por foto isolada, sem fila",
        fonte=FontePrimaria(uri="certidao://feito-hbm/inquerito-fls-12"),
    )


# Minuta sintética que satisfaz todos os gates do Feito-HBM.
# Inclui todos os precedentes/dispositivos catalogados no eixo dogmático
# (Tema 1.258, HC 598.887, HC 712.781, art. 226) — esse é justamente o
# contrato que o gate `precedente_do_eixo` verifica.
_MINUTA_OK = """
HABEAS CORPUS — Feito-HBM

I. DOS FATOS
1. Reconhecimento por foto isolada, sem fila (fonte: certidao://feito-hbm/inquerito-fls-12).

II. TABELA DE VULNERABILIDADES
| ... |

III. DO DIREITO
Distinguishing estrito contra o Tema 1.258/STF, conforme HC 598.887/SC (STJ)
e HC 712.781/RJ (STJ — contágio probatório). Violação do art. 226, II e III, do CPP.

IV. DOS PEDIDOS
Requer-se a concessão da ordem.

AUDITORIA DE SILÊNCIO
- Certidão de trânsito em julgado não fornecida.
"""


def test_minuta_completa_score_100():
    rel = avaliar_qualidade(_MINUTA_OK, FEITOS["Feito-HBM"], [_fato()])
    assert rel.score == 100
    assert rel.gates_failed == []


def test_precedente_do_eixo_ausente_reprova():
    minuta = _MINUTA_OK.replace("Tema 1.258/STF", "Tema X").replace("HC 598.887/SC", "HC Y")
    rel = avaliar_qualidade(minuta, FEITOS["Feito-HBM"], [_fato()])
    assert rel.score < 100
    nomes_falha = [g.name for g in rel.gates_failed]
    assert "precedente_do_eixo" in nomes_falha


def test_fonte_nao_citada_reprova():
    minuta = _MINUTA_OK.replace("certidao://feito-hbm/inquerito-fls-12", "(sem fonte)")
    rel = avaliar_qualidade(minuta, FEITOS["Feito-HBM"], [_fato()])
    assert "fonte_por_fato" in [g.name for g in rel.gates_failed]


def test_auditoria_silencio_ausente_reprova():
    minuta = _MINUTA_OK.replace("AUDITORIA DE SILÊNCIO", "FIM")
    rel = avaliar_qualidade(minuta, FEITOS["Feito-HBM"], [_fato()])
    assert "auditoria_silencio" in [g.name for g in rel.gates_failed]


def test_submissao_burocratica_reprova_assinatura_tigre():
    minuta = _MINUTA_OK + "\nData venia, ousamos requerer."
    rel = avaliar_qualidade(minuta, FEITOS["Feito-HBM"], [_fato()])
    falha = next(g for g in rel.gates_failed if g.name == "assinatura_tigre")
    assert "data venia" in falha.detail.lower()


def test_fato_argumentativo_nao_exige_fonte():
    arg = Fato(id="hip", proposto="hipótese", dispositivo=False)
    rel = avaliar_qualidade(_MINUTA_OK, FEITOS["Feito-HBM"], [arg])
    assert "fonte_por_fato" in rel.gates_passed


def test_score_proporcional_aos_gates():
    # Minuta vazia, sem fatos dispositivos. Passam fonte_por_fato (nada a citar)
    # e assinatura_tigre (sem submissão). Falham precedente, auditoria e pedido.
    arg = Fato(id="hip", proposto="hipótese", dispositivo=False)
    rel = avaliar_qualidade("texto sem nada", FEITOS["Feito-HBM"], [arg])
    assert rel.score == 40  # 2 de 5 gates
    assert set(rel.gates_passed) == {"fonte_por_fato", "assinatura_tigre"}
