"""Ponto de entrada ASGI do consumidor NEXUM para servidores (uvicorn).

O consumidor e criado por uma *factory* (`create_app`) que recebe as dependencias
injetadas. Este modulo expoe um objeto `app` de nivel de modulo construido a
partir do ambiente (REDIS_URL), permitindo apontar o uvicorn diretamente para
`nexum.consumer.asgi:app` sem a flag `--factory`.
"""

from __future__ import annotations

from nexum.consumer.app import get_app

# App ASGI de producao: le REDIS_URL do ambiente e injeta o dispatcher real.
app = get_app()
