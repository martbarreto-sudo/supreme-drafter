"""Disclaimer obrigatório em toda peça gerada + versionamento de TOS.

Por que disclaimer no topo (não no rodapé): se a peça for impressa
parcialmente, copiada para outra ferramenta, ou compartilhada por print,
o aviso vai junto. Rodapé seria fácil de cortar.

TOS_VERSION_ATUAL é incrementado a cada versão nova do TOS. Usuários com
versão antiga precisam re-aceitar (não implementado nesta fase — gancho
para futuro: middleware que checa user.tos_version < TOS_VERSION_ATUAL).
"""

from __future__ import annotations

from nexus.db.models import User

TOS_VERSION_ATUAL = 1

DISCLAIMER_TEMPLATE = """\
<!-- ============================================================
NEXUS BY TIGRE — MINUTA AUTOMATIZADA, NÃO PROTOCOLAR SEM REVISÃO
============================================================

Documento gerado pelo motor Nexus em {data} para o advogado-operador:

  {nome_advogado}
  OAB/{uf} {numero}

Esta minuta é fruto de pipeline determinístico (Dado Líquido + HALT +
quality gates) + síntese por Modelo de Linguagem. **NÃO é peça jurídica
final**: cabe ao advogado-operador acima nomeado revisar integralmente,
ajustar onde a estratégia processual exigir, e assinar sob sua OAB
antes de protocolar.

A plataforma Nexus é ferramenta de produtividade para advogados; não
exerce advocacia, não emite parecer jurídico, não substitui a análise
técnica humana. Responsabilidade técnica é integralmente do
advogado-operador identificado acima.

============================================================ -->

"""


def prepend_disclaimer(texto: str, user: User, data_iso: str) -> str:
    """Adiciona o cabeçalho de disclaimer ao topo da minuta."""
    header = DISCLAIMER_TEMPLATE.format(
        data=data_iso,
        nome_advogado=user.name,
        uf=user.oab_uf,
        numero=user.oab_numero,
    )
    return header + texto
