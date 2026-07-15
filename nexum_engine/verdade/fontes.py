"""Fontes de precedentes verificados — o chão de verdade do auditor.

Duas implementações do mesmo contrato:

- ``FonteJsonVerificada``: lê a base MINDJUS em disco (o diretório
  ``mindjus_data/`` do warroom-tigre, ou qualquer cópia dela). Funciona
  hoje, sem credencial nenhuma — é o caminho local-first.
- ``FonteSupabase``: consulta a tabela ``precedentes_verificados`` no
  PostgreSQL via ``ports.DatabasePort`` (AsyncpgAdapter injetado no HITL).
  Schema em ``nexum_engine/schema/precedentes.sql``.

Ambas aplicam a mesma doutrina: precedente em quarentena ou sem fonte de
verificação NUNCA é retornado como citável.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Protocol, Sequence, runtime_checkable

from ..ports import DatabasePort, EmbedderPort
from .precedente import Precedente, normalizar_citacao

logger = logging.getLogger(__name__)

# Limiar mínimo de similaridade de cosseno para um match semântico.
LIMIAR_SIMILARIDADE_PADRAO = 0.7


def _vetor_para_sql(vetor: Sequence[float]) -> str:
    """Literal pgvector ('[0.1,0.2,...]') para bind parametrizado ::vector."""
    return "[" + ",".join(str(float(v)) for v in vetor) + "]"


def _tokens_de_busca(query: str) -> list[str]:
    """Tokens (>2 chars, minúsculos) para o fallback honesto por tags."""
    return [t.strip().lower() for t in query.split() if len(t.strip()) > 2]


def _passa_filtros(
    p: Precedente, tribunal: str | None, tema: str | None
) -> bool:
    """Filtros opcionais de metadados, case-insensitivos — a MESMA semântica
    do SQL (``upper(coluna) = upper($n)``), para as fontes não divergirem."""
    if tribunal is not None:
        if p.tribunal.strip().casefold() != tribunal.strip().casefold():
            return False
    if tema is not None:
        if p.tema.strip().casefold() != tema.strip().casefold():
            return False
    return True


@runtime_checkable
class FonteDePrecedentes(Protocol):
    """Contrato de consulta que o auditor consome."""

    async def obter_por_numero(self, numero: str) -> Precedente | None:
        """Busca exata (normalizada) por número de precedente citável."""
        ...

    async def buscar_por_tags(self, tags: Sequence[str]) -> list[Precedente]:
        """Precedentes citáveis que tenham ao menos uma das tags."""
        ...

    async def buscar_por_semelhanca(
        self,
        query: str,
        limite: int = 5,
        *,
        tribunal: str | None = None,
        tema: str | None = None,
    ) -> list[Precedente]:
        """Busca semântica (analogia fática), com filtros opcionais de
        metadados aplicados NA fonte (nunca pós-filtro no chamador) e
        fallback honesto por tags quando não há embeddings/credenciais —
        nunca falha silenciosamente."""
        ...


class FonteJsonVerificada:
    """Base MINDJUS em JSON no disco (local-first, zero credenciais)."""

    def __init__(self, diretorio: str | Path) -> None:
        self._diretorio = Path(diretorio)
        if not self._diretorio.is_dir():
            raise FileNotFoundError(
                f"diretório da base verificada não existe: {self._diretorio}"
            )
        self._indice: dict[str, Precedente] = {}
        self._todos: list[Precedente] = []
        self._carregar()

    def _carregar(self) -> None:
        for caminho in sorted(self._diretorio.glob("*.json")):
            dados = json.loads(caminho.read_text(encoding="utf-8"))
            tema = str(dados.get("tema") or dados.get("termo_busca") or "").strip()
            # Arquivos temáticos (07/08) registram a verificação no nível do
            # arquivo; o registro herda essa fonte quando não tem a própria.
            fonte_do_arquivo = str(dados.get("fonte_verificacao", "")).strip()
            for registro in dados.get("precedentes", []):
                if fonte_do_arquivo and not registro.get("fonte_verificacao"):
                    registro = {**registro, "fonte_verificacao": fonte_do_arquivo}
                p = Precedente.de_dict(registro, tema=tema)
                if not p.citavel:
                    continue  # quarentena/sem fonte: invisível para o auditor
                self._todos.append(p)
                self._indice[p.numero_normalizado] = p

    @property
    def total_citaveis(self) -> int:
        return len(self._todos)

    async def obter_por_numero(self, numero: str) -> Precedente | None:
        return self._indice.get(normalizar_citacao(numero))

    async def buscar_por_tags(self, tags: Sequence[str]) -> list[Precedente]:
        alvo = {t.strip().lower() for t in tags if t.strip()}
        if not alvo:
            return []
        return [
            p for p in self._todos
            if alvo & {t.lower() for t in p.tags}
        ]

    async def buscar_por_semelhanca(
        self,
        query: str,
        limite: int = 5,
        *,
        tribunal: str | None = None,
        tema: str | None = None,
    ) -> list[Precedente]:
        """Local-first não tem vetores: ranqueia por sobreposição de tokens
        nas tags e no texto da tese (fallback honesto, determinístico).
        Filtros de metadados cortam ANTES do ranking, como no SQL."""
        tokens = _tokens_de_busca(query)
        if not tokens:
            return []
        ranqueados: list[tuple[int, Precedente]] = []
        for p in self._todos:
            if not _passa_filtros(p, tribunal, tema):
                continue
            tags = {t.lower() for t in p.tags}
            texto = f"{p.tese} {p.ementa}".lower()
            acertos = sum(1 for t in tokens if t in tags or t in texto)
            if acertos:
                ranqueados.append((acertos, p))
        ranqueados.sort(key=lambda par: (-par[0], par[1].numero_normalizado))
        return [p for _, p in ranqueados[:limite]]


class FonteSupabase:
    """Base verificada no PostgreSQL/Supabase, via DatabasePort.

    As consultas filtram a citabilidade no próprio SQL (fonte de verificação
    obrigatória + fora de quarentena), espelhando a FonteJsonVerificada.
    """

    _COLUNAS = (
        "numero, tese, tribunal, relator, data_julgamento, ementa, resultado, "
        "tags, relevancia, fonte_verificacao, tema, verificacao_pendente, "
        "motivo_quarentena"
    )
    _CITAVEL = "fonte_verificacao <> '' AND NOT verificacao_pendente"

    def __init__(
        self,
        db: DatabasePort,
        embedder: EmbedderPort | None = None,
        *,
        limiar_similaridade: float = LIMIAR_SIMILARIDADE_PADRAO,
    ) -> None:
        self._db = db
        self._embedder = embedder
        self._limiar = limiar_similaridade

    async def obter_por_numero(self, numero: str) -> Precedente | None:
        linha = await self._db.fetchrow(
            f"SELECT {self._COLUNAS} FROM precedentes_verificados "
            f"WHERE numero_normalizado = $1 AND {self._CITAVEL}",
            normalizar_citacao(numero),
        )
        return Precedente.de_dict(linha) if linha else None

    async def buscar_por_tags(self, tags: Sequence[str]) -> list[Precedente]:
        alvo = [t.strip().lower() for t in tags if t.strip()]
        if not alvo:
            return []
        linhas = await self._db.fetch(
            f"SELECT {self._COLUNAS} FROM precedentes_verificados "
            f"WHERE tags && $1::text[] AND {self._CITAVEL}",
            alvo,
        )
        return [Precedente.de_dict(l) for l in linhas]

    async def buscar_por_semelhanca(
        self,
        query: str,
        limite: int = 5,
        *,
        tribunal: str | None = None,
        tema: str | None = None,
    ) -> list[Precedente]:
        """Busca vetorial (operador <=>, distância de cosseno) com fallback.

        Filtros opcionais de metadados entram na PRÓPRIA consulta (binds
        numerados dinamicamente), nunca como pós-filtro no repositório —
        pós-filtrar o top-K de fora destrói recall e paginação. No pgvector
        o WHERE é pós-filtro do índice HNSW; a migração 0003 fixa
        ``hnsw.iterative_scan`` no nível do banco para o LIMIT continuar
        sendo satisfeito com filtros seletivos.

        Cenários de contingência (nunca exceção para o chamador):
        1. Embedder não injetado (zero-credencial) → fallback por tags.
        2. Falha do provedor de embeddings ou do banco → log + fallback.
        Registros sem ``vetor_semantico`` (backfill pendente) são ignorados
        pela consulta vetorial — o fallback os cobre.
        """
        if not query.strip():
            return []
        if self._embedder is None:
            return await self._fallback_tags(
                query, limite, tribunal=tribunal, tema=tema
            )
        try:
            vetores = await self._embedder.embed([query])
            literal = _vetor_para_sql(vetores[0])
            params: list = [literal, self._limiar]
            filtros = ""
            if tribunal is not None:
                params.append(tribunal.strip())
                filtros += f" AND upper(tribunal) = upper(${len(params)})"
            if tema is not None:
                params.append(tema.strip())
                filtros += f" AND upper(tema) = upper(${len(params)})"
            params.append(limite)
            linhas = await self._db.fetch(
                f"SELECT {self._COLUNAS}, "
                f"1 - (vetor_semantico <=> $1::vector) AS similaridade "
                f"FROM precedentes_verificados "
                f"WHERE {self._CITAVEL} AND vetor_semantico IS NOT NULL "
                f"AND 1 - (vetor_semantico <=> $1::vector) >= $2"
                f"{filtros} "
                f"ORDER BY vetor_semantico <=> $1::vector "
                f"LIMIT ${len(params)}",
                *params,
            )
            return [Precedente.de_dict(l) for l in linhas]
        except Exception:  # noqa: BLE001 — contingência deliberada
            logger.warning(
                "busca semântica indisponível (embedder/banco); usando "
                "fallback por tags", exc_info=True,
            )
            return await self._fallback_tags(
                query, limite, tribunal=tribunal, tema=tema
            )

    async def _fallback_tags(
        self,
        query: str,
        limite: int,
        *,
        tribunal: str | None = None,
        tema: str | None = None,
    ) -> list[Precedente]:
        """Fallback honesto que NÃO alarga o escopo: os mesmos filtros de
        metadados da rota vetorial valem aqui (aplicados em Python, já que
        ``buscar_por_tags`` mantém seu contrato próprio)."""
        achados = await self.buscar_por_tags(_tokens_de_busca(query))
        filtrados = [p for p in achados if _passa_filtros(p, tribunal, tema)]
        return filtrados[:limite]
