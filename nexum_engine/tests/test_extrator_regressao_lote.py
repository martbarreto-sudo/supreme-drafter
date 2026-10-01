"""Regressão do extrator de citações — encontrada rodando o gate em lote.

Em 01/10/2026 o gate foi executado pela primeira vez contra as 30 peças reais
(20 minutas do supreme-drafter + examples/ do warroom-tigre). Os vereditos
importavam menos que dois defeitos que o lote expôs no extrator:

1. ``Tema 1.260`` e ``Tema 1.196`` eram ambos extraídos como ``Tema 1`` — o
   ``\\d+`` parava no ponto de milhar. Dois temas distintos colidindo numa
   única chave é o pior erro possível aqui: a citação podia casar com o tema
   errado na base e sair aprovada.
2. ``RE`` casava no meio de palavra: "sobre 9 mm" virava ``RE 9`` e
   "refere 42 laudos" virava ``RE 42``. Falso positivo reprova peça íntegra —
   e gate que reprova à toa é gate que as pessoas aprendem a ignorar.
"""

from __future__ import annotations

import pytest

from nexum_engine.verdade.auditor import extrair_citacoes
from nexum_engine.verdade.precedente import normalizar_citacao


@pytest.mark.parametrize(
    "texto, esperado",
    [
        ("aplica-se o Tema 1.260 dos repetitivos", "Tema 1.260"),
        ("conforme o Tema 1.196 do STJ", "Tema 1.196"),
        ("o Tema 280 da repercussão geral", "Tema 280"),
    ],
)
def test_numero_de_tema_preserva_o_milhar(texto: str, esperado: str) -> None:
    assert extrair_citacoes(texto) == [esperado]


def test_temas_distintos_nao_colidem_na_chave_normalizada() -> None:
    assert normalizar_citacao("Tema 1.260") != normalizar_citacao("Tema 1.196")


@pytest.mark.parametrize(
    "texto",
    [
        "o projétil de calibre sobre 9 mm foi apreendido",
        "o parecer refere 42 laudos periciais",
        "a defesa quer rever 15 pontos do acórdão",
    ],
)
def test_classe_nao_casa_no_meio_de_palavra(texto: str) -> None:
    assert extrair_citacoes(texto) == [], f"falso positivo em: {texto!r}"


def test_citacoes_legitimas_continuam_sendo_extraidas() -> None:
    texto = (
        "Invoca-se o AgRg no HC 789.432/SP, o HC 598.886/SC, a Súmula Vinculante 11, "
        "a Súmula 444/STJ, o RE 603.616/RO e a ADC 43, 44 e 54."
    )
    assert extrair_citacoes(texto) == [
        "AgRg no HC 789.432/SP",
        "HC 598.886/SC",
        "Súmula Vinculante 11",
        "Súmula 444/STJ",
        "RE 603.616/RO",
        "ADC 43, 44 e 54",
    ]
