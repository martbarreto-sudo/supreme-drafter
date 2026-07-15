"""Recall@K: gabarito exato local vs. caminho de produção — e falha-alto."""

import asyncio
import math

import pytest

from nexum_engine.verdade.validar_recall import (
    RelatorioRecall,
    validar_recall,
)


def executar(coro):
    return asyncio.run(coro)


def _circulo():
    """Seis vetores unitários 2-D com TODAS as distâncias par-a-par
    distintas (ângulos de espaçamento irregular) — rankings sem empate."""
    angulos = [0.0, 0.15, 0.45, 1.0, 1.7, 2.6]
    return {
        f"HC {i}/SP": [math.cos(a), math.sin(a)]
        for i, a in enumerate(angulos)
    }


class FakeDB:
    """DatabasePort falso SOMENTE LEITURA: simula um índice ideal, com
    degradação injetável por consulta (``forcar``) para testar a métrica."""

    def __init__(self, vetores, forcar=None, como_literal=False):
        self.vetores = dict(vetores)
        self.forcar = dict(forcar or {})
        self.como_literal = como_literal
        self.consultas_sql = []

    async def fetch(self, query, *args):
        self.consultas_sql.append((query, args))
        if "<=>" not in query:
            linhas = []
            for n in sorted(self.vetores):
                v = self.vetores[n]
                valor = (
                    "[" + ",".join(str(float(x)) for x in v) + "]"
                    if self.como_literal else list(v)
                )
                linhas.append(
                    {"numero_normalizado": n, "vetor_semantico": valor}
                )
            return linhas
        literal, excluido, k = args
        if excluido in self.forcar:
            return [
                {"numero_normalizado": n} for n in self.forcar[excluido][:k]
            ]
        alvo = [float(x) for x in literal.strip("[]").split(",")]

        def dist(v):
            prod = sum(a * b for a, b in zip(alvo, v))
            na = math.sqrt(sum(a * a for a in alvo))
            nb = math.sqrt(sum(b * b for b in v))
            return 1.0 - prod / (na * nb)

        cands = sorted(
            (dist(v), n) for n, v in self.vetores.items() if n != excluido
        )
        return [{"numero_normalizado": n} for _, n in cands[:k]]

    async def fetchrow(self, query, *args):
        raise AssertionError("não usado")

    async def execute(self, query, *args):
        raise AssertionError("utilitário é somente leitura — nunca escreve")


def test_indice_ideal_tem_recall_perfeito():
    rel = executar(validar_recall(FakeDB(_circulo()), k=3))
    assert rel == RelatorioRecall(
        k=3, consultas=6, vetorizados=6,
        recall_medio=1.0, recall_minimo=1.0, pior_consulta="HC 0/SP",
    )
    assert "média 1.000" in str(rel) and "recall@3" in str(rel)


def test_degradacao_aparece_na_media_no_minimo_e_no_pior_caso():
    vetores = _circulo()
    # Para a consulta HC 0/SP o gabarito exato é {HC 1, HC 2, HC 3};
    # o "índice" devolve só 2 acertos + 1 intruso → recall 2/3.
    db = FakeDB(vetores, forcar={"HC 0/SP": ["HC 1/SP", "HC 2/SP", "HC 5/SP"]})
    rel = executar(validar_recall(db, k=3))
    assert rel.recall_minimo == pytest.approx(2 / 3)
    assert rel.recall_medio == pytest.approx((5 * 1.0 + 2 / 3) / 6)
    assert rel.pior_consulta == "HC 0/SP"


def test_sql_espelha_a_producao_e_exclui_a_propria_consulta():
    db = FakeDB(_circulo())
    executar(validar_recall(db, k=3))
    selecao = db.consultas_sql[0][0]
    assert "vetor_semantico IS NOT NULL" in selecao
    assert "NOT verificacao_pendente" in selecao
    assert "fonte_verificacao <> ''" in selecao
    consulta, args = db.consultas_sql[1]
    assert "ORDER BY vetor_semantico <=> $1::vector LIMIT $3" in consulta
    assert "numero_normalizado <> $2" in consulta
    assert args[1] == "HC 0/SP" and args[2] == 3


def test_le_vetor_em_literal_pgvector():
    rel = executar(validar_recall(FakeDB(_circulo(), como_literal=True), k=3))
    assert rel.recall_medio == 1.0


def test_amostra_limita_de_forma_deterministica():
    db = FakeDB(_circulo())
    rel = executar(validar_recall(db, k=3, amostra=2))
    assert rel.consultas == 2 and rel.vetorizados == 6
    vetoriais = [a for q, a in db.consultas_sql if "<=>" in q]
    assert [a[1] for a in vetoriais] == ["HC 0/SP", "HC 1/SP"]


def test_poucos_vetorizados_falha_alto():
    poucos = dict(list(_circulo().items())[:3])
    with pytest.raises(RuntimeError, match="backfill"):
        executar(validar_recall(FakeDB(poucos), k=3))


def test_vetor_norma_zero_falha_alto_com_o_numero():
    vetores = _circulo()
    vetores["HC 9/SP"] = [0.0, 0.0]
    with pytest.raises(RuntimeError, match="HC 9/SP"):
        executar(validar_recall(FakeDB(vetores), k=3))


def test_dimensao_divergente_falha_alto():
    vetores = _circulo()
    vetores["HC 9/SP"] = [1.0, 0.0, 0.0]
    with pytest.raises(RuntimeError, match="HC 9/SP"):
        executar(validar_recall(FakeDB(vetores), k=3))


def test_vetor_ilegivel_falha_alto():
    db = FakeDB({"HC 0/SP": [1.0, 0.0]})

    async def fetch_corrompido(query, *args):
        return [
            {"numero_normalizado": f"HC {i}/SP", "vetor_semantico": "lixo"}
            for i in range(4)
        ]

    db.fetch = fetch_corrompido
    with pytest.raises(RuntimeError, match="ilegível"):
        executar(validar_recall(db, k=3))


def test_banco_violando_o_limit_falha_alto():
    db = FakeDB(_circulo())
    fetch_original = db.fetch

    async def fetch_transbordando(query, *args):
        if "<=>" in query:
            return [{"numero_normalizado": f"HC {i}/SP"} for i in range(1, 5)]
        return await fetch_original(query, *args)

    db.fetch = fetch_transbordando
    with pytest.raises(RuntimeError, match="LIMIT"):
        executar(validar_recall(db, k=3))


def test_parametros_invalidos():
    with pytest.raises(ValueError):
        executar(validar_recall(FakeDB(_circulo()), k=0))
    with pytest.raises(ValueError):
        executar(validar_recall(FakeDB(_circulo()), k=3, amostra=0))
