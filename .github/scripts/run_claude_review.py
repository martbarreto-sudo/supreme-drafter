#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Entrypoint de produção do Job 1 (Claude Opus 4.8).

Lê o roteamento do PR (rota.json), extrai o(s) PDF(s) de peças, audita via
Claude Opus 4.8 e grava o JSON de resultado. Usado pelo workflow peer-review.yml.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from peer_review_orchestrator import ClaudeReviewer, PecaExtractor


def _peca_neutra(motivo: str) -> dict:
    return {
        "tipo_peca": "outro",
        "risco_rejeicao": 0,
        "vicios_formais": [],
        "preliminares_ausentes": [],
        "fundamentos_fragilizados": [],
        "jurisprudencia_omitida": [],
        "veredito_tier0": "reprovado_<97",
        "score": 0,
        "recomendacoes": [motivo],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rota", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--pr", default="")
    args = ap.parse_args()

    rota = json.loads(Path(args.rota).read_text(encoding="utf-8"))

    # Sem PDF de peça neste PR: pipeline jurídico pulado (resultado neutro).
    if not rota.get("roda_pipeline_juridico"):
        resultado = _peca_neutra("PR sem pecas/*.pdf — pipeline jurídico não aplicável.")
        Path(args.out).write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
        return 0

    extractor = PecaExtractor()
    textos = []
    for pdf in rota.get("pdfs_pecas", []):
        try:
            textos.append(extractor.extrair_texto(pdf))
        except Exception as exc:  # noqa: BLE001 — robustez de CI
            textos.append(f"[falha ao extrair {pdf}: {exc}]")

    reviewer = ClaudeReviewer()
    resultado = reviewer.revisar("\n\n".join(textos))
    Path(args.out).write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
