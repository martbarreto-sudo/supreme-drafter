"""Backfill de embeddings — (tese + ementa) → ``vetor_semantico`` no Supabase.

Utilitário de OPERADOR (service role), não da engine em runtime:

- a RLS de ``precedentes_verificados`` nega escrita aos papéis da engine de
  propósito — este script só funciona com um pool conectado como
  OWNER/service role, injetado pelo operador no gatilho HITL;
- diferente da busca (que degrada com fallback honesto), o backfill FALHA
  ALTO: inconsistência entre textos e vetores é erro de operação, nunca
  algo a mascarar.

Injeção de dependência pura — nenhum SDK importado aqui:

    from nexum_engine.adapters import AsyncpgAdapter, VertexEmbedAdapter
    from nexum_engine.verdade.backfill_embeddings import backfill_embeddings

    rel = await backfill_embeddings(
        AsyncpgAdapter(pool_service_role),
        VertexEmbedAdapter(client, modelo="..."),  # MESMO modelo da busca
        dry_run=True,   # primeiro rode em ensaio; depois dry_run=False
    )
    print(rel)

Pré-requisitos no banco: ``schema/precedentes.sql`` + a migração
``0002_fase2_busca_semantica.sql`` (coluna ``vetor_semantico vector(768)``).
"""

from __future__ import annotations

from dataclasses import dataclass

from ..ports import DatabasePort, EmbedderPort
from .fontes import _vetor_para_sql

LOTE_PADRAO = 16


@dataclass(frozen=True)
class RelatorioBackfill:
    candidatos: int          # citáveis sem vetor encontrados
    atualizados: int         # UPDATEs executados (0 em dry-run)
    dry_run: bool

    def __str__(self) -> str:  # legível no terminal do operador
        modo = " (ensaio — nada gravado)" if self.dry_run else ""
        return (
            f"backfill: {self.candidatos} candidato(s) sem vetor, "
            f"{self.atualizados} atualizado(s){modo}"
        )


def _texto_para_embedding(linha: dict) -> str:
    """Conteúdo vetorizado: tese + ementa (o mesmo contrato da migração)."""
    tese = str(linha.get("tese", "")).strip()
    ementa = str(linha.get("ementa", "")).strip()
    return f"{tese}\n{ementa}".strip()


async def backfill_embeddings(
    db: DatabasePort,
    embedder: EmbedderPort,
    *,
    lote: int = LOTE_PADRAO,
    dry_run: bool = False,
) -> RelatorioBackfill:
    """Vetoriza todos os precedentes citáveis ainda sem ``vetor_semantico``.

    Idempotente por construção: só seleciona linhas com vetor NULL, então
    reexecutar continua de onde parou. ``dry_run=True`` apenas conta os
    candidatos, sem chamar o provedor de embeddings nem gravar.
    """
    if lote < 1:
        raise ValueError("lote deve ser >= 1")

    linhas = await db.fetch(
        "SELECT numero_normalizado, tese, ementa "
        "FROM precedentes_verificados "
        "WHERE fonte_verificacao <> '' AND NOT verificacao_pendente "
        "AND vetor_semantico IS NULL "
        "ORDER BY numero_normalizado"
    )
    if dry_run or not linhas:
        return RelatorioBackfill(
            candidatos=len(linhas), atualizados=0, dry_run=dry_run
        )

    atualizados = 0
    for inicio in range(0, len(linhas), lote):
        grupo = linhas[inicio:inicio + lote]
        textos = [_texto_para_embedding(l) for l in grupo]
        if any(not t for t in textos):
            vazios = [
                g["numero_normalizado"] for g, t in zip(grupo, textos) if not t
            ]
            raise RuntimeError(
                f"precedente(s) citável(is) sem tese/ementa — corrigir a base "
                f"antes do backfill: {vazios}"
            )
        vetores = await embedder.embed(textos)
        if len(vetores) != len(grupo):
            raise RuntimeError(
                f"provedor devolveu {len(vetores)} vetores para {len(grupo)} "
                "textos — abortando sem gravar este lote"
            )
        for linha, vetor in zip(grupo, vetores):
            await db.execute(
                "UPDATE precedentes_verificados "
                "SET vetor_semantico = $1::vector, atualizado_em = now() "
                "WHERE numero_normalizado = $2",
                _vetor_para_sql(vetor),
                linha["numero_normalizado"],
            )
            atualizados += 1

    return RelatorioBackfill(
        candidatos=len(linhas), atualizados=atualizados, dry_run=False
    )
