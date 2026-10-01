#!/usr/bin/env python3
"""Sincroniza as cópias da especificação a partir de public/openapi.json.

Havia três cópias da spec no repositório e nenhuma dizia qual mandava. Foi essa
duplicação silenciosa que permitiu um agente ler o contrato-alvo como runtime em
produção. Agora existe uma fonte canônica e duas derivadas:

    public/openapi.json                     ← CANÔNICA (editar aqui)
    public/api.html (#openapi-spec)         ← fallback da página (gerado)
    services/runtime/docs/api-spec.json     ← cópia do runtime (gerada)

    python3 tools/sync-spec.py            # regrava as derivadas
    python3 tools/sync-spec.py --check    # falha se alguma divergiu
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CANONICA = RAIZ / "public" / "openapi.json"
PAGINA = RAIZ / "public" / "api.html"
COPIA_RUNTIME = RAIZ / "services" / "runtime" / "docs" / "api-spec.json"

_BLOCO_EMBUTIDO = re.compile(
    r'(<script type="application/json" id="openapi-spec">)(.*?)(</script>)', re.S
)


def _canonica() -> dict:
    return json.loads(CANONICA.read_text(encoding="utf-8"))


def _derivada_runtime(spec: dict) -> str:
    copia = json.loads(json.dumps(spec))
    copia["info"]["x-nexum-canonical-source"] = "public/openapi.json"
    copia["info"]["x-nexum-copy-note"] = (
        "Cópia gerada por tools/sync-spec.py. Não edite: altere a canônica e rode o script."
    )
    return json.dumps(copia, ensure_ascii=False, indent=2) + "\n"


def _pagina_com_fallback(spec: dict) -> str:
    html = PAGINA.read_text(encoding="utf-8")
    novo = json.dumps(spec, ensure_ascii=False, indent=2)
    if not _BLOCO_EMBUTIDO.search(html):
        raise SystemExit("public/api.html: bloco #openapi-spec não encontrado.")
    return _BLOCO_EMBUTIDO.sub(lambda m: m.group(1) + novo + m.group(3), html, count=1)


def main() -> int:
    spec = _canonica()
    alvos = [
        (COPIA_RUNTIME, _derivada_runtime(spec)),
        (PAGINA, _pagina_com_fallback(spec)),
    ]

    if "--check" in sys.argv:
        divergentes = [
            str(caminho.relative_to(RAIZ))
            for caminho, esperado in alvos
            if caminho.read_text(encoding="utf-8") != esperado
        ]
        if divergentes:
            print(
                "Cópias da spec divergiram da canônica: "
                + ", ".join(divergentes)
                + "\nRode: python3 tools/sync-spec.py"
            )
            return 1
        print(f"Spec sincronizada ({len(spec.get('paths', {}))} paths em {len(alvos)} cópias).")
        return 0

    for caminho, conteudo in alvos:
        caminho.write_text(conteudo, encoding="utf-8")
        print(f"sincronizado: {caminho.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
