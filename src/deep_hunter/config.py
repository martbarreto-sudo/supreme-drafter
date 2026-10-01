"""Configuração central: modelo, modos de investigação e comandos de auditoria."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum

# Modelo padrão. `claude-opus-4-8` não aceita `temperature` (a especificação pede
# "temperatura zero"); o determinismo é obtido via effort + contrato de grounding.
DEFAULT_MODEL = os.environ.get("DEEP_HUNTER_MODEL", "claude-opus-4-8")
DEFAULT_EFFORT = os.environ.get("DEEP_HUNTER_EFFORT", "high")

# Níveis aceites por `output_config.effort`. Um valor fora desta lista só falhava
# no servidor (HTTP 400) — depois de os autos terem sido lidos e transmitidos.
EFFORTS_VALIDOS = ("low", "medium", "high", "xhigh", "max")


class Provedor(str, Enum):
    """Canal por onde o motor fala com o modelo.

    `ANTHROPIC` é a API comercial de primeira parte (padrão). `VERTEX` serve o
    Claude de forma gerida dentro do perímetro do Google Cloud do cliente — a rota
    para quem exige que os autos não saiam da sua própria nuvem.
    """

    ANTHROPIC = "anthropic"
    VERTEX = "vertex"


def provedor_do_ambiente() -> str:
    """Lê `DEEP_HUNTER_PROVEDOR` no momento da construção, não no do import.

    Ao contrário de `DEFAULT_MODEL`/`DEFAULT_EFFORT` (fixados no import), isto
    permite comutar de canal sem reimportar o pacote — e torna a comutação
    testável sem recarregar módulos.
    """
    return os.environ.get("DEEP_HUNTER_PROVEDOR", Provedor.ANTHROPIC.value)

# Streaming é obrigatório para max_tokens grande (evita timeout HTTP do SDK).
MAX_TOKENS = 32000


class Modo(str, Enum):
    """Modos de investigação do Deep Hunter (V12.0 Apex Singularity)."""

    CRONOS = "CRONOS"
    FORENSE = "FORENSE"
    POLIGRAFO = "POLIGRAFO"
    SIMBIOSE = "SIMBIOSE"

    @property
    def foco(self) -> str:
        return {
            Modo.CRONOS: (
                "Cronologia existencial dos factos e lapsos temporais na cadeia de "
                "custódia. Reconstrua a linha do tempo e sinalize toda descontinuidade."
            ),
            Modo.FORENSE: (
                "Exame técnico exclusivo de metadados, endereços IP, chaves hash e "
                "laudos periciais. DESCONSIDERE depoimentos orais."
            ),
            Modo.POLIGRAFO: (
                "Confronto de contradições lógicas e factuais entre depoimentos "
                "prestados na fase policial e na instrução judicial."
            ),
            Modo.SIMBIOSE: (
                "Varredura padrão concorrente: falhas de Cadeia de Custódia, "
                "Competência jurisdicional e Contemporaneidade da medida cautelar."
            ),
        }[self]


class Comando(str, Enum):
    """Comandos específicos de auditoria (Cmd Hunter)."""

    HASH_AUDIT = "HASH_AUDIT"
    WRITE_BLOCKER = "WRITE_BLOCKER"
    CLOUD_EXTRACTION = "CLOUD_EXTRACTION"

    @property
    def diretriz(self) -> str:
        return {
            Comando.HASH_AUDIT: (
                "Cmd Hunter 01 — valide as assinaturas criptográficas (hash) de cada "
                "arquivo digital. A ausência de registo de hash rompe o princípio da "
                "mesmidade (AgRg no HC 828.054-RN, Inf. 811 STJ)."
            ),
            Comando.WRITE_BLOCKER: (
                "Cmd Hunter 03 — audite se a polícia utilizou bloqueadores físicos de "
                "escrita (write blocker) ao extrair dados via Cellebrite/IPED, "
                "garantindo que o suporte original não sofreu mutações."
            ),
            Comando.CLOUD_EXTRACTION: (
                "Cmd Hunter 04 — identifique acesso remoto não autorizado "
                "judicialmente a contas em nuvem (WhatsApp Web / iCloud)."
            ),
        }[self]


@dataclass(frozen=True)
class RunConfig:
    """Configuração de uma execução do pipeline."""

    model: str = DEFAULT_MODEL
    effort: str = DEFAULT_EFFORT
    max_tokens: int = MAX_TOKENS
    provedor: str = field(default_factory=provedor_do_ambiente)

    def __post_init__(self) -> None:
        if self.effort not in EFFORTS_VALIDOS:
            raise ValueError(
                f"Nível de esforço inválido: {self.effort!r}. "
                f"Use um de {', '.join(EFFORTS_VALIDOS)} "
                "(variável DEEP_HUNTER_EFFORT)."
            )
        if self.provedor not in tuple(p.value for p in Provedor):
            raise ValueError(
                f"Provedor inválido: {self.provedor!r}. "
                f"Use um de {', '.join(p.value for p in Provedor)} "
                "(variável DEEP_HUNTER_PROVEDOR)."
            )
