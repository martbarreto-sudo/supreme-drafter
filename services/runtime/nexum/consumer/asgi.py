"""Ponto de entrada ASGI do consumidor NEXUM para servidores (uvicorn).

O consumidor e criado por uma *factory* (`create_app`) que recebe as dependencias
injetadas. Este modulo expoe um objeto `app` de nivel de modulo construido a
partir do ambiente (REDIS_URL), permitindo apontar o uvicorn diretamente para
`nexum.consumer.asgi:app` sem a flag `--factory`.
"""

from __future__ import annotations

import os

from nexum.consumer.app import get_app
from nexum.observability.tracing import configure_tracing

# Ativa o tracing no entrypoint real de producao ANTES de construir o app. Como
# `configure_tracing` e no-op quando `OTEL_TRACES_EXPORTER` esta ausente/"none",
# isto e seguro em qualquer ambiente e nao exige collector; quando o Helm/compose
# injeta OTEL_TRACES_EXPORTER/OTEL_EXPORTER_OTLP_ENDPOINT, os spans passam a
# exportar de fato. Fica fora de `create_app` (importado por testes unitarios).
configure_tracing(service_name=os.getenv("OTEL_SERVICE_NAME", "nexum-consumer"))

# App ASGI de producao: le REDIS_URL do ambiente e injeta o dispatcher real.
app = get_app()
