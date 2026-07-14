"""Adaptadores concretos da NEXUM Engine v5.5 (injeção de dependência pura)."""

from .anthropic_adapters import AnthropicVertexAdapter, DirectAPIAdapter
from .asyncpg_adapter import AsyncpgAdapter
from .vertex_embed_adapter import VertexEmbedAdapter

__all__ = [
    "AnthropicVertexAdapter",
    "AsyncpgAdapter",
    "DirectAPIAdapter",
    "VertexEmbedAdapter",
]
