"""Gate de citações — acoplagem do loop de verdade à esteira de peer-review.

CLI que audita arquivos de peça/minuta contra a base MINDJUS verificada e
aplica a postura binária de governança:

- saída 0: todas as citações de todos os arquivos estão na base verificada
  (ou não há citações) — PROTOCOLAVEL;
- saída 1: qualquer citação fora da base — NAO_PROTOCOLAVEL, derruba o
  pipeline e impede o merge;
- saída 2: erro operacional (base ausente/ilegível) em modo estrito.

Contingência local-first: a fonte é a ``FonteJsonVerificada`` (nenhuma
credencial). Com ``--inconclusivo-sem-base``, a ausência da base sela
⚪ INCONCLUSIVO e sai 0 — o mesmo desenho do gate dual-provider (#27):
não reprovar o que não pôde ser auditado. Após o HITL do Supabase, a
troca por ``FonteSupabase`` é um ponto único neste módulo.

Uso:
    python -m nexum_engine.verdade.gate --base <dir_mindjus> arquivo.md [...]
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from .auditor import auditar_citacoes
from .fontes import FonteJsonVerificada

EXTENSOES_AUDITAVEIS = {".md", ".txt", ".html"}

SELO_APROVADO = "✅ [GATE APROVADO]"
SELO_BLOQUEADO = "❌ [GATE BLOQUEADO]"
SELO_INCONCLUSIVO = "⚪ [GATE INCONCLUSIVO]"


def _auditar_arquivos(
    fonte: FonteJsonVerificada, arquivos: list[Path]
) -> tuple[bool, list[str]]:
    """Audita cada arquivo; devolve (tudo_protocolavel, linhas_do_relatorio)."""
    linhas: list[str] = []
    tudo_ok = True
    for arquivo in arquivos:
        if arquivo.suffix.lower() not in EXTENSOES_AUDITAVEIS:
            linhas.append(f"  ~ {arquivo}: extensão fora do escopo do gate "
                          f"(auditável: {sorted(EXTENSOES_AUDITAVEIS)}) — pulado")
            continue
        texto = arquivo.read_text(encoding="utf-8", errors="ignore")
        relatorio = asyncio.run(auditar_citacoes(texto, fonte))
        if relatorio.protocolavel:
            linhas.append(
                f"  ✓ {arquivo}: {relatorio.veredito} "
                f"({len(relatorio.citacoes)} citações verificadas)"
            )
        else:
            tudo_ok = False
            linhas.append(f"  ✗ {arquivo}: {relatorio.veredito}")
            for c in relatorio.nao_verificadas:
                linhas.append(
                    f"      ⚠️  citação fora da base verificada: {c.citacao!r} "
                    f"(normalizada: {c.normalizada})"
                )
    return tudo_ok, linhas


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("arquivos", nargs="+", help="peças/minutas a auditar")
    parser.add_argument(
        "--base", required=True,
        help="diretório da base MINDJUS verificada (mindjus_data/)",
    )
    parser.add_argument(
        "--inconclusivo-sem-base", action="store_true",
        help="base ausente => selar INCONCLUSIVO e sair 0 (padrão: erro, sair 2)",
    )
    args = parser.parse_args(argv)

    try:
        fonte = FonteJsonVerificada(args.base)
    except FileNotFoundError as exc:
        if args.inconclusivo_sem_base:
            print(f"{SELO_INCONCLUSIVO} base verificada indisponível ({exc}). "
                  "As peças NÃO foram reprovadas — apenas não puderam ser "
                  "auditadas. Configure o acesso à base (WARROOM_TIGRE_TOKEN).")
            return 0
        print(f"[ERRO] {exc}", file=sys.stderr)
        return 2

    existentes = []
    for nome in args.arquivos:
        caminho = Path(nome)
        if not caminho.is_file():
            print(f"[ERRO] arquivo não localizado: {caminho}", file=sys.stderr)
            return 2
        existentes.append(caminho)

    print(f"[NEXUM GATE] base verificada: {fonte.total_citaveis} precedentes "
          f"citáveis; auditando {len(existentes)} arquivo(s)...")
    tudo_ok, linhas = _auditar_arquivos(fonte, existentes)
    print("\n".join(linhas))

    if not tudo_ok:
        print(f"\n{SELO_BLOQUEADO} citação fora da base verificada — "
              "NAO_PROTOCOLAVEL (zero_tolerance). Verifique em fonte oficial "
              "e promova o precedente à base antes de reapresentar.")
        return 1
    print(f"\n{SELO_APROVADO} todas as citações verificadas contra o acervo "
          "auditado do MINDJUS.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
