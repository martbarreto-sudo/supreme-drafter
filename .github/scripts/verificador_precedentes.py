#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verificador determinístico de precedentes — Ponte NEXUM (lado supreme-drafter).

Ribeiro & Tigre Advocacia Criminal · Recife/PE · OAB/PE 27.543

Fecha o furo P1 do PARECER_CONSELHO_2026-06-19 (repo warroom-tigre): o
peer-review LLM (Claude/Gemini) julgava peças SEM consultar a base de
jurisprudência verificada — uma citação FABRICADA podia passar pelo gate
TIER 0 se os dois modelos não a flagrassem.

Este verificador roda ANTES/além dos LLMs, é 100% local e determinístico
(nenhum dado sai do runner — LGPD ok) e classifica cada citação da peça contra
o manifesto exportado pelo warroom-tigre:

  🔴 fabricada conhecida  → REPROVAÇÃO AUTOMÁTICA do gate (consolidação)
  🟢 verificada           → consta da base MINDJUS com fonte oficial registrada
  🟡 na base sem fonte    → consta da base curada; fonte oficial a confirmar
  ⚪ fora da base          → não coberta pela base (conferência humana)

FONTE CANÔNICA: a normalização/extração espelha `ponte_nexum.py` do repo
`martbarreto-sudo/warroom-tigre` — se mudar lá, replicar aqui. A fixture
`tests/fixtures/peca_ponte_nexum.txt` é idêntica nos dois repos e os testes
dos dois lados exigem a MESMA classificação (teste cross-repo da ponte).

O manifesto vendorizado vive em `nexum_bridge/manifesto_citacoes.json`.
Para atualizá-lo: no warroom-tigre, `python ponte_nexum.py gerar` e copie
`manifesto_citacoes.json` para cá.

CLI (usado pelo peer-review.yml, Job 1):
    python verificador_precedentes.py --rota rota.json --out verificacao.json
    python verificador_precedentes.py --texto-arquivo peca.txt --out verificacao.json

Sempre sai com exit 0 — quem aplica o gate é a consolidação
(`peer_review_orchestrator.py consolidar --verificacao ...`).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from pathlib import Path
from typing import List, Optional

MANIFESTO_VENDORIZADO = Path(__file__).parent / "nexum_bridge" / "manifesto_citacoes.json"

# Blocklist de citações FABRICADAS (depuração MINDJUS, revisão 19/06/2026).
# Espelha ponte_nexum.DIGITOS_FABRICADOS — nunca depende do manifesto estar são.
DIGITOS_FABRICADOS: frozenset[str] = frozenset({"612234", "587456", "1055941"})

# ---------------------------------------------------------------------------
# Normalização/extração — espelho de ponte_nexum.py (warroom-tigre)
# ---------------------------------------------------------------------------

_CLASSES = ("AREsp", "EREsp", "REsp", "ARE", "RE", "RHC", "HC",
            "ADPF", "ADC", "ADI", "Rcl")
_NUM = r"\d{1,3}(?:\.\d{3})+|\d{2,}"

_RE_DOCKET = re.compile(
    r"\b(?:(?:AgRg|AgInt|EDcl|EREsp|RvCr)\s+(?:no|na|em|nos)\s+)?"
    r"(" + "|".join(_CLASSES) + r")"
    r"\s*(?:n[.ºo°]{0,2}\s*)?"
    r"((?:" + _NUM + r")(?:\s*(?:,|e)\s*(?:" + _NUM + r"))*)"
    r"(?:\s*/\s*([A-Z]{2}))?"
)
_RE_SUMULA = re.compile(
    r"S[úu]mula\s+(Vinculante\s+)?(?:n[.ºo°]{0,2}\s*)?(\d+)"
    r"(?:\s*(?:/|do|da)\s*(STF|STJ))?",
    re.IGNORECASE,
)
_RE_TEMA = re.compile(r"\bTema\s+(?:n[.ºo°]{0,2}\s*)?(\d+)", re.IGNORECASE)
_RE_SO_NUM = re.compile(r"^(?:" + _NUM + r")$")


def _digitos(numero: str) -> str:
    return re.sub(r"\D", "", numero)


def normalizar_citacoes(texto: str) -> List[str]:
    """Extrai chaves canônicas ("HC 598051", "SUMULA 444", "SV 11", "TEMA 280").

    Ordem: dockets na ordem de aparição, depois súmulas, depois temas
    (dedup preserva a 1ª ocorrência). Idêntico a ponte_nexum.normalizar_citacoes.
    """
    texto = unicodedata.normalize("NFC", texto or "")
    chaves: List[str] = []

    for m in _RE_DOCKET.finditer(texto):
        classe, blob = m.group(1), m.group(2)
        for pedaco in re.split(r"\s*(?:,|\be\b)\s*", blob):
            pedaco = pedaco.strip()
            if pedaco and _RE_SO_NUM.match(pedaco):
                chaves.append(f"{classe.upper()} {_digitos(pedaco)}")

    for m in _RE_SUMULA.finditer(texto):
        vinculante, num = m.group(1), m.group(2)
        chaves.append(f"SV {num}" if vinculante else f"SUMULA {num}")

    for m in _RE_TEMA.finditer(texto):
        chaves.append(f"TEMA {m.group(1)}")

    vistos: set[str] = set()
    return [c for c in chaves if not (c in vistos or vistos.add(c))]


def citacao_fabricada(chave: str) -> bool:
    return _digitos(chave) in DIGITOS_FABRICADOS


# ---------------------------------------------------------------------------
# Manifesto vendorizado
# ---------------------------------------------------------------------------


def carregar_manifesto(caminho: Path = MANIFESTO_VENDORIZADO) -> dict:
    return json.loads(Path(caminho).read_text(encoding="utf-8"))


def manifesto_integro(manifesto: dict) -> bool:
    """Confere o selo sha256 embutido pelo gerador (ponte_nexum.py)."""
    corpo = {k: v for k, v in manifesto.items() if k != "sha256"}
    esperado = hashlib.sha256(
        json.dumps(corpo, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    return esperado == manifesto.get("sha256")


# ---------------------------------------------------------------------------
# Classificação + relatório
# ---------------------------------------------------------------------------


def classificar_texto(texto: str, manifesto: dict) -> dict:
    """Espelho de ponte_nexum.classificar_texto — mesmos 4 baldes."""
    fabricadas: List[str] = []
    verificadas: List[str] = []
    sem_fonte: List[str] = []
    fora: List[str] = []

    for chave in normalizar_citacoes(texto):
        if citacao_fabricada(chave):
            fabricadas.append(chave)
        elif chave in manifesto.get("verificadas", {}):
            verificadas.append(chave)
        elif chave in manifesto.get("na_base_sem_fonte", {}):
            sem_fonte.append(chave)
        else:
            fora.append(chave)

    return {
        "fabricadas": fabricadas,
        "verificadas": verificadas,
        "na_base_sem_fonte": sem_fonte,
        "fora_da_base": fora,
        "total_citacoes": len(fabricadas) + len(verificadas) + len(sem_fonte) + len(fora),
    }


def render_secao_markdown(resultado: dict) -> str:
    """Seção do relatório consolidado com o veredito determinístico da ponte."""
    if not resultado.get("aplicavel", True):
        return ""

    linhas = [
        "### 🔗 Ponte NEXUM — verificação determinística de precedentes",
        "",
        "_Citações da peça conferidas localmente contra a base MINDJUS "
        "verificada (warroom-tigre); nenhum dado sai do runner._",
        "",
    ]
    fab = resultado.get("fabricadas", [])
    if fab:
        linhas += [
            "> 🔴 **CITAÇÃO FABRICADA DETECTADA — REPROVAÇÃO AUTOMÁTICA DO GATE.**",
            "> Estes números constam da blocklist da depuração MINDJUS e "
            "não correspondem a julgados reais:",
            "",
        ]
        linhas += [f"> - `{c}`" for c in fab]
        linhas += [""]

    def _lista(titulo: str, chaves: List[str]) -> List[str]:
        corpo = [f"- `{c}`" for c in chaves] if chaves else ["- _Nenhuma_"]
        return [titulo, ""] + corpo + [""]

    linhas += _lista("**🟢 Verificadas em fonte oficial:**", resultado.get("verificadas", []))
    linhas += _lista(
        "**🟡 Na base MINDJUS, fonte oficial não registrada (confirmar):**",
        resultado.get("na_base_sem_fonte", []),
    )
    linhas += _lista(
        "**⚪ Fora da base — conferência humana obrigatória:**",
        resultado.get("fora_da_base", []),
    )
    return "\n".join(linhas)


# ---------------------------------------------------------------------------
# CLI — Job 1 do peer-review.yml
# ---------------------------------------------------------------------------


def _resultado_nao_aplicavel(motivo: str) -> dict:
    return {"aplicavel": False, "motivo": motivo, "fabricadas": [],
            "verificadas": [], "na_base_sem_fonte": [], "fora_da_base": [],
            "total_citacoes": 0}


def executar(rota: Optional[dict], texto: Optional[str]) -> dict:
    """Monta o resultado da verificação para a peça do PR (ou texto direto)."""
    if texto is None:
        if not rota or not rota.get("roda_pipeline_juridico"):
            return _resultado_nao_aplicavel("PR sem pecas/*.pdf — ponte não se aplica.")
        from peer_review_orchestrator import PecaExtractor  # import local (CI)

        extractor = PecaExtractor()
        partes: List[str] = []
        for pdf in rota.get("pdfs_pecas", []):
            try:
                partes.append(extractor.extrair_texto(pdf))
            except Exception as exc:  # noqa: BLE001 — robustez de CI
                partes.append(f"[falha ao extrair {pdf}: {exc}]")
        texto = "\n\n".join(partes)

    manifesto = carregar_manifesto()
    resultado = classificar_texto(texto, manifesto)
    resultado["aplicavel"] = True
    resultado["manifesto_integro"] = manifesto_integro(manifesto)
    resultado["manifesto_origem"] = manifesto.get("origem", "")
    return resultado


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Ponte NEXUM — verificação de precedentes")
    fonte = ap.add_mutually_exclusive_group(required=True)
    fonte.add_argument("--rota", help="rota.json do orquestrador (modo CI)")
    fonte.add_argument("--texto-arquivo", help="arquivo texto da peça (modo manual)")
    ap.add_argument("--out", required=True, help="JSON de saída")
    args = ap.parse_args(argv)

    if args.rota:
        rota = json.loads(Path(args.rota).read_text(encoding="utf-8"))
        resultado = executar(rota, None)
    else:
        resultado = executar(None, Path(args.texto_arquivo).read_text(encoding="utf-8"))

    Path(args.out).write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    if resultado.get("fabricadas"):
        print(f"PONTE NEXUM: citação FABRICADA detectada: {resultado['fabricadas']} "
              "(gate reprova na consolidação).")
    else:
        print(f"PONTE NEXUM: {resultado.get('total_citacoes', 0)} citação(ões) "
              "classificada(s); nenhuma fabricada.")
    return 0  # o gate é aplicado na consolidação, nunca aqui


if __name__ == "__main__":
    raise SystemExit(main())
