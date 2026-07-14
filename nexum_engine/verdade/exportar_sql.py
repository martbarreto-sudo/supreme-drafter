"""Carga MINDJUS → SQL: gera o manifesto de INSERTs para o Supabase.

Transforma a base verificada em disco (``mindjus_data/*.json``) num único
arquivo SQL transacional para ``precedentes_verificados`` (DDL em
``nexum_engine/schema/precedentes.sql``). Regras:

- **Nada é descartado**: registros citáveis entram como estão; registros em
  quarentena entram quarentenados; registros SEM fonte de verificação são
  exportados JÁ EM QUARENTENA (``verificacao_pendente = TRUE`` + motivo
  automático) — antecipando os CHECKs do banco em vez de quebrar neles.
- **Deduplicação por numero_normalizado** (coluna UNIQUE): o representante
  é o primeiro registro citável na ordem dos arquivos (ou o primeiro, se
  nenhum for citável); as tags são a união de todas as ocorrências.
- Saída determinística (ordenada) e idempotente (ON CONFLICT DO NOTHING).

A base atual tem ~25 registros — um único arquivo basta; não há necessidade
de fragmentar em batches. Executar como OWNER/service role no SQL Editor do
Supabase: a RLS da tabela nega escrita aos papéis da engine de propósito.

Uso:
    python -m nexum_engine.verdade.exportar_sql <dir_mindjus> [-o saida.sql]
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from pathlib import Path

from .precedente import Precedente

MOTIVO_SEM_FONTE = (
    "carga MINDJUS: fonte_verificacao ausente no registro de origem — "
    "revalidar em fonte oficial antes de promover"
)


def _carregar_todos(diretorio: Path) -> list[Precedente]:
    """Todos os registros da base, com herança da fonte no nível do arquivo."""
    todos: list[Precedente] = []
    for caminho in sorted(diretorio.glob("*.json")):
        dados = json.loads(caminho.read_text(encoding="utf-8"))
        tema = str(dados.get("tema") or dados.get("termo_busca") or "").strip()
        fonte_do_arquivo = str(dados.get("fonte_verificacao", "")).strip()
        for registro in dados.get("precedentes", []):
            if fonte_do_arquivo and not registro.get("fonte_verificacao"):
                registro = {**registro, "fonte_verificacao": fonte_do_arquivo}
            todos.append(Precedente.de_dict(registro, tema=tema))
    return todos


def _quarentenar_orfao(p: Precedente) -> Precedente:
    """Sem fonte e sem quarentena declarada → entra quarentenado."""
    if p.citavel or p.verificacao_pendente:
        return p
    return dataclasses.replace(
        p,
        verificacao_pendente=True,
        motivo_quarentena=p.motivo_quarentena or MOTIVO_SEM_FONTE,
    )


def _deduplicar(todos: list[Precedente]) -> list[Precedente]:
    grupos: dict[str, list[Precedente]] = {}
    for p in todos:
        if not p.numero:
            continue
        grupos.setdefault(p.numero_normalizado, []).append(p)

    resultado: list[Precedente] = []
    for chave in sorted(grupos):
        ocorrencias = grupos[chave]
        representante = next((p for p in ocorrencias if p.citavel), ocorrencias[0])
        tags = tuple(sorted({t for p in ocorrencias for t in p.tags}))
        resultado.append(dataclasses.replace(representante, tags=tags))
    return resultado


def _sql_texto(valor: str) -> str:
    return "'" + valor.replace("'", "''") + "'"


def _sql_tags(tags: tuple[str, ...]) -> str:
    if not tags:
        return "'{}'::text[]"
    return "ARRAY[" + ", ".join(_sql_texto(t) for t in tags) + "]::text[]"


def _insert(p: Precedente) -> str:
    colunas = (
        "numero, numero_normalizado, tese, tribunal, relator, data_julgamento, "
        "ementa, resultado, tags, relevancia, fonte_verificacao, tema, "
        "verificacao_pendente, motivo_quarentena"
    )
    valores = ", ".join([
        _sql_texto(p.numero),
        _sql_texto(p.numero_normalizado),
        _sql_texto(p.tese),
        _sql_texto(p.tribunal),
        _sql_texto(p.relator),
        _sql_texto(p.data_julgamento),
        _sql_texto(p.ementa),
        _sql_texto(p.resultado),
        _sql_tags(p.tags),
        _sql_texto(p.relevancia),
        _sql_texto(p.fonte_verificacao),
        _sql_texto(p.tema),
        "TRUE" if p.verificacao_pendente else "FALSE",
        _sql_texto(p.motivo_quarentena),
    ])
    return (
        f"INSERT INTO precedentes_verificados ({colunas})\n"
        f"VALUES ({valores})\n"
        f"ON CONFLICT (numero_normalizado) DO NOTHING;"
    )


def gerar_sql(diretorio: str | Path) -> str:
    """Gera o manifesto SQL completo a partir do diretório da base."""
    caminho = Path(diretorio)
    if not caminho.is_dir():
        raise FileNotFoundError(f"diretório da base não existe: {caminho}")

    unicos = _deduplicar([_quarentenar_orfao(p) for p in _carregar_todos(caminho)])
    citaveis = sum(1 for p in unicos if p.citavel)
    quarentenados = len(unicos) - citaveis

    linhas = [
        "-- Manifesto de carga MINDJUS → precedentes_verificados",
        "-- Gerado por nexum_engine.verdade.exportar_sql (determinístico).",
        f"-- {len(unicos)} precedentes únicos: {citaveis} citáveis, "
        f"{quarentenados} em quarentena (fabricados + sem fonte registrada).",
        "-- Executar como OWNER/service role (a RLS nega escrita à engine).",
        "-- Idempotente: reexecutar não duplica (ON CONFLICT DO NOTHING).",
        "",
        "BEGIN;",
        "",
    ]
    linhas.extend(_insert(p) + "\n" for p in unicos)
    linhas.append("COMMIT;")
    return "\n".join(linhas) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("diretorio", help="diretório mindjus_data/ de origem")
    parser.add_argument("-o", "--output", help="arquivo .sql de saída (padrão: stdout)")
    args = parser.parse_args(argv)

    sql = gerar_sql(args.diretorio)
    if args.output:
        Path(args.output).write_text(sql, encoding="utf-8")
        print(f"Manifesto salvo em {args.output}")
    else:
        print(sql, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
