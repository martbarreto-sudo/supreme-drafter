"""Quality Gate Pipeline — Gap 1 (epistemologia verificável) + Gap 4 (validação).

Generaliza o validar_feito_hbm hardcoded para uma bateria de gates determinísticos
que rodam sobre a minuta gerada e produzem um quality_score auditável. Cada gate
verifica um traço epistemológico do protocolo Nexum: fonte por fato, precedente do
eixo, auditoria de silêncio, e Assinatura Tigre (ausência de submissão burocrática).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .models import Fato, Feito


@dataclass
class GateResult:
    name: str
    passed: bool
    detail: str


@dataclass
class QualityReport:
    score: int  # 0-100
    gates: list[GateResult]

    @property
    def gates_passed(self) -> list[str]:
        return [g.name for g in self.gates if g.passed]

    @property
    def gates_failed(self) -> list[GateResult]:
        return [g for g in self.gates if not g.passed]

    def to_dict(self) -> dict:
        return {
            "score": self.score,
            "gates": [
                {"name": g.name, "passed": g.passed, "detail": g.detail}
                for g in self.gates
            ],
        }


# Termos de submissão burocrática vetados pela Assinatura Tigre
_SUBMISSAO = ["data venia", "data vênia", "ousamos", "mui respeitosamente", "vossa excelência se digne"]

# Tokens que parecem referência a precedente/súmula/tema
_PRECEDENTE_RE = re.compile(
    r"(Tema\s*\d|Súmula\s*\d|Sumula\s*\d|HC\s*\d|RHC\s*\d|RE\s*\d|REsp\s*\d|ADPF\s*\d|ADI\s*\d)",
    re.IGNORECASE,
)


def _tokens_precedente(texto: str) -> set[str]:
    """Extrai tokens-chave de precedente (dígitos contíguos) para cotejo robusto a pontuação."""
    return set(re.findall(r"\d{2,}", texto))


def _gate_fonte_por_fato(minuta: str, fatos: list[Fato]) -> GateResult:
    dispositivos = [f for f in fatos if f.dispositivo and f.fonte is not None]
    if not dispositivos:
        return GateResult("fonte_por_fato", True, "Sem fatos dispositivos a citar")
    faltando = [
        f.id
        for f in dispositivos
        if not any(tok in minuta for tok in _ref_tokens(f.fonte.uri))
    ]
    ok = not faltando
    detail = "Todas as fontes primárias referenciadas" if ok else f"Fontes não citadas: {faltando}"
    return GateResult("fonte_por_fato", ok, detail)


def _ref_tokens(uri: str) -> list[str]:
    """Tokens identificadores de uma fonte para detectar sua citação na minuta.

    Ex.: certidao://feito-hbm/inquerito-fls-12 → ['certidao', 'feito-hbm', 'inquerito-fls-12', '12']
    """
    corpo = uri.split("://", 1)[-1]
    partes = re.split(r"[/\-_]", corpo)
    tokens = [uri.split("://", 1)[0]] + [p for p in partes if p]
    return [t for t in tokens if len(t) >= 2]


def _gate_precedente_do_eixo(minuta: str, feito: Feito) -> GateResult:
    esperados = _tokens_precedente(feito.eixo_dogmatico)
    if not esperados:
        return GateResult("precedente_do_eixo", True, "Eixo sem precedente numérico explícito")
    presentes = _tokens_precedente(minuta)
    faltando = esperados - presentes
    ok = not faltando
    detail = (
        f"Precedentes do eixo presentes: {sorted(esperados)}"
        if ok
        else f"Precedentes do eixo ausentes na minuta: {sorted(faltando)}"
    )
    return GateResult("precedente_do_eixo", ok, detail)


def _gate_auditoria_silencio(minuta: str) -> GateResult:
    ok = "AUDITORIA DE SILÊNCIO" in minuta.upper() or "AUDITORIA DE SILENCIO" in minuta.upper()
    return GateResult(
        "auditoria_silencio",
        ok,
        "Bloco de Auditoria de Silêncio presente" if ok else "Auditoria de Silêncio ausente",
    )


def _gate_pedido(minuta: str) -> GateResult:
    upper = minuta.upper()
    ok = "PEDIDO" in upper or "REQUER" in upper
    return GateResult(
        "pedido_presente",
        ok,
        "Pedido presente" if ok else "Nenhum pedido/requerimento identificado",
    )


def _gate_assinatura_tigre(minuta: str) -> GateResult:
    baixo = minuta.lower()
    achados = [t for t in _SUBMISSAO if t in baixo]
    ok = not achados
    return GateResult(
        "assinatura_tigre",
        ok,
        "Sem submissão burocrática" if ok else f"Submissão burocrática detectada: {achados}",
    )


def avaliar_qualidade(minuta: str, feito: Feito, fatos: list[Fato]) -> QualityReport:
    gates = [
        _gate_fonte_por_fato(minuta, fatos),
        _gate_precedente_do_eixo(minuta, feito),
        _gate_auditoria_silencio(minuta),
        _gate_pedido(minuta),
        _gate_assinatura_tigre(minuta),
    ]
    aprovados = sum(1 for g in gates if g.passed)
    score = round(100 * aprovados / len(gates))
    return QualityReport(score=score, gates=gates)
