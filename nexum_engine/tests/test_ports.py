"""Conformidade de contrato: cada adaptador satisfaz sua Protocol."""

from nexum_engine.adapters import (
    AnthropicVertexAdapter,
    AsyncpgAdapter,
    DirectAPIAdapter,
    VertexEmbedAdapter,
)
from nexum_engine.ports import CompletionPort, DatabasePort, EmbedderPort


def test_asyncpg_adapter_satisfaz_database_port():
    assert isinstance(AsyncpgAdapter(), DatabasePort)


def test_vertex_embed_adapter_satisfaz_embedder_port():
    assert isinstance(VertexEmbedAdapter(), EmbedderPort)


def test_adaptadores_claude_satisfazem_completion_port():
    assert isinstance(AnthropicVertexAdapter(), CompletionPort)
    assert isinstance(DirectAPIAdapter(), CompletionPort)


def test_um_fake_qualquer_com_a_assinatura_certa_satisfaz_o_contrato():
    """O acoplamento é estrutural (duck typing), não por herança."""

    class FakeDB:
        async def fetch(self, query, *args):
            return []

        async def fetchrow(self, query, *args):
            return None

        async def execute(self, query, *args):
            return "OK"

    assert isinstance(FakeDB(), DatabasePort)
