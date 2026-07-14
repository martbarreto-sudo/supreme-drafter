"""Adaptadores concretos, exercitados com fakes — zero credenciais de nuvem."""

import asyncio
from types import SimpleNamespace

import pytest

from nexum_engine.adapters import (
    AnthropicVertexAdapter,
    AsyncpgAdapter,
    DirectAPIAdapter,
    VertexEmbedAdapter,
)
from nexum_engine.adapters.anthropic_adapters import (
    ClienteLLMNaoInjetadoError,
    RespostaSemTextoError,
)
from nexum_engine.adapters.asyncpg_adapter import PoolNaoInjetadoError
from nexum_engine.adapters.vertex_embed_adapter import (
    ClienteEmbedNaoInjetadoError,
    RespostaEmbedInvalidaError,
)
from nexum_engine.models import (
    MODELO_AGENTE_PARALELO,
    MODELO_CONSOLIDADOR,
    ModeloInvalidoError,
)


def executar(coro):
    return asyncio.run(coro)


# --- AsyncpgAdapter ----------------------------------------------------------

class FakePool:
    """Imita a superfície de asyncpg.Pool usada pelo adaptador."""

    def __init__(self):
        self.chamadas = []

    async def fetch(self, query, *args):
        self.chamadas.append(("fetch", query, args))
        return [{"npu": "0000401-24.2026.8.17.9480"}]

    async def fetchrow(self, query, *args):
        self.chamadas.append(("fetchrow", query, args))
        return {"id": 1} if args and args[0] == 1 else None

    async def execute(self, query, *args):
        self.chamadas.append(("execute", query, args))
        return "INSERT 0 1"


def test_asyncpg_fetch_delegando_ao_pool():
    pool = FakePool()
    adapter = AsyncpgAdapter(pool)
    linhas = executar(adapter.fetch("SELECT * FROM casos WHERE id = $1", 7))
    assert linhas == [{"npu": "0000401-24.2026.8.17.9480"}]
    assert pool.chamadas[0] == ("fetch", "SELECT * FROM casos WHERE id = $1", (7,))


def test_asyncpg_fetchrow_none_quando_sem_resultado():
    adapter = AsyncpgAdapter(FakePool())
    assert executar(adapter.fetchrow("SELECT 1", 99)) is None
    assert executar(adapter.fetchrow("SELECT 1", 1)) == {"id": 1}


def test_asyncpg_execute_devolve_status():
    adapter = AsyncpgAdapter(FakePool())
    assert executar(adapter.execute("INSERT ...")) == "INSERT 0 1"


def test_asyncpg_sem_pool_aponta_o_gatilho_hitl():
    adapter = AsyncpgAdapter()
    with pytest.raises(PoolNaoInjetadoError, match="HITL"):
        executar(adapter.fetch("SELECT 1"))


# --- VertexEmbedAdapter ------------------------------------------------------

class FakeEmbedClient:
    def __init__(self, resposta=None):
        self.resposta = resposta
        self.chamadas = []

    async def embed(self, *, model, texts):
        self.chamadas.append((model, texts))
        if self.resposta is not None:
            return self.resposta
        return [[0.1, 0.2] for _ in texts]


def test_embed_devolve_um_vetor_por_texto():
    client = FakeEmbedClient()
    adapter = VertexEmbedAdapter(client, modelo="modelo-embed")
    vetores = executar(adapter.embed(["cadeia de custódia", "hearsay"]))
    assert vetores == [[0.1, 0.2], [0.1, 0.2]]
    assert client.chamadas == [("modelo-embed", ["cadeia de custódia", "hearsay"])]


def test_embed_lista_vazia_nao_chama_o_provedor():
    client = FakeEmbedClient()
    adapter = VertexEmbedAdapter(client, modelo="modelo-embed")
    assert executar(adapter.embed([])) == []
    assert client.chamadas == []


def test_embed_valida_quantidade_de_vetores():
    adapter = VertexEmbedAdapter(FakeEmbedClient(resposta=[[0.1]]), modelo="m")
    with pytest.raises(RespostaEmbedInvalidaError):
        executar(adapter.embed(["a", "b"]))


def test_embed_sem_cliente_aponta_o_gatilho_hitl():
    with pytest.raises(ClienteEmbedNaoInjetadoError, match="HITL"):
        executar(VertexEmbedAdapter().embed(["a"]))


def test_embed_com_cliente_exige_modelo():
    with pytest.raises(ValueError, match="modelo"):
        VertexEmbedAdapter(FakeEmbedClient())


# --- Adaptadores Claude ------------------------------------------------------

class FakeAnthropicClient:
    """Imita a superfície messages.create dos clientes anthropic.*."""

    def __init__(self, blocos=None, stop_reason="end_turn"):
        self.kwargs = None
        self._blocos = blocos if blocos is not None else [
            SimpleNamespace(type="text", text="minuta gerada"),
        ]
        self._stop = stop_reason
        self.messages = SimpleNamespace(create=self._create)

    async def _create(self, **kwargs):
        self.kwargs = kwargs
        return SimpleNamespace(content=self._blocos, stop_reason=self._stop)


def test_direct_api_usa_o_modelo_dos_agentes_paralelos():
    client = FakeAnthropicClient()
    adapter = DirectAPIAdapter(client)
    texto = executar(adapter.gerar("analise o NPU", system="você é o A.02"))
    assert texto == "minuta gerada"
    assert client.kwargs["model"] == MODELO_AGENTE_PARALELO
    assert client.kwargs["system"] == "você é o A.02"
    assert client.kwargs["messages"] == [{"role": "user", "content": "analise o NPU"}]


def test_vertex_usa_o_modelo_do_consolidador_com_id_puro():
    client = FakeAnthropicClient()
    adapter = AnthropicVertexAdapter(client)
    executar(adapter.gerar("consolide os pareceres"))
    assert client.kwargs["model"] == MODELO_CONSOLIDADOR
    assert "system" not in client.kwargs


def test_vertex_snapshot_datado_formata_nome_arroba_data():
    client = FakeAnthropicClient()
    adapter = AnthropicVertexAdapter(client, versao_snapshot="20260101")
    executar(adapter.gerar("x"))
    assert client.kwargs["model"] == f"{MODELO_CONSOLIDADOR}@20260101"


def test_max_tokens_e_repassado():
    client = FakeAnthropicClient()
    executar(DirectAPIAdapter(client).gerar("x", max_tokens=32000))
    assert client.kwargs["max_tokens"] == 32000


def test_multiplos_blocos_de_texto_sao_concatenados():
    blocos = [
        SimpleNamespace(type="thinking", thinking="..."),
        SimpleNamespace(type="text", text="parte 1"),
        SimpleNamespace(type="text", text="parte 2"),
    ]
    adapter = DirectAPIAdapter(FakeAnthropicClient(blocos=blocos))
    assert executar(adapter.gerar("x")) == "parte 1\nparte 2"


def test_resposta_sem_texto_falha_explicitamente():
    adapter = DirectAPIAdapter(
        FakeAnthropicClient(blocos=[], stop_reason="refusal")
    )
    with pytest.raises(RespostaSemTextoError, match="refusal"):
        executar(adapter.gerar("x"))


def test_sem_cliente_aponta_o_gatilho_hitl():
    with pytest.raises(ClienteLLMNaoInjetadoError, match="HITL"):
        executar(DirectAPIAdapter().gerar("x"))


def test_construtor_rejeita_modelo_fora_do_canone():
    with pytest.raises(ModeloInvalidoError):
        DirectAPIAdapter(FakeAnthropicClient(), modelo="claude-imaginario-9")
