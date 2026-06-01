"""Auditor Adversarial — Camada 4 do TIER 0 (vide docs/tier-0-protocolo.md).

> "O nó que redige não é o nó que aprova."

Esta camada implementa o mandato do AUDITOR FORENSE (gem auditado em
docs/audit-drive-gems.md §3): assumir a perspectiva do promotor adversário e
do relator cético, e **tentar derrubar** a minuta caçando:

1. Cegueira deliberada documental — fato dispositivo no input que NÃO
   aparece na minuta (silenciamento)
2. Citação não verificada — referência a precedente/súmula sem âncora em
   "fonte" do Dado Líquido
3. Vocabulário vetado — passivo/submissão burocrática que o TIER 0 §1
   bane (data venia, ousamos, mui respeitosamente, vossa excelência se
   digne, sucumbente sempre)
4. Autoelogio na peça — adjetivo do autor que TIER 0 §1 proíbe (fulminante,
   destruição científica, esmagador, irrefutável quando aplicado à própria
   peça)
5. Endereçamento ausente — peça processual sem endereçamento ao juízo

Output: AuditorAdversarialReport com lista de Findings categorizados por
severidade. Decisão final (REPROVA vs APROVA_PARA_CURADORIA com ressalvas)
deriva do agregado das severidades — alta severidade reprova; média gera
ressalva; baixa registra mas aprova.

Não confunde com `quality.py` (gates determinísticos de qualidade técnica,
positivos). Auditor é adversarial — busca o que está errado, não confirma
o que está certo.
"""

from __future__ import annotations

import enum
import re
from dataclasses import dataclass, field

from nexus.models import Fato


class Severity(str, enum.Enum):
    BAIXA = "BAIXA"      # registrar, não bloqueia
    MEDIA = "MEDIA"      # APROVA_PARA_CURADORIA com ressalva
    ALTA = "ALTA"        # REPROVA


@dataclass(frozen=True)
class Finding:
    code: str
    severity: Severity
    description: str
    evidence: str = ""  # trecho da minuta ou ID do fato problemático


@dataclass
class AuditorAdversarialReport:
    findings: list[Finding] = field(default_factory=list)

    @property
    def decisao(self) -> str:
        if any(f.severity == Severity.ALTA for f in self.findings):
            return "REPROVA"
        if any(f.severity == Severity.MEDIA for f in self.findings):
            return "APROVA_PARA_CURADORIA_COM_RESSALVAS"
        return "APROVA_PARA_CURADORIA"

    @property
    def findings_por_severidade(self) -> dict[str, list[Finding]]:
        out: dict[str, list[Finding]] = {"ALTA": [], "MEDIA": [], "BAIXA": []}
        for f in self.findings:
            out[f.severity.value].append(f)
        return out

    def to_dict(self) -> dict:
        return {
            "decisao": self.decisao,
            "findings": [
                {
                    "code": f.code,
                    "severity": f.severity.value,
                    "description": f.description,
                    "evidence": f.evidence,
                }
                for f in self.findings
            ],
            "total_por_severidade": {
                k: len(v) for k, v in self.findings_por_severidade.items()
            },
        }


# --- Passo 1: cegueira deliberada documental ---

# Tokens "verbais" de um fato que podem aparecer na minuta como referência
# implícita. Heurística: split por palavras significantes do `proposto` ou
# `verificado` e checar se alguma combinação aparece no texto da minuta.
_STOPWORDS = {
    "o", "a", "os", "as", "um", "uma", "uns", "umas", "de", "do", "da", "dos",
    "das", "em", "no", "na", "nos", "nas", "por", "para", "com", "sem", "que",
    "se", "e", "ou", "à", "às", "ao", "aos", "como", "já", "foi", "ser",
    "está", "estão", "este", "esta", "estes", "estas", "isso", "isto", "tal",
    "qual", "quais", "também", "ainda", "mas", "porém", "contudo",
}


def _tokens_relevantes(texto: str) -> set[str]:
    return {
        t.lower()
        for t in re.findall(r"\b[\wáéíóúâêôãõçÁÉÍÓÚÂÊÔÃÕÇ]+\b", texto)
        if len(t) >= 4 and t.lower() not in _STOPWORDS
    }


def _gate_cegueira_deliberada(minuta: str, fatos: list[Fato]) -> list[Finding]:
    """Cada fato dispositivo do input precisa ter eco na minuta.

    Sinal de presença: ≥40% dos tokens relevantes do `verificado` (ou
    `proposto`, se verificado vazio) aparecem na minuta. Abaixo disso, o
    fato foi silenciado.
    """
    findings: list[Finding] = []
    minuta_tokens = _tokens_relevantes(minuta)
    for fato in fatos:
        if not fato.dispositivo:
            continue
        base = fato.verificado or fato.proposto
        fato_tokens = _tokens_relevantes(base)
        if not fato_tokens:
            continue
        overlap = len(fato_tokens & minuta_tokens)
        ratio = overlap / len(fato_tokens)
        if ratio < 0.4:
            findings.append(
                Finding(
                    code="cegueira_deliberada",
                    severity=Severity.ALTA,
                    description=(
                        f"Fato dispositivo `{fato.id}` não tem eco substantivo "
                        f"na minuta (overlap={ratio:.0%})"
                    ),
                    evidence=base[:200],
                )
            )
    return findings


# --- Passo 2: citação não verificada ---

# Padrões de citação que exigem âncora em "fonte" (verificada via Dado Líquido).
# Heurística MVP: detecta tokens-padrão; verificação real (consulta tribunal)
# fica como handoff para o curador humano. Falha aqui flag → MEDIA, não ALTA,
# porque pode ser citação válida ainda não anotada.
_PADROES_CITACAO = [
    re.compile(r"\bS[úu]mula\s+(?:Vinculante\s+)?(\d+)", re.IGNORECASE),
    re.compile(r"\bTema\s+(\d+(?:\.\d+)?)", re.IGNORECASE),
    re.compile(r"\bHC\s+(\d+\.?\d*)", re.IGNORECASE),
    re.compile(r"\bRHC\s+(\d+\.?\d*)", re.IGNORECASE),
    re.compile(r"\bREsp\s+(\d+\.?\d*)", re.IGNORECASE),
    re.compile(r"\b(?:R\.?E|RExt)\s+(\d+\.?\d*)", re.IGNORECASE),
    re.compile(r"\bRcl\s+(\d+\.?\d*)", re.IGNORECASE),
    re.compile(r"\bAgRg(?:\s+(?:em|no)\s+\w+)?\s+(\d+\.?\d*)", re.IGNORECASE),
]


def _gate_citacao_nao_verificada(minuta: str, fatos: list[Fato]) -> list[Finding]:
    """Cada citação a precedente/súmula/tema precisa de fonte rastreável."""
    findings: list[Finding] = []
    # Coleta as fontes ancoradas em fatos do Dado Líquido (texto verificado)
    fontes_textos = " ".join(
        (f.verificado or "") for f in fatos if f.fonte is not None
    ).lower()

    citacoes_encontradas: set[tuple[str, str]] = set()
    for padrao in _PADROES_CITACAO:
        for match in padrao.finditer(minuta):
            ref = match.group(0).strip()
            numero = match.group(1)
            citacoes_encontradas.add((ref, numero))

    for ref, numero in citacoes_encontradas:
        # Se o número da citação aparece nas fontes do Dado Líquido, OK.
        # Senão, sinaliza para curador verificar no tribunal.
        if numero not in fontes_textos:
            findings.append(
                Finding(
                    code="citacao_nao_verificada",
                    severity=Severity.MEDIA,
                    description=(
                        f"Citação `{ref}` não aparece ancorada em fonte do "
                        "Dado Líquido. Confirmar no tribunal antes do protocolo."
                    ),
                    evidence=ref,
                )
            )
    return findings


# --- Passo 3: vocabulário vetado ---

_VETADOS = [
    ("data venia", "passivo retórico"),
    ("data vênia", "passivo retórico"),
    ("ousamos", "submissão burocrática"),
    ("mui respeitosamente", "submissão burocrática"),
    ("vossa excelência se digne", "submissão burocrática"),
    ("esquizofrenia fática", "metáfora de doença mental vetada"),
    ("estupro às regras", "metáfora de violência sexual vetada"),
]


def _gate_vocabulario_vetado(minuta: str) -> list[Finding]:
    findings: list[Finding] = []
    minuta_lower = minuta.lower()
    for termo, razao in _VETADOS:
        if termo in minuta_lower:
            findings.append(
                Finding(
                    code="vocabulario_vetado",
                    severity=Severity.ALTA,
                    description=f"Termo proibido pelo TIER 0 §1: '{termo}' ({razao})",
                    evidence=termo,
                )
            )
    return findings


# --- Passo 4: autoelogio na peça ---

# TIER 0 §1: "O adjetivo é do leitor, não do autor."
# Procuramos elogio próprio só quando o termo se refere à PEÇA (não a um
# precedente externo, que pode usar "fulminante" descritivamente).
_PADROES_AUTOELOGIO = [
    re.compile(r"\b(?:esta|presente|nossa)\s+(?:tese|peça|defesa|insurgência)\s+(?:é\s+)?(fulminante|esmagadora|irrefutável|impecável|incontestável)\b", re.IGNORECASE),
    re.compile(r"\b(?:destruição|aniquilação)\s+científica\b", re.IGNORECASE),
    re.compile(r"\b(?:tese|argumentação)\s+(?:devastadora|demolidora)\b", re.IGNORECASE),
]


def _gate_autoelogio(minuta: str) -> list[Finding]:
    findings: list[Finding] = []
    for padrao in _PADROES_AUTOELOGIO:
        for match in padrao.finditer(minuta):
            findings.append(
                Finding(
                    code="autoelogio",
                    severity=Severity.MEDIA,
                    description="Adjetivação da própria peça (TIER 0 §1: adjetivo é do leitor)",
                    evidence=match.group(0),
                )
            )
    return findings


# --- Passo 5: endereçamento ausente ---

_PADROES_ENDERECAMENTO = [
    re.compile(r"\bEXCELENT[ÍI]SSIM[OA]\s+SENHOR", re.IGNORECASE),
    re.compile(r"\bMM\.?\s+JU[ÍI]ZO?\b", re.IGNORECASE),
    re.compile(r"\bColenda\s+(?:Turma|C[âa]mara|Se[çc][ãa]o)", re.IGNORECASE),
    re.compile(r"\bEgr[ée]gio\s+Tribunal", re.IGNORECASE),
]


def _gate_enderecamento(minuta: str) -> list[Finding]:
    for padrao in _PADROES_ENDERECAMENTO:
        if padrao.search(minuta):
            return []  # endereçamento presente
    return [
        Finding(
            code="enderecamento_ausente",
            severity=Severity.ALTA,
            description="Peça sem endereçamento ao juízo (EXCELENTÍSSIMO / MM. JUÍZO / Colenda etc)",
            evidence="(não encontrado)",
        )
    ]


# --- Orquestrador ---


def auditar_adversarial(
    minuta: str, fatos: list[Fato]
) -> AuditorAdversarialReport:
    """Roda os 5 gates adversariais e devolve o parecer estruturado.

    NÃO emite adjetivos como 'pronto' ou 'fulminante' (TIER 0 §4). Apenas
    REPROVA, APROVA_PARA_CURADORIA_COM_RESSALVAS ou APROVA_PARA_CURADORIA.
    A decisão final de protocolar é sempre humana.
    """
    findings: list[Finding] = []
    findings.extend(_gate_cegueira_deliberada(minuta, fatos))
    findings.extend(_gate_citacao_nao_verificada(minuta, fatos))
    findings.extend(_gate_vocabulario_vetado(minuta))
    findings.extend(_gate_autoelogio(minuta))
    findings.extend(_gate_enderecamento(minuta))
    return AuditorAdversarialReport(findings=findings)
