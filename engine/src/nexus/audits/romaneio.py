"""Composição do Romaneio de Revisão — formato canônico do HITL gate.

Replica o ritual operacional documentado em `ROMANEIO DE REVISAO — RAPHAEL`
(vide docs/audit-drive-gems.md §3). Cada peça gerada recebe um romaneio
que classifica:

- [NIVEL 1 — DISPARAR]: peça fechada, pronta para protocolo após assinatura.
- [NIVEL 2 — CONDICIONADA]: peça pronta na forma, mas condicionada a fatos
  da moldura subjacente que só a fonte/advogado confirma.

NUNCA emite "aprovado para protocolo" (TIER 0 §4 — protocolo é decisão
humana exclusiva).
"""

from __future__ import annotations

from nexus.auditor import AuditorAdversarialReport, Severity
from nexus.models import Feito
from nexus.quality import QualityReport


def _status(
    quality: QualityReport,
    auditor: AuditorAdversarialReport,
    assertions_falhas: list[str],
) -> tuple[str, str]:
    """Calcula status + razão. Critério de NIVEL 1: score==100 +
    auditor==APROVA_PARA_CURADORIA + zero assertions_falhas.
    Qualquer outra coisa = NIVEL 2 — CONDICIONADA."""
    if (
        quality.score == 100
        and auditor.decisao == "APROVA_PARA_CURADORIA"
        and not assertions_falhas
    ):
        return ("[NIVEL 1 — DISPARAR]", "peça fechada, pronta para protocolo após assinatura")
    return (
        "[NIVEL 2 — CONDICIONADA]",
        "peça pronta na forma, mas condicionada a dado(s) da moldura subjacente",
    )


def _condicoes(
    quality: QualityReport,
    auditor: AuditorAdversarialReport,
    assertions_falhas: list[str],
) -> list[str]:
    """Lista as condições a fechar antes do disparo. Ordem: ALTA → MEDIA →
    BAIXA do auditor, depois gates de quality falhos, depois assertions."""
    cond: list[str] = []
    for severity in (Severity.ALTA, Severity.MEDIA, Severity.BAIXA):
        for f in auditor.findings:
            if f.severity != severity:
                continue
            evid = f" — `{f.evidence}`" if f.evidence else ""
            cond.append(f"[AUDITOR/{severity.value}] {f.description}{evid}")
    for gate in quality.gates_failed:
        cond.append(f"[QUALITY/{gate.name}] {gate.detail}")
    for falha in assertions_falhas:
        cond.append(f"[ASSERTION] {falha}")
    return cond


def compor_romaneio(
    *,
    audit_id: str,
    feito: Feito,
    peca_tipo: str,
    modelo: str,
    quality: QualityReport,
    auditor: AuditorAdversarialReport,
    assertions_falhas: list[str],
    data_iso: str,
) -> str:
    """Devolve o markdown do romaneio. Caller persiste em
    `$CASO_DATA_DIR/{user_id}/audits/{audit_id}.romaneio.md`.

    Não inclui texto da minuta — o curador lê em `{audit_id}.md`.
    """
    status, razao = _status(quality, auditor, assertions_falhas)
    condicoes = _condicoes(quality, auditor, assertions_falhas)

    linhas: list[str] = []
    linhas.append(f"# ROMANEIO DE REVISÃO — {feito.id}")
    linhas.append("")
    linhas.append(
        f"Gerado pela engine Nexus em {data_iso}. Esta é a penúltima camada — "
        "a chancela final é do advogado-operador OAB."
    )
    linhas.append("")
    linhas.append("## LEGENDA")
    linhas.append("")
    linhas.append("- `[NIVEL 1 — DISPARAR]` peça fechada, pronta para protocolo após assinatura.")
    linhas.append(
        "- `[NIVEL 2 — CONDICIONADA]` peça pronta na forma, mas condicionada a dado(s) "
        "da moldura factica subjacente que só a fonte/advogado confirma. **NÃO protocolar** "
        "antes de fechar a condição."
    )
    linhas.append("")
    linhas.append("================================================================")
    linhas.append("")
    linhas.append(f"## PEÇA — {peca_tipo}")
    linhas.append("")
    linhas.append(f"- **Feito:** {feito.id} ({feito.quadrante})")
    linhas.append(f"- **Eixo dogmático:** {feito.eixo_dogmatico}")
    if feito.tribunal_destino:
        linhas.append(f"- **Destinatário:** {feito.tribunal_destino}")
    if feito.peca_alvo:
        linhas.append(f"- **Peça-alvo do eixo:** {feito.peca_alvo}")
    linhas.append(f"- **Modelo:** {modelo}")
    linhas.append(
        f"- **Quality score:** {quality.score}/100  ·  "
        f"**Auditor:** {auditor.decisao}"
    )
    linhas.append(f"- **Arquivo da minuta:** `audits/{audit_id}.md`")
    linhas.append("")
    linhas.append(f"## STATUS: {status}")
    linhas.append("")
    linhas.append(f"_{razao}_")
    linhas.append("")

    if condicoes:
        linhas.append("## Condições a fechar antes do disparo")
        linhas.append("")
        for i, c in enumerate(condicoes, 1):
            linhas.append(f"({chr(96 + i) if i <= 26 else i}) {c}")
        linhas.append("")

    if feito.fontes_silenciadas:
        linhas.append("## Auditoria de Silêncio (registrar nos autos se ausente)")
        linhas.append("")
        for item in feito.fontes_silenciadas:
            linhas.append(f"- {item}")
        linhas.append("")

    linhas.append("================================================================")
    linhas.append("")
    linhas.append(
        "*A auditoria é a penúltima camada; a chancela final é do advogado com OAB.*"
    )
    return "\n".join(linhas)
