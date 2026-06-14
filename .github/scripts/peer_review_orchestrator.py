#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Orquestrador de peer-review dual-provider — NEXUM TIER 0.

Ribeiro & Tigre Advocacia Criminal · Recife/PE · OAB/PE 27.543

Este módulo é o coração do workflow `.github/workflows/peer-review.yml`. Ele:

  1. Detecta o tipo de mudança de um PR (PDF de peça em `pecas/` x código de
     engine em `engine/`/`nexum_engine/`) e roteia para o pipeline correto.
  2. Aplica o filtro LGPD determinístico ANTES de qualquer envio à API
     (whitelist das OABs dos sócios R&T 27.543 e 27.482).
  3. Extrai texto de PDFs de peças via pdfplumber (mesmo motor do engine v3.0.1).
  4. Audita a peça em dois provedores independentes:
        - Claude Opus 4.8 (Anthropic Messages API, XML in / JSON out, pré-fill `{`)
        - Gemini 3 Pro (via gemini-cli em modo headless)
  5. Consolida os dois JSONs em um veredito TIER 0 com tabela markdown
     (convergências, divergências, score médio ponderado, gate >= 97).

Padrão de prompt canônico: `references/prompts-juridicos-xml-json.md` (skill v1.5.0).

REGRA DE DESIGN: os clientes de API são injetáveis (parâmetro `client`/`runner`).
Em produção usam-se os SDKs reais; nos testes injetam-se dublês determinísticos.
Nenhum teste depende de rede — exigência do gate TIER 0 (cobertura >= 90%).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional

# --------------------------------------------------------------------------- #
# Constantes institucionais R&T (espelham nexum/constants.py do engine v3.0.1)
# --------------------------------------------------------------------------- #

# OABs dos sócios — NUNCA mascarar (preserva rastreabilidade institucional).
OAB_WHITELIST_RT: frozenset[str] = frozenset(
    {"OAB/PE 27543", "OAB/PE 27.543", "OAB/PE 27482", "OAB/PE 27.482"}
)

# Caminhos de roteamento. Tocar nesses prefixos define qual pipeline roda.
PREFIXO_PECAS: str = "pecas/"
PREFIXOS_CODIGO: tuple[str, ...] = ("engine/", "nexum_engine/")

# Score mínimo do gate TIER 0 (configurável via env TIER0_GATE_SCORE).
GATE_SCORE_PADRAO: int = 97

# Modelos canônicos (Dr. Marcelo exigiu o modelo mais avançado em cada provedor).
MODELO_CLAUDE_PADRAO: str = "claude-opus-4-8"
MODELO_GEMINI_PADRAO: str = "gemini-3-pro"


# --------------------------------------------------------------------------- #
# 1. LGPDAnonimizer — filtro determinístico pré-envio
# --------------------------------------------------------------------------- #


class LGPDAnonimizer:
    """Mascara dados pessoais sensíveis antes de enviar texto a qualquer LLM.

    Mascara CPF, CNPJ, RG, telefone, e-mail e endereço completo. Para OAB,
    preserva as inscrições dos sócios R&T (whitelist) e mascara as demais —
    inclusive a OAB de advogados de outras partes, conforme sigilo profissional
    (Lei 8.906/94, art. 7º, II) e minimização de dados (LGPD, art. 6º, III).
    """

    def __init__(self, oab_whitelist: Optional[frozenset[str]] = None) -> None:
        self.oab_whitelist = oab_whitelist or OAB_WHITELIST_RT
        # Conjunto normalizado (sem espaços) para comparação robusta.
        self._whitelist_norm = {self._norm_oab(o) for o in self.oab_whitelist}

        self.patterns: dict[str, re.Pattern[str]] = {
            "cpf": re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b"),
            "cnpj": re.compile(r"\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b"),
            "rg": re.compile(r"\b\d{1,2}\.\d{3}\.\d{3}-?[\dXx]\b"),
            "telefone": re.compile(r"\b\(?\d{2}\)?\s*9?\d{4}-?\d{4}\b"),
            "email": re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"),
            "endereco_completo": re.compile(
                r"(?i)\b(rua|avenida|av\.|alameda|travessa|pra\u00e7a)\s+[\w\s,]+,\s*\d+"
            ),
        }
        # OAB tratada à parte (precisa da lógica de whitelist).
        self._oab_re = re.compile(r"OAB/[A-Z]{2}\s*\d{1,3}(?:\.\d{3})?")

    @staticmethod
    def _norm_oab(marker: str) -> str:
        """Normaliza marcador OAB: remove espaços e pontos para comparar."""
        return marker.replace(" ", "").replace(".", "").upper()

    def _mascarar_oab(self, m: re.Match[str]) -> str:
        bruto = m.group(0)
        if self._norm_oab(bruto) in self._whitelist_norm:
            return bruto  # sócio R&T — preserva
        return "[OAB_MASCARADA]"

    def anonimizar(self, texto: str) -> str:
        """Aplica todos os filtros LGPD e devolve o texto anonimizado."""
        if not texto:
            return texto
        # OAB primeiro (whitelist), para não colidir com outros padrões.
        texto = self._oab_re.sub(self._mascarar_oab, texto)
        for nome, regex in self.patterns.items():
            texto = regex.sub(f"[{nome.upper()}_MASCARADO]", texto)
        return texto

    def contem_dado_sensivel(self, texto: str) -> bool:
        """True se ainda restar CPF/CNPJ/RG/telefone/e-mail no texto.

        Usado como verificação defensiva pós-anonimização (não deve sobrar nada).
        """
        for nome, regex in self.patterns.items():
            if nome == "endereco_completo":
                continue
            if regex.search(texto):
                return True
        return False


# --------------------------------------------------------------------------- #
# 2. PecaExtractor — PDF -> texto (pdfplumber, igual ao engine v3.0.1)
# --------------------------------------------------------------------------- #


class PecaExtractor:
    """Extrai texto de PDFs de peças usando pdfplumber.

    O `pdfplumber` é importado de forma preguiçosa (lazy) para que o módulo possa
    ser importado em ambientes de teste sem a dependência instalada.
    """

    def __init__(self, extractor: Optional[Callable[[str], str]] = None) -> None:
        # Permite injetar um extrator nos testes (sem PDF/pdfplumber real).
        self._extractor = extractor

    def extrair_texto(self, caminho_pdf: str) -> str:
        if self._extractor is not None:
            return self._extractor(caminho_pdf)
        return self._extrair_via_pdfplumber(caminho_pdf)

    @staticmethod
    def _extrair_via_pdfplumber(caminho_pdf: str) -> str:
        import pdfplumber  # import preguiçoso — só em produção

        partes: list[str] = []
        with pdfplumber.open(caminho_pdf) as pdf:
            for pagina in pdf.pages:
                partes.append(pagina.extract_text() or "")
        return "\n".join(partes)


# --------------------------------------------------------------------------- #
# Roteamento PDF/código a partir da lista de arquivos do PR
# --------------------------------------------------------------------------- #


@dataclass
class RoteamentoPR:
    """Resultado do roteamento de um PR."""

    pdfs_pecas: list[str] = field(default_factory=list)
    arquivos_codigo: list[str] = field(default_factory=list)

    @property
    def roda_pipeline_juridico(self) -> bool:
        return bool(self.pdfs_pecas)

    @property
    def roda_pipeline_codigo(self) -> bool:
        return bool(self.arquivos_codigo)


def rotear_arquivos(arquivos_alterados: list[str]) -> RoteamentoPR:
    """Classifica os arquivos do PR em pipeline jurídico e/ou de código.

    - `pecas/*.pdf`            -> pipeline jurídico (XML + JSON de auditoria)
    - `engine/*.py` ou
      `nexum_engine/*.py`      -> pipeline de security review técnico
    Se ambos forem tocados, os dois pipelines rodam.
    """
    rot = RoteamentoPR()
    for caminho in arquivos_alterados:
        c = caminho.strip()
        if not c:
            continue
        if c.startswith(PREFIXO_PECAS) and c.lower().endswith(".pdf"):
            rot.pdfs_pecas.append(c)
        elif c.startswith(PREFIXOS_CODIGO) and c.endswith(".py"):
            rot.arquivos_codigo.append(c)
    return rot


# --------------------------------------------------------------------------- #
# Construção do XML semântico R&T (input canônico)
# --------------------------------------------------------------------------- #


def construir_xml_auditoria(peca_anonimizada: str, contexto: str = "") -> str:
    """Monta o XML semântico R&T para auditoria recursal.

    Usa tags do domínio jurídico (não genéricas), conforme o reference v1.5.0.
    """
    obj = (
        "Identificar vícios formais e omissões doutrinárias que ensejem rejeição "
        "liminar do recurso ou prejudiquem o conhecimento de mérito."
    )
    return (
        "<auditoria_recursal>\n"
        "  <objeto>" + obj + "</objeto>\n"
        "  <fatos_relevantes>" + (contexto or "Vide peça integral.") + "</fatos_relevantes>\n"
        "  <peca_integral_anonimizada>" + peca_anonimizada + "</peca_integral_anonimizada>\n"
        "</auditoria_recursal>"
    )


# Schema JSON canônico do output jurídico (resumido — vide reference v1.5.0).
SCHEMA_OUTPUT: dict[str, Any] = {
    "tipo_peca": "habeas_corpus|agravo_regimental|alegacoes_finais|"
    "razoes_apelacao|memorial|contrarrazoes|outro",
    "risco_rejeicao": "0-100",
    "vicios_formais": [],
    "preliminares_ausentes": [],
    "fundamentos_fragilizados": [],
    "jurisprudencia_omitida": [],
    "veredito_tier0": "aprovado_>=97|reprovado_<97",
    "score": "0-100",
    "recomendacoes": [],
}

# System prompt canônico — carregado do arquivo versionado (não duplicado aqui).
_CAMINHO_SYSTEM_PROMPT = (
    Path(__file__).parent / "system_prompts" / "auditor_juridico_rt.md"
)


def carregar_system_prompt() -> str:
    """Lê o system prompt canônico versionado em system_prompts/."""
    try:
        return _CAMINHO_SYSTEM_PROMPT.read_text(encoding="utf-8")
    except FileNotFoundError:
        # Fallback mínimo — em produção o arquivo sempre existe (versionado).
        return (
            "Você é o auditor recursal sênior do escritório Ribeiro & Tigre, "
            "OAB/PE. Padrão NEXUM TIER 0. Responda exclusivamente com JSON válido."
        )


# --------------------------------------------------------------------------- #
# 3. ClaudeReviewer — Anthropic Messages API (XML in / JSON out, pré-fill `{`)
# --------------------------------------------------------------------------- #


class ClaudeReviewer:
    """Auditor via Claude Opus 4.8 (Anthropic Messages API).

    Aplica o truque canônico de pré-fill `{` no turno do assistant para forçar
    JSON puro sem preâmbulo (reference v1.5.0, seção 3.3).
    """

    def __init__(
        self,
        client: Optional[Any] = None,
        modelo: str = MODELO_CLAUDE_PADRAO,
        temperature: float = 0.0,
    ) -> None:
        self._client = client  # injetável; em produção é anthropic.Anthropic
        self.modelo = modelo
        self.temperature = temperature
        self.anonimizador = LGPDAnonimizer()

    def _client_real(self) -> Any:
        if self._client is not None:
            return self._client
        from anthropic import Anthropic  # import preguiçoso

        return Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    def revisar(self, texto_peca: str, contexto: str = "") -> dict[str, Any]:
        """Audita uma peça e devolve o dict JSON conforme o schema."""
        # 1) LGPD ANTES do envio (nunca depois).
        peca_anon = self.anonimizador.anonimizar(texto_peca)
        xml_input = construir_xml_auditoria(peca_anon, self.anonimizador.anonimizar(contexto))

        user_message = (
            "Realize auditoria recursal NEXUM TIER 0 sobre a peça abaixo e "
            "retorne JSON estrito conforme o schema.\n\nSCHEMA:\n"
            + json.dumps(SCHEMA_OUTPUT, ensure_ascii=False, indent=2)
            + "\n\nCASO:\n"
            + xml_input
        )

        resp = self._client_real().messages.create(
            model=self.modelo,
            max_tokens=8000,
            temperature=self.temperature,
            system=carregar_system_prompt(),
            messages=[
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": "{"},  # pré-fill JSON canônico
            ],
        )
        raw = "{" + self._texto_resposta(resp)
        return self._parse_json(raw, provedor="claude")

    @staticmethod
    def _texto_resposta(resp: Any) -> str:
        # SDK Anthropic: resp.content[0].text
        return resp.content[0].text

    @staticmethod
    def _parse_json(raw: str, provedor: str) -> dict[str, Any]:
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"{provedor} retornou JSON inválido: {exc}\nRaw: {raw[:300]}..."
            ) from exc


# --------------------------------------------------------------------------- #
# 4. GeminiReviewer — gemini-cli em modo headless
# --------------------------------------------------------------------------- #


class GeminiReviewer:
    """Auditor via Gemini 3 Pro, executando o gemini-cli em modo headless.

    A autenticação real é por Workload Identity Federation (zero secret) — o
    gemini-cli já recebe as credenciais ADC injetadas pelo step
    `google-github-actions/auth@v2`. Aqui apenas montamos e executamos o comando.
    O `runner` é injetável para testes (sem subprocess real).
    """

    def __init__(
        self,
        runner: Optional[Callable[[list[str], str], str]] = None,
        modelo: str = MODELO_GEMINI_PADRAO,
    ) -> None:
        self._runner = runner
        self.modelo = modelo
        self.anonimizador = LGPDAnonimizer()

    def _executar(self, comando: list[str], prompt: str) -> str:
        if self._runner is not None:
            return self._runner(comando, prompt)
        # Produção: chama o gemini-cli e envia o prompt por stdin.
        proc = subprocess.run(
            comando,
            input=prompt,
            text=True,
            capture_output=True,
            timeout=600,
            check=True,
        )
        return proc.stdout

    def revisar(self, texto_peca: str, contexto: str = "") -> dict[str, Any]:
        peca_anon = self.anonimizador.anonimizar(texto_peca)
        xml_input = construir_xml_auditoria(peca_anon, self.anonimizador.anonimizar(contexto))
        prompt = (
            carregar_system_prompt()
            + "\n\nRetorne SOMENTE JSON conforme o schema:\n"
            + json.dumps(SCHEMA_OUTPUT, ensure_ascii=False)
            + "\n\nCASO:\n"
            + xml_input
        )
        comando = ["gemini", "--model", self.modelo, "--prompt", "-"]
        saida = self._executar(comando, prompt)
        return self._extrair_json(saida)

    @staticmethod
    def _extrair_json(saida: str) -> dict[str, Any]:
        """Extrai o primeiro objeto JSON da saída do CLI (tolera ruído ao redor)."""
        ini = saida.find("{")
        fim = saida.rfind("}")
        if ini == -1 or fim == -1 or fim < ini:
            raise RuntimeError(f"gemini não retornou JSON: {saida[:300]}...")
        bloco = saida[ini : fim + 1]
        try:
            return json.loads(bloco)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"gemini JSON inválido: {exc}\nBloco: {bloco[:300]}") from exc


# --------------------------------------------------------------------------- #
# 5. TIER0Consolidator — merge dos JSONs + tabela markdown + veredito
# --------------------------------------------------------------------------- #


@dataclass
class ResultadoConsolidado:
    score_consolidado: float
    aprovado: bool
    convergencias: list[str]
    divergencias_claude: list[str]
    divergencias_gemini: list[str]
    delta_risco: int
    markdown: str


class TIER0Consolidator:
    """Consolida os dois JSONs em um veredito TIER 0 com relatório markdown."""

    def __init__(self, gate_score: int = GATE_SCORE_PADRAO) -> None:
        self.gate_score = gate_score

    # ------------------------------------------------ utilidades de extração
    @staticmethod
    def _score(rev: dict[str, Any]) -> float:
        s = rev.get("score")
        return float(s) if isinstance(s, (int, float)) else 0.0

    @staticmethod
    def _risco(rev: dict[str, Any]) -> int:
        r = rev.get("risco_rejeicao")
        return int(r) if isinstance(r, (int, float)) else 0

    @staticmethod
    def _achados(rev: dict[str, Any]) -> set[str]:
        """Conjunto normalizado de achados (vícios + jurisprudência omitida)."""
        out: set[str] = set()
        for v in rev.get("vicios_formais", []) or []:
            out.add(str(v).strip().lower())
        for j in rev.get("jurisprudencia_omitida", []) or []:
            out.add(str(j).strip().lower())
        return out

    # ------------------------------------------------ consolidação
    def consolidar(
        self,
        rev_claude: dict[str, Any],
        rev_gemini: dict[str, Any],
        peso_claude: float = 0.5,
        peso_gemini: float = 0.5,
    ) -> ResultadoConsolidado:
        s_claude = self._score(rev_claude)
        s_gemini = self._score(rev_gemini)
        score = round(s_claude * peso_claude + s_gemini * peso_gemini, 2)

        a_claude = self._achados(rev_claude)
        a_gemini = self._achados(rev_gemini)
        convergencias = sorted(a_claude & a_gemini)
        excl_claude = sorted(a_claude - a_gemini)
        excl_gemini = sorted(a_gemini - a_claude)

        delta = abs(self._risco(rev_claude) - self._risco(rev_gemini))
        aprovado = score >= self.gate_score

        md = self._render_markdown(
            rev_claude, rev_gemini, score, aprovado,
            convergencias, excl_claude, excl_gemini, delta,
        )
        return ResultadoConsolidado(
            score_consolidado=score,
            aprovado=aprovado,
            convergencias=convergencias,
            divergencias_claude=excl_claude,
            divergencias_gemini=excl_gemini,
            delta_risco=delta,
            markdown=md,
        )

    # ------------------------------------------------ relatório markdown
    def _render_markdown(
        self,
        rev_claude: dict[str, Any],
        rev_gemini: dict[str, Any],
        score: float,
        aprovado: bool,
        convergencias: list[str],
        excl_claude: list[str],
        excl_gemini: list[str],
        delta: int,
    ) -> str:
        selo = (
            "🟢 **APROVADO ≥97 — TIER 0**"
            if aprovado
            else "🔴 **REPROVADO <97 — refatoração obrigatória**"
        )
        alerta_delta = (
            "\n> ⚠️ **Divergência significativa de risco (Δ>15)** — revisão humana "
            "obrigatória antes do merge.\n"
            if delta > 15
            else ""
        )
        linhas = [
            "## 🛡️ Peer-Review Consolidado — NEXUM TIER 0",
            "",
            f"**Veredito consolidado:** {selo}",
            f"**Score médio ponderado:** `{score:.2f}` / 100 "
            f"(gate = {self.gate_score})",
            alerta_delta,
            "### Comparação dimensional",
            "",
            "| Dimensão | Claude Opus 4.8 | Gemini 3 Pro |",
            "|---|---|---|",
            f"| Tipo da peça | {rev_claude.get('tipo_peca', '—')} "
            f"| {rev_gemini.get('tipo_peca', '—')} |",
            f"| Score | {self._score(rev_claude):.0f} | {self._score(rev_gemini):.0f} |",
            f"| Risco de rejeição | {self._risco(rev_claude)} "
            f"| {self._risco(rev_gemini)} (Δ={delta}) |",
            f"| Veredito | {rev_claude.get('veredito_tier0', '—')} "
            f"| {rev_gemini.get('veredito_tier0', '—')} |",
            "",
            "### Convergências (ambos apontaram)",
            "",
        ]
        linhas += (
            [f"- {c}" for c in convergencias] if convergencias else ["- _Nenhuma_"]
        )
        linhas += ["", "### Divergências exclusivas — Claude Opus 4.8", ""]
        linhas += (
            [f"- {c}" for c in excl_claude] if excl_claude else ["- _Nenhuma_"]
        )
        linhas += ["", "### Divergências exclusivas — Gemini 3 Pro", ""]
        linhas += (
            [f"- {c}" for c in excl_gemini] if excl_gemini else ["- _Nenhuma_"]
        )
        linhas += [
            "",
            "---",
            "_Ribeiro & Tigre Advocacia Criminal · NEXUM TIER 0 · "
            "peer-review dual-provider (Claude Opus 4.8 + Gemini 3 Pro)_",
        ]
        return "\n".join(linhas)


# --------------------------------------------------------------------------- #
# Renderização do selo de comentário por provedor (Job 1 / Job 2)
# --------------------------------------------------------------------------- #


def render_comentario_provedor(provedor: str, modelo: str, rev: dict[str, Any]) -> str:
    """Gera o comentário markdown de um job individual (Claude ou Gemini)."""
    score = rev.get("score", 0)
    try:
        aprovado = float(score) >= GATE_SCORE_PADRAO
    except (TypeError, ValueError):
        aprovado = False
    selo = "🟢 APROVADO ≥97" if aprovado else "🔴 REPROVADO <97"
    return (
        f"## Revisão {provedor} (`{modelo}`)\n\n"
        f"**Selo TIER 0:** {selo} — score `{score}`\n\n"
        "```json\n"
        + json.dumps(rev, ensure_ascii=False, indent=2)
        + "\n```\n"
    )


# --------------------------------------------------------------------------- #
# CLI — usado pelos steps do workflow
# --------------------------------------------------------------------------- #


def _carregar_json(caminho: str) -> dict[str, Any]:
    return json.loads(Path(caminho).read_text(encoding="utf-8"))


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Orquestrador de peer-review NEXUM TIER 0"
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_rota = sub.add_parser("rotear", help="Classifica arquivos do PR (stdin: lista)")
    p_rota.add_argument("--arquivos", nargs="*", default=None)

    p_cons = sub.add_parser("consolidar", help="Consolida dois JSONs de revisão")
    p_cons.add_argument("--claude", required=True, help="JSON do Claude")
    p_cons.add_argument("--gemini", required=True, help="JSON do Gemini")
    p_cons.add_argument("--out", required=True, help="Markdown de saída")
    p_cons.add_argument(
        "--gate", type=int, default=int(os.environ.get("TIER0_GATE_SCORE", GATE_SCORE_PADRAO))
    )

    args = parser.parse_args(argv)

    if args.cmd == "rotear":
        arquivos = args.arquivos or sys.stdin.read().splitlines()
        rot = rotear_arquivos(arquivos)
        print(
            json.dumps(
                {
                    "roda_pipeline_juridico": rot.roda_pipeline_juridico,
                    "roda_pipeline_codigo": rot.roda_pipeline_codigo,
                    "pdfs_pecas": rot.pdfs_pecas,
                    "arquivos_codigo": rot.arquivos_codigo,
                },
                ensure_ascii=False,
            )
        )
        return 0

    if args.cmd == "consolidar":
        rev_claude = _carregar_json(args.claude)
        rev_gemini = _carregar_json(args.gemini)
        cons = TIER0Consolidator(gate_score=args.gate)
        res = cons.consolidar(rev_claude, rev_gemini)
        Path(args.out).write_text(res.markdown, encoding="utf-8")
        # Falha o gate se reprovado (exit code != 0 quebra o job de consolidação).
        if not res.aprovado:
            print(f"GATE TIER 0 REPROVADO: score {res.score_consolidado} < {args.gate}")
            return 1
        print(f"GATE TIER 0 APROVADO: score {res.score_consolidado} >= {args.gate}")
        return 0

    return 2  # pragma: no cover


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
