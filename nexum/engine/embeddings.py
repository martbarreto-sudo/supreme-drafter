"""Contrato de embedder e um fake deterministico para testes sem rede.

`Embedder` e um Protocol: qualquer objeto com `embed(texts) -> list[list[float]]`
serve. `DeterministicFakeEmbedder` deriva vetores estaveis de um hash SHA-256 do
texto (sem `random`, sem relogio, sem rede), tornando os testes de recuperacao
100% reproduziveis. O provedor real (Gemini/Vertex) e uma importacao LAZY que
hoje apenas sinaliza `NotImplementedError` — nao adiciona dependencias pesadas.
"""

from __future__ import annotations

import hashlib
import os
import struct
from typing import Protocol, runtime_checkable

from nexum.engine.vectors import EMBEDDING_DIM, l2_normalize


@runtime_checkable
class Embedder(Protocol):
    """Contrato minimo de um gerador de embeddings.

    `embed` recebe uma lista de textos e retorna uma lista de vetores, cada um
    com `EMBEDDING_DIM` posicoes (ou a dimensao configurada do embedder).
    """

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Retorna um embedding por texto, na mesma ordem da entrada."""
        ...


class DeterministicFakeEmbedder:
    """Embedder fake e deterministico: mesmo texto -> mesmo vetor unitario.

    Cada posicao `i` do vetor deriva de `sha256(f"{text}#{i}")`, mapeada para
    [-1, 1); o vetor final e L2-normalizado (norma == 1). Textos diferentes
    produzem vetores diferentes com probabilidade altissima. Sem rede, sem
    estado global, sem aleatoriedade — ideal para testes de ranking.
    """

    def __init__(self, dim: int = EMBEDDING_DIM) -> None:
        if dim <= 0:
            raise ValueError("dim deve ser positivo")
        self.dim = dim

    def _vector_for(self, text: str) -> list[float]:
        raw: list[float] = []
        for i in range(self.dim):
            digest = hashlib.sha256(f"{text}#{i}".encode("utf-8")).digest()
            # 8 bytes -> inteiro sem sinal de 64 bits -> [-1, 1).
            (value,) = struct.unpack(">Q", digest[:8])
            raw.append((value / 2**63) - 1.0)
        # Normaliza; a chance de vetor zero e desprezivel, mas o guard fica em
        # l2_normalize. Passa dim explicito para independer da env global.
        return l2_normalize(raw, dim=self.dim)

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._vector_for(text) for text in texts]


def build_embedder_from_env() -> Embedder:
    """Constroi o embedder conforme `NEXUM_EMBEDDING_PROVIDER` (default: fake).

    - ausente ou "fake" => `DeterministicFakeEmbedder` (offline, testavel);
    - "gemini"/"vertex" => provedor real (importacao LAZY, hoje um stub que
      levanta `NotImplementedError` — a fiacao com Gemini/Vertex e o proximo
      passo e nao deve arrastar dependencias pesadas para este pacote).
    """

    provider = os.environ.get("NEXUM_EMBEDDING_PROVIDER", "fake").lower()
    if provider in ("", "fake"):
        return DeterministicFakeEmbedder()
    if provider in ("gemini", "vertex"):
        raise NotImplementedError(
            "wire Gemini/Vertex here "
            "(provedor real de embeddings ainda nao implementado)"
        )
    raise ValueError(f"NEXUM_EMBEDDING_PROVIDER desconhecido: {provider!r}")
