"""Comutação de canal: primeira parte × Vertex AI (sem rede, sem credenciais).

A portabilidade para o perímetro de nuvem do cliente é afirmação comercial; estes
testes são o que a sustenta — a troca é configuração de ambiente e nada mais.
"""

from __future__ import annotations

import anthropic
import pytest

from deep_hunter.config import Provedor, RunConfig
from deep_hunter.providers import build_client


def test_padrao_e_a_api_de_primeira_parte(monkeypatch):
    monkeypatch.delenv("DEEP_HUNTER_PROVEDOR", raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-teste")
    assert RunConfig().provedor == Provedor.ANTHROPIC.value
    assert type(build_client()) is anthropic.Anthropic


def test_provedor_vem_do_ambiente_sem_reimportar(monkeypatch):
    """O canal é lido na construção, não no import do pacote."""
    monkeypatch.setenv("DEEP_HUNTER_PROVEDOR", "vertex")
    assert RunConfig().provedor == Provedor.VERTEX.value


def test_rota_vertex_constroi_o_cliente_do_google_cloud(monkeypatch):
    monkeypatch.setenv("DEEP_HUNTER_PROVEDOR", "vertex")
    monkeypatch.setenv("ANTHROPIC_VERTEX_PROJECT_ID", "tigre-prod")
    monkeypatch.setenv("CLOUD_ML_REGION", "us-east5")

    capturado: dict = {}

    class FakeVertex:
        def __init__(self, **kwargs):
            capturado.update(kwargs)

    monkeypatch.setattr(anthropic, "AnthropicVertex", FakeVertex)
    cliente = build_client()

    assert isinstance(cliente, FakeVertex)
    assert capturado == {"project_id": "tigre-prod", "region": "us-east5"}


def test_vertex_sem_projecto_delega_a_resolucao_ao_sdk(monkeypatch):
    """Ausentes as variáveis, nada é passado — o SDK resolve por ADC e erra ele.

    Inventar aqui um projecto ou uma região esconderia do operador a configuração
    que falta no ambiente de nuvem.
    """
    monkeypatch.setenv("DEEP_HUNTER_PROVEDOR", "vertex")
    monkeypatch.delenv("ANTHROPIC_VERTEX_PROJECT_ID", raising=False)
    monkeypatch.delenv("CLOUD_ML_REGION", raising=False)

    capturado: dict = {"sentinela": True}

    class FakeVertex:
        def __init__(self, **kwargs):
            capturado.clear()
            capturado.update(kwargs)

    monkeypatch.setattr(anthropic, "AnthropicVertex", FakeVertex)
    build_client()
    assert capturado == {}


def test_provedor_desconhecido_e_recusado(monkeypatch):
    monkeypatch.setenv("DEEP_HUNTER_PROVEDOR", "bedrock")
    with pytest.raises(ValueError, match="Provedor inválido"):
        RunConfig()


def test_pipeline_usa_o_canal_configurado(monkeypatch):
    """O Pipeline sem cliente injectado passa pela comutação, não pelo atalho."""
    from deep_hunter import Pipeline

    monkeypatch.setenv("DEEP_HUNTER_PROVEDOR", "vertex")
    monkeypatch.setenv("ANTHROPIC_VERTEX_PROJECT_ID", "tigre-prod")
    monkeypatch.setenv("CLOUD_ML_REGION", "europe-west1")

    class FakeVertex:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    monkeypatch.setattr(anthropic, "AnthropicVertex", FakeVertex)
    pipeline = Pipeline()

    assert isinstance(pipeline.client, FakeVertex)
    assert pipeline.client.kwargs["region"] == "europe-west1"
    # Os dois agentes partilham o mesmo cliente — um só canal por execução.
    assert pipeline.hunter.client is pipeline.client
    assert pipeline.drafter.client is pipeline.client
