"""Exemplo mínimo de uso do pipeline Deep Hunter × Supreme Drafter.

Requer ANTHROPIC_API_KEY no ambiente e um PDF real dos autos.

    python examples/exemplo_uso.py caminho/para/autos.pdf
"""

from __future__ import annotations

import sys

from deep_hunter import Comando, Modo, Peca, Pipeline


def main() -> int:
    if len(sys.argv) < 2:
        print("uso: python examples/exemplo_uso.py <autos.pdf>", file=sys.stderr)
        return 2

    pipeline = Pipeline()
    resultado = pipeline.run(
        sys.argv[1],
        modo=Modo.SIMBIOSE,
        comandos=[Comando.HASH_AUDIT, Comando.WRITE_BLOCKER],
        peca=Peca.HABEAS_CORPUS,
    )

    print(f"Vulnerabilidades: {len(resultado.dossie['dossie_vulnerabilidades'])}")
    print(f"Nulidades:        {len(resultado.dossie['tabela_nulidades'])}")
    print("=" * 60)
    print(resultado.peca_markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
