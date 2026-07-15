"""Adapter DossierHunter → Auditoria de Silêncio.

Converte OMISSÕES do dossiê (ausências que deveriam estar nos autos) em
linhas de `fontes_silenciadas`, o mesmo vocabulário que o Feito já usa.
NÃO converte AFIRMAÇÕES aqui — essas viram Fato/Vulnerabilidade e passam
pelo HALT (fora do escopo da v1).
"""

from __future__ import annotations

from .schema import DossierHunterSchema


def dossier_para_fontes_silenciadas(dossier: DossierHunterSchema) -> list[str]:
    """Extrai as omissões do dossiê como linhas de Auditoria de Silêncio.

    Ordem estável: desvios de magistrado → cadeia de custódia → filtros de
    omissão (contemporaneidade, ata, quebras sequenciais) → omissões livres.
    """
    linhas: list[str] = []

    for d in dossier.auditoria_magistrados:
        if d.eh_omissao:
            linhas.append(
                f"Portaria de designação de {d.juiz_prolator} para o ato "
                f"'{d.ato_referencia}' ({d.data_ato.isoformat()}) — ausente ou "
                "não localizada em fonte pública (desvio de juiz natural)"
            )

    for m in dossier.midias_e_pericias:
        if not m.hash_presente or not m.cadeia_custodia_integra:
            linhas.append(
                f"Cadeia de custódia da mídia {m.id_documento} ({m.tipo_midia}) — "
                "hash de integridade ausente ou custódia não íntegra "
                "(art. 158-A ss. CPP)"
            )

    filtros = dossier.filtros_omissao
    if filtros.omissao_analise_contemporaneidade:
        linhas.append(
            "Fundamentação sobre contemporaneidade/atualidade da medida cautelar "
            "— ausente"
        )
    if filtros.ausencia_ata_plenario:
        linhas.append("Ata da sessão plenária do Júri — ausente")

    for g in filtros.quebra_sequencial_ids:
        ctx = f" ({g.contexto})" if g.contexto else ""
        linhas.append(
            f"Quebra sequencial de IDs no PJe: eventos {g.de}–{g.ate}{ctx}"
        )

    linhas.extend(filtros.omissoes_livres)

    return linhas
