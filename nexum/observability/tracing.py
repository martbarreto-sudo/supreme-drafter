"""Tracing distribuido (OpenTelemetry) do pipeline forense NEXUM.

Este modulo centraliza a configuracao do `TracerProvider` e os utilitarios de
propagacao de contexto W3C usados pelo relay, pelo consumidor e pelo dispatcher.

Principios de projeto:

* **No-op por padrao.** Importar este modulo (ou usar `TRACER`) nunca exige um
  collector. Enquanto `configure_tracing` nao for chamado com um exportador
  real, o `trace.get_tracer` usa o provider default (no-op) da API: os spans sao
  criados via `start_as_current_span` mas nao gravam nem exportam nada, de modo
  que o comportamento do pipeline permanece identico.
* **Exportador tardio.** O `OTLPSpanExporter` so e importado quando explicitamente
  selecionado, para que testes/CI nao precisem do pacote gRPC/HTTP instalado.
* **Idempotente.** `configure_tracing` registra o provider global uma unica vez.
"""

from __future__ import annotations

import os
from typing import Optional

from opentelemetry import trace
from opentelemetry.context import Context
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
    SimpleSpanProcessor,
    SpanExporter,
)
from opentelemetry.trace.propagation.tracecontext import (
    TraceContextTextMapPropagator,
)

# Propagador W3C `traceparent`/`tracestate` reutilizado nas duas pontas.
_PROPAGATOR = TraceContextTextMapPropagator()

# Provider registrado globalmente (evita registro duplicado).
_PROVIDER: Optional[TracerProvider] = None


def configure_tracing(
    service_name: str,
    exporter: Optional[str] = None,
) -> TracerProvider:
    """Configura e registra um `TracerProvider` global (idempotente).

    A selecao do exportador segue a ordem: argumento `exporter`, senao a env
    `OTEL_TRACES_EXPORTER`, senao `"none"` (default no-op):

    * ``"otlp"``    -> `OTLPSpanExporter` (importado tardiamente) com
      `BatchSpanProcessor`; usa `OTEL_EXPORTER_OTLP_ENDPOINT` quando definido.
    * ``"console"`` -> `ConsoleSpanExporter` com `SimpleSpanProcessor`.
    * ``"none"``/``None`` -> nenhum span processor (no-op), o padrao, para que o
      pipeline rode sem qualquer collector.

    Retorna o `TracerProvider` em uso. Chamadas subsequentes nao re-registram.
    """

    global _PROVIDER
    if _PROVIDER is not None:
        return _PROVIDER

    choice = (exporter or os.environ.get("OTEL_TRACES_EXPORTER") or "none").lower()
    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)

    if choice == "otlp":
        # Importacao tardia: so exige o pacote do exportador quando selecionado.
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
            OTLPSpanExporter,
        )

        endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
        otlp = OTLPSpanExporter(endpoint=endpoint) if endpoint else OTLPSpanExporter()
        provider.add_span_processor(BatchSpanProcessor(otlp))
    elif choice == "console":
        provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
    else:
        # "none"/None: sem span processor -> no-op (nao exige collector).
        pass

    trace.set_tracer_provider(provider)
    _PROVIDER = provider
    return provider


def configure_tracing_for_test(exporter: SpanExporter) -> TracerProvider:
    """Registra um provider de teste que exporta para `exporter` (SimpleSpanProcessor).

    Facilita testes unitarios com `InMemorySpanExporter`: o provider global e
    criado uma unica vez e cada chamada apenas anexa um novo `SimpleSpanProcessor`
    para o exportador informado, preservando o registro global (que so pode ser
    feito uma vez por processo).
    """

    global _PROVIDER
    if _PROVIDER is None:
        _PROVIDER = TracerProvider(
            resource=Resource.create({"service.name": "nexum-test"})
        )
        trace.set_tracer_provider(_PROVIDER)
    _PROVIDER.add_span_processor(SimpleSpanProcessor(exporter))
    return _PROVIDER


def get_tracer(name: str) -> trace.Tracer:
    """Retorna um `Tracer` para o `name` informado (`trace.get_tracer`)."""

    return trace.get_tracer(name)


def inject_trace_context() -> dict:
    """Injeta o contexto de trace atual num carrier novo (W3C `traceparent`).

    Retorna um `dict` com as chaves `traceparent`/`tracestate` quando ha um
    span ativo; um dict vazio sob o provider no-op.
    """

    carrier: dict = {}
    _PROPAGATOR.inject(carrier)
    return carrier


def extract_trace_context(carrier: dict) -> Context:
    """Extrai um `Context` de um carrier W3C para uso como pai de span."""

    return _PROPAGATOR.extract(carrier)


# Tracer de modulo compartilhado pelo pipeline. Como e um proxy, ele delega ao
# provider global vigente no momento de criar o span (no-op ate configurar).
TRACER = get_tracer("nexum")
