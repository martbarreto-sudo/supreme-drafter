"""Interface de linha de comando: `python -m deep_hunter <subcomando>`."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from core.draft_engine import ModoRedacional
from schema.dossier_hunter import DossierHunterSchema

from .config import Comando, Modo
from .pipeline import Pipeline


def _write_outputs(out_dir: Path, dossie: DossierHunterSchema | None, peca: str | None) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    if dossie is not None:
        (out_dir / "dossie.json").write_text(
            dossie.model_dump_json(indent=2), encoding="utf-8"
        )
        print(f"[+] Dossiê gravado em {out_dir / 'dossie.json'}", file=sys.stderr)
    if peca is not None:
        (out_dir / "peca.md").write_text(peca, encoding="utf-8")
        print(f"[+] Peça gravada em {out_dir / 'peca.md'}", file=sys.stderr)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="deep_hunter",
        description="Deep Hunter (auditor forense) × Supreme Drafter (redator).",
    )
    p.add_argument("--out", default="out", help="Diretório de saída (padrão: out/).")
    sub = p.add_subparsers(dest="cmd", required=True)

    modos = [m.value for m in Modo]
    comandos = [c.value for c in Comando]
    modos_red = [m.value for m in ModoRedacional]

    a = sub.add_parser("audit", help="Apenas auditoria (Agente 01).")
    a.add_argument("pdf", help="Caminho dos autos em PDF.")
    a.add_argument("--modo", choices=modos, default=Modo.SIMBIOSE.value)
    a.add_argument("--comando", action="append", choices=comandos, default=[],
                   help="Comando de auditoria (repetível).")

    d = sub.add_parser("draft", help="Apenas redação (Agente 02) a partir de um dossiê JSON.")
    d.add_argument("dossie", help="Caminho do dossiê JSON auditado.")
    d.add_argument("--modo-redacional", choices=modos_red, default=ModoRedacional.PERTINAZ.value)

    r = sub.add_parser("run", help="Auditoria + redação, ponta a ponta.")
    r.add_argument("pdf", help="Caminho dos autos em PDF.")
    r.add_argument("--modo", choices=modos, default=Modo.SIMBIOSE.value)
    r.add_argument("--comando", action="append", choices=comandos, default=[])
    r.add_argument("--modo-redacional", choices=modos_red, default=ModoRedacional.PERTINAZ.value)

    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    out_dir = Path(args.out)
    pipeline = Pipeline()

    if args.cmd == "audit":
        dossie = pipeline.audit(args.pdf, modo=args.modo, comandos=args.comando)
        _write_outputs(out_dir, dossie, None)
        print(dossie.model_dump_json(indent=2))
        return 0

    if args.cmd == "draft":
        dossie = DossierHunterSchema.model_validate_json(
            Path(args.dossie).read_text(encoding="utf-8")
        )
        peca = pipeline.draft(dossie, modo=args.modo_redacional)
        _write_outputs(out_dir, None, peca)
        print(peca)
        return 0

    if args.cmd == "run":
        resultado = pipeline.run(
            args.pdf,
            modo=args.modo,
            comandos=args.comando,
            modo_redacional=args.modo_redacional,
        )
        _write_outputs(out_dir, resultado.dossie, resultado.peca_markdown)
        print(resultado.peca_markdown)
        return 0

    return 1  # pragma: no cover


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
