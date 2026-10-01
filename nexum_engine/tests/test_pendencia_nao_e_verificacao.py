"""Regressão: aviso de pendência não pode ser lido como prova de verificação.

Defeito encontrado em 01/10/2026 cruzando este motor com a base real do
warroom-tigre: ``fonte_verificacao`` é texto livre, e a base o usa para
registrar a PENDÊNCIA ("PENDENTE — validar inteiro teor antes de citar").
Como ``citavel`` só checava se a string era não-vazia, 5 dos 7 precedentes
que o gate considerava citáveis eram exatamente aqueles cujo próprio texto
dizia que NÃO podiam ser citados — e o gate selava PROTOCOLAVEL.

Num gate de segurança, o falso negativo é o modo de falha caro: o
bloqueio indevido custa uma conferência; a aprovação indevida vai para o
tribunal.
"""

from __future__ import annotations

import asyncio

from nexum_engine.verdade.auditor import auditar_citacoes
from nexum_engine.verdade.fontes import FonteJsonVerificada
from nexum_engine.verdade.precedente import Precedente

VERIFICADO = {
    "numero": "HC 598.886/SC",
    "tese": "O rito do art. 226 do CPP é de observância obrigatória.",
    "fonte_verificacao": "STJ — 6ª Turma, Rel. Min. Rogerio Schietti, j. 27/10/2020.",
}


def test_precedente_com_fonte_oficial_e_citavel() -> None:
    assert Precedente.de_dict(VERIFICADO).citavel


def test_fonte_verificacao_que_declara_pendencia_nao_torna_citavel() -> None:
    pendente = dict(VERIFICADO, numero="HC 598.051/SP")
    pendente["fonte_verificacao"] = (
        "PENDENTE — validar inteiro teor antes de citar em peça "
        "(não verificado por esta esteira)"
    )
    assert not Precedente.de_dict(pendente).citavel


def test_numero_prefixado_com_quarentena_nao_e_citavel() -> None:
    quarentena = dict(
        VERIFICADO,
        numero="[A CONFERIR] Teses repetitivas do art. 226 — 3ª Seção/STJ (2025)",
        fonte_verificacao="SEM NÚMERO DE TEMA/PROCESSO — não citável nesta forma.",
    )
    assert not Precedente.de_dict(quarentena).citavel


def test_flag_estruturada_continua_prevalecendo() -> None:
    """O contrato antigo (flag booleana) não foi enfraquecido pelo novo."""
    com_flag = dict(VERIFICADO, verificacao_pendente=True)
    assert not Precedente.de_dict(com_flag).citavel


def test_gate_bloqueia_citacao_pendente_na_base_em_disco(tmp_path) -> None:
    """Teste de ponta a ponta: da base no disco até o veredito do auditor."""
    (tmp_path / "00_tema.json").write_text(
        '{"precedentes": ['
        '{"numero": "HC 598.886/SC", "tese": "art. 226 obrigatório", '
        '"fonte_verificacao": "STJ, 6ª T., j. 27/10/2020"},'
        '{"numero": "HC 598.051/SP", "tese": "consentimento do morador", '
        '"fonte_verificacao": "PENDENTE — validar antes de citar"}'
        "]}",
        encoding="utf-8",
    )
    fonte = FonteJsonVerificada(tmp_path)
    assert fonte.total_citaveis == 1

    relatorio = asyncio.run(
        auditar_citacoes("Invoca-se o HC 598.886/SC e o HC 598.051/SP.", fonte)
    )
    assert relatorio.veredito == "NAO_PROTOCOLAVEL"
    assert [c.citacao for c in relatorio.nao_verificadas] == ["HC 598.051/SP"]
