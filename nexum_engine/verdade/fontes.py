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
from pathlib import Path
from typing import Protocol, Sequence, runtime_checkable

from ..ports import DatabasePort
from .precedente import Precedente, normalizar_citacao


@runtime_checkable
class FonteDePrecedentes(Protocol):
    """Contrato de consulta que o auditor consome."""

    async def obter_por_numero(self, numero: str) -> Precedente | None:
        """Busca exata (normalizada) por número de precedente citável."""
        ...

    async def buscar_por_tags(self, tags: Sequence[str]) -> list[Precedente]:
        """Precedentes citáveis que tenham ao menos uma das tags."""
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

    def __init__(self, db: DatabasePort) -> None:
        self._db = db

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
