#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dryrun_tier0.py — valida a esteira de peer-review TIER 0 LOCALMENTE, sem nenhuma
credencial de nuvem (sem ANTHROPIC_API_KEY, sem WIF).

Exercita o caminho real de ponta a ponta — filtro LGPD -> XML semantico ->
parse do JSON de cada provedor -> consolidacao -> gate >=97 — usando revisores
SIMULADOS (dubles deterministicos injetados). Serve para a banca "ver" o gate
funcionando antes de configurar os provedores no console.

Uso:
    python3 .github/scripts/dryrun_tier0.py                 # cenario aprovado
    python3 .github/scripts/dryrun_tier0.py --cenario reprovado
    python3 .github/scripts/dryrun_tier0.py --gate 97

Exit code espelha o gate real (0 = aprovado, 1 = reprovado) — igual ao CI.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Torna os modulos do peer-review importaveis quando chamado da raiz do repo.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from peer_review_orchestrator import (  # noqa: E402
    ClaudeReviewer,
    GeminiReviewer,
    TIER0Consolidator,
)

# Peca sintetica com PII proposital, para evidenciar o filtro LGPD em acao.
PECA_SINTETICA = (
    "RAZOES DE APELACAO. Apelante Joao da Silva, CPF 123.456.789-00, "
    "telefone (81) 99999-8888, e-mail joao@example.com. Subscreve OAB/PE 27.543 "
    "(socio) e OAB/PE 99.999 (terceiro). Preliminar de nulidade por cerceamento "
    "de defesa; no merito, decisao manifestamente contraria a prova dos autos."
)

CENARIOS: dict[str, dict] = {
    "aprovado": {
        "tipo_peca": "razoes_apelacao",
        "risco_rejeicao": 8,
        "vicios_formais": [],
        "preliminares_ausentes": [],
        "fundamentos_fragilizados": [],
        "jurisprudencia_omitida": [],
        "veredito_tier0": "aprovado_>=97",
        "score": 98,
        "recomendacoes": ["Peca solida; ajustes marginais de citacao."],
    },
    "reprovado": {
        "tipo_peca": "razoes_apelacao",
        "risco_rejeicao": 72,
        "vicios_formais": ["tempestividade nao demonstrada"],
        "preliminares_ausentes": ["prequestionamento"],
        "fundamentos_fragilizados": ["dosimetria sem fundamentacao"],
        "jurisprudencia_omitida": ["Sumula 443 do STJ"],
        "veredito_tier0": "reprovado_<97",
        "score": 61,
        "recomendacoes": ["Refatorar preliminares e reforcar prequestionamento."],
    },
}


def _stub_claude(payload: dict) -> ClaudeReviewer:
    """Injeta um cliente Anthropic duble que devolve o JSON do cenario."""
    corpo = json.dumps(payload, ensure_ascii=False)

    class _Msgs:
        def create(self, **_kw):
            # revisar() faz raw = "{" + text  -> devolvemos o JSON sem a 1a chave.
            texto = corpo[1:]
            return type("R", (), {"content": [type("C", (), {"text": texto})()]})()

    return ClaudeReviewer(client=type("Cli", (), {"messages": _Msgs()})())


def _stub_gemini(payload: dict) -> GeminiReviewer:
    """Injeta um runner de CLI duble que ecoa o JSON do cenario."""
    corpo = json.dumps(payload, ensure_ascii=False)
    return GeminiReviewer(runner=lambda _cmd, _prompt: f"```json\n{corpo}\n```")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Dry-run local da esteira TIER 0.")
    ap.add_argument("--cenario", choices=sorted(CENARIOS), default="aprovado")
    ap.add_argument("--gate", type=int, default=97)
    args = ap.parse_args(argv)

    payload = CENARIOS[args.cenario]
    print(f">> Cenario: {args.cenario} | gate: {args.gate} | (offline, sem credenciais)\n")

    claude = _stub_claude(payload)
    gemini = _stub_gemini(payload)

    # Caminho real: LGPD + XML + parse do JSON de cada provedor.
    rev_claude = claude.revisar(PECA_SINTETICA)
    rev_gemini = gemini.revisar(PECA_SINTETICA)

    # Evidencia do filtro LGPD (a peca enviada ao provedor e anonimizada).
    anon = claude.anonimizador.anonimizar(PECA_SINTETICA)
    print("-- LGPD (amostra do que e enviado ao provedor) --")
    print("   " + anon[:180] + " ...\n")

    cons = TIER0Consolidator(gate_score=args.gate).consolidar(rev_claude, rev_gemini)
    print(cons.markdown)
    print(f"\n>> Gate: {'APROVADO' if cons.aprovado else 'REPROVADO'} "
          f"(score {cons.score_consolidado} / {args.gate}) | exit={0 if cons.aprovado else 1}")
    return 0 if cons.aprovado else 1


if __name__ == "__main__":
    raise SystemExit(main())
