"""Trava de regressão de model strings — barreira do CI.

Varre os arquivos versionados do repositório em busca de model IDs
aposentados (ex.: o antigo Sonnet 3.5 datado). As strings proibidas são
montadas por concatenação para que esta própria suíte não dispare a trava.
"""

import subprocess
from pathlib import Path

from nexum_engine import models

RAIZ = Path(__file__).resolve().parents[2]

# Extensões de texto que valem auditoria (código, config, docs).
EXTENSOES = {".py", ".yml", ".yaml", ".json", ".md", ".toml", ".sh", ".js", ".ts", ".html"}


def _arquivos_versionados():
    saida = subprocess.run(
        ["git", "ls-files"], cwd=RAIZ, capture_output=True, text=True, check=True
    ).stdout
    for nome in saida.splitlines():
        caminho = RAIZ / nome
        if caminho.suffix in EXTENSOES and caminho.is_file():
            yield caminho


class TestModelStringRegression:
    def test_nenhum_model_id_aposentado_no_repositorio(self):
        ocorrencias = []
        for caminho in _arquivos_versionados():
            try:
                conteudo = caminho.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for proibido in models.MODELOS_PROIBIDOS:
                if proibido in conteudo:
                    ocorrencias.append(f"{caminho.relative_to(RAIZ)}: {proibido}")
        assert not ocorrencias, (
            "model IDs aposentados encontrados (substitua pelo cânone em "
            f"nexum_engine/models.py): {ocorrencias}"
        )

    def test_canone_exige_a_nomenclatura_nova(self):
        assert "claude-sonnet-4-6" in models.MODELOS_PERMITIDOS
        assert "claude-opus-4-8" in models.MODELOS_PERMITIDOS
        # Nenhum permitido pode estar simultaneamente proibido.
        assert not models.MODELOS_PERMITIDOS & models.MODELOS_PROIBIDOS

    def test_defaults_dos_adaptadores_passam_pela_validacao(self):
        from nexum_engine.adapters import AnthropicVertexAdapter, DirectAPIAdapter

        assert DirectAPIAdapter().modelo == models.MODELO_AGENTE_PARALELO
        assert AnthropicVertexAdapter().modelo == models.MODELO_CONSOLIDADOR
