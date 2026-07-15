"""Exemplo mínimo de uso do pipeline Deep Hunter × Supreme Drafter.

Requer ANTHROPIC_API_KEY no ambiente e um PDF real dos autos.

    python examples/exemplo_uso.py caminho/para/autos.pdf
"""

from __future__ import annotations

import sys

from deep_hunter import Comando, Modo, ModoRedacional, Pipeline


def main() -> int:
    if len(sys.argv) < 2:
        print("uso: python examples/exemplo_uso.py <autos.pdf>", file=sys.stderr)
        return 2

    pipeline = Pipeline()
    resultado = pipeline.run(
        sys.argv[1],
        modo=Modo.SIMBIOSE,
        comandos=[Comando.HASH_AUDIT, Comando.WRITE_BLOCKER],
        modo_redacional=ModoRedacional.CUSTODIA,
    )

    dossie = resultado.dossie
    quebras = sum(1 for m in dossie.auditoria_custodia if m.possui_quebra_custodia)
    print(f"NPU:               {dossie.npu}")
    print(f"Atos mapeados:     {len(dossie.linha_tempo_atos)}")
    print(f"Quebras custódia:  {quebras}")
    print("=" * 60)
    print(resultado.peca_markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
