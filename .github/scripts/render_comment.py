#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Renderiza o comentário markdown de um provedor (Job 1/Job 2) a partir do JSON."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from peer_review_orchestrator import render_comentario_provedor


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--provedor", required=True)
    ap.add_argument("--modelo", required=True)
    ap.add_argument("--json", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    rev = json.loads(Path(args.json).read_text(encoding="utf-8"))
    md = render_comentario_provedor(args.provedor, args.modelo, rev)
    Path(args.out).write_text(md, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
