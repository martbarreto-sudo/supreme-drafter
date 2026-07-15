"""Auditoria de citações — o portão que o adversarial_auditor consulta.

Extrai as citações jurisprudenciais de uma minuta e classifica cada uma
contra uma ``FonteDePrecedentes``. Qualquer citação não encontrada na base
verificada é BLOQUEANTE (``precedente_nao_verificado``) e o veredito da
peça vira NAO_PROTOCOLAVEL — a regra ``zero_tolerance`` que o gate de
peer-review aplica, agora com chão de verdade real.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .fontes import FonteDePrecedentes
from .precedente import Precedente, normalizar_citacao

# Classes processuais e enunciados citados em peças criminais.
# Limitação conhecida: entradas compostas da base (ex.: "ADC 43, 44 e 54")
# só casam quando citadas na mesma forma composta; "ADC 43" isolado extrai
# "ADC 43" e será bloqueado se não houver registro próprio — conservador
# por desenho (nada passa sem correspondência exata na base).
_PADRAO_CITACAO = re.compile(
    r"""
    (?:
        (?P<adc_composta>ADC\s*\d+(?:\s*,\s*\d+)*\s+e\s+\d+)
      |
        (?P<classe>HC|RHC|AgRg\ no\ HC|AgRg\ no\ RHC|REsp|AREsp|ADC|ADI|RE|ARE)
        \s*(?P<numero>[\d.]+)
        (?:\s*/\s*(?P<uf>[A-Z]{2}))?
      |
        S[úu]mula
        (?:\s+(?P<vinculante>Vinculante))?
        \s*(?:n[ºo.]?\s*)?(?P<sumula>\d+)
        (?:\s*(?:/|do\s+|da\s+)(?P<corte>STF|STJ))?
      |
        Tema\s*(?:n[ºo.]?\s*)?(?P<tema>\d+)
    )
    """,
    re.VERBOSE | re.IGNORECASE,
)


@dataclass(frozen=True)
class CitacaoAuditada:
    citacao: str                       # como apareceu na peça
    normalizada: str
    verificada: bool
    precedente: Precedente | None = None


@dataclass(frozen=True)
class RelatorioAuditoria:
    citacoes: tuple[CitacaoAuditada, ...]

    @property
    def nao_verificadas(self) -> tuple[CitacaoAuditada, ...]:
        return tuple(c for c in self.citacoes if not c.verificada)

    @property
    def protocolavel(self) -> bool:
        """zero_tolerance: uma única citação não verificada já bloqueia."""
        return not self.nao_verificadas

    @property
    def veredito(self) -> str:
        return "PROTOCOLAVEL" if self.protocolavel else "NAO_PROTOCOLAVEL"


def extrair_citacoes(texto: str) -> list[str]:
    """Citações jurisprudenciais encontradas no texto, na ordem, sem repetição."""
    vistas: set[str] = set()
    resultado: list[str] = []
    for m in _PADRAO_CITACAO.finditer(texto):
        if m.group("adc_composta"):
            citacao = m.group("adc_composta")
        elif m.group("classe"):
            citacao = f"{m.group('classe')} {m.group('numero')}"
            if m.group("uf"):
                citacao += f"/{m.group('uf')}"
        elif m.group("sumula"):
            if m.group("vinculante"):
                citacao = f"Súmula Vinculante {m.group('sumula')}"
            else:
                citacao = f"Súmula {m.group('sumula')}"
                if m.group("corte"):
                    citacao += f"/{m.group('corte').upper()}"
        else:
            citacao = f"Tema {m.group('tema')}"
        chave = normalizar_citacao(citacao)
        if chave not in vistas:
            vistas.add(chave)
            resultado.append(citacao)
    return resultado


async def auditar_citacoes(
    texto: str, fonte: FonteDePrecedentes
) -> RelatorioAuditoria:
    """Audita todas as citações do texto contra a base verificada."""
    auditadas: list[CitacaoAuditada] = []
    for citacao in extrair_citacoes(texto):
        precedente = await fonte.obter_por_numero(citacao)
        auditadas.append(
            CitacaoAuditada(
                citacao=citacao,
                normalizada=normalizar_citacao(citacao),
                verificada=precedente is not None,
                precedente=precedente,
            )
        )
    return RelatorioAuditoria(citacoes=tuple(auditadas))
