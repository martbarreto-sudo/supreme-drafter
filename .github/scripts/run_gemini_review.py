#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Entrypoint de produção do Job 2 (Gemini 3 Pro via gemini-cli + WIF).

Mesma lógica de roteamento do Job 1, mas auditando via GeminiReviewer.
A autenticação ADC já foi injetada pelo google-github-actions/auth@v2 (WIF).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from peer_review_orchestrator import GeminiReviewer, PecaExtractor


def _nao_aplicavel(motivo: str) -> dict:
    # Sem peça: o gate não se aplica → passa (score alto, não reprova).
    return {
        "tipo_peca": "nao_aplicavel",
        "disponivel": True,
        "risco_rejeicao": 0,
        "vicios_formais": [],
        "preliminares_ausentes": [],
        "fundamentos_fragilizados": [],
        "jurisprudencia_omitida": [],
        "veredito_tier0": "nao_aplicavel",
        "score": 100,
        "recomendacoes": [motivo],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rota", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--pr", default="")
    args = ap.parse_args()

    rota = json.loads(Path(args.rota).read_text(encoding="utf-8"))

    if not rota.get("roda_pipeline_juridico"):
        resultado = _nao_aplicavel("PR sem pecas/*.pdf — pipeline jurídico não aplicável.")
        Path(args.out).write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
        return 0

    extractor = PecaExtractor()
    textos = []
    for pdf in rota.get("pdfs_pecas", []):
        try:
            textos.append(extractor.extrair_texto(pdf))
        except Exception as exc:  # noqa: BLE001
            textos.append(f"[falha ao extrair {pdf}: {exc}]")

    reviewer = GeminiReviewer()
    resultado = reviewer.revisar("\n\n".join(textos))
    Path(args.out).write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
