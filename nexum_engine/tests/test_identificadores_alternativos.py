"""Um repetitivo tem mais de uma citação legítima.

O Tema 1.260 é citado em peça ora como ``REsp 2.048.687/BA``, ora como
``Tema 1.260`` — as duas formas são corretas e correspondem ao MESMO
precedente verificado. Indexando apenas o campo ``numero``, o gate bloqueava
a peça que usasse a outra forma, embora a base a tivesse verificado: um falso
positivo que empurra o redator a reescrever citação correta para agradar a
ferramenta.
"""

from __future__ import annotations

import asyncio
import json

from nexum_engine.verdade.auditor import auditar_citacoes
from nexum_engine.verdade.fontes import FonteJsonVerificada
from nexum_engine.verdade.precedente import Precedente

REPETITIVO = {
    "numero": "REsp 2.048.687/BA",
    "identificadores_alternativos": ["Tema 1.260", "Tema 1260"],
    "tese": "Hearsay não basta, por si só, para o standard da pronúncia.",
    "fonte_verificacao": "STJ, 3ª Seção, Rel. Min. Reynaldo Soares da Fonseca, j. 12/08/2026.",
}


def test_chaves_de_indice_cobrem_numero_e_aliases() -> None:
    chaves = Precedente.de_dict(REPETITIVO).chaves_de_indice
    assert "RESP 2048687/BA" in chaves
    assert "TEMA 1260" in chaves


def test_chaves_nao_repetem() -> None:
    """'Tema 1.260' e 'Tema 1260' normalizam igual — uma chave só."""
    chaves = Precedente.de_dict(
        dict(REPETITIVO, identificadores_alternativos=["Tema 1.260", "Tema 1260"])
    ).chaves_de_indice
    assert len(chaves) == len(set(chaves))


def test_precedente_sem_aliases_continua_funcionando() -> None:
    simples = {k: v for k, v in REPETITIVO.items() if k != "identificadores_alternativos"}
    assert Precedente.de_dict(simples).chaves_de_indice == ("RESP 2048687/BA",)


def test_gate_aceita_as_duas_formas_de_citar_o_mesmo_repetitivo(tmp_path) -> None:
    (tmp_path / "08_juri.json").write_text(
        json.dumps({"precedentes": [REPETITIVO]}, ensure_ascii=False), encoding="utf-8"
    )
    fonte = FonteJsonVerificada(tmp_path)
    assert fonte.total_citaveis == 1, "o alias não pode contar como segundo precedente"

    relatorio = asyncio.run(
        auditar_citacoes(
            "Aplica-se o Tema 1.260 do STJ (REsp 2.048.687/BA) à pronúncia.", fonte
        )
    )
    assert relatorio.veredito == "PROTOCOLAVEL"
    assert len(relatorio.citacoes) == 2
