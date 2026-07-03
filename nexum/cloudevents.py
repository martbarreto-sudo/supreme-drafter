"""Modelos CloudEvents v1.0 (CNCF) para o pipeline forense NEXUM TIER 0.

Este modulo define o envelope CloudEvents e as quatro extension attributes
forenses proprietarias do NEXUM. Segundo a especificacao CloudEvents, os
*nomes* de extension attributes devem ser compostos exclusivamente por
caracteres alfanumericos minusculos (`[a-z0-9]`), sem underscores nem hifens.
"""

from __future__ import annotations

import json
import re
from enum import Enum

from pydantic import BaseModel, Field, field_validator

# --------------------------------------------------------------------------- #
# Extension attributes forenses (nomes devem ser lowercase alphanumeric)
# --------------------------------------------------------------------------- #
FORENSIC_EXTENSION_ATTRIBUTES: list[str] = [
    "correlationid",
    "idempotencykey",
    "isreplay",
    "operatorid",
]

_EXTENSION_NAME_RE = re.compile(r"^[a-z0-9]+$")


class Priority(str, Enum):
    """Prioridade operacional derivada do tipo do evento."""

    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


# Mapa tipo de evento -> prioridade. Tipos ausentes caem no default P3.
EVENT_TYPE_PRIORITY: dict[str, Priority] = {
    "br.nexum.artifact.integrity.alert.v1": Priority.P1,
    "br.nexum.artifact.compensate.v1": Priority.P1,
    "br.nexum.artifact.quarantined.v1": Priority.P2,
    "br.nexum.infra.replay.executed.v1": Priority.P3,
}


def build_idempotency_key(artifact_id: str, target_state: str) -> str:
    """Constroi a chave de idempotencia composta `artifact_id:target_state`."""

    return f"{artifact_id}:{target_state}"


class CloudEvent(BaseModel):
    """Envelope CloudEvents v1.0 com extension attributes forenses do NEXUM."""

    specversion: str = Field(default="1.0")
    id: str
    source: str
    type: str
    subject: str
    time: str
    datacontenttype: str = Field(default="application/json")

    # Extension attributes forenses (nomes lowercase alphanumeric).
    correlationid: str
    idempotencykey: str
    isreplay: bool = False
    operatorid: str = "system"

    data: dict = Field(default_factory=dict)

    @field_validator("specversion")
    @classmethod
    def _check_specversion(cls, value: str) -> str:
        if value != "1.0":
            raise ValueError("specversion deve ser '1.0' (CloudEvents v1.0)")
        return value

    @classmethod
    def _assert_extension_names_valid(cls) -> None:
        """Garante que os nomes das extension attributes sao alfanumericos minusculos.

        Rejeita qualquer nome com underscore ou hifen conforme a especificacao
        CloudEvents v1.0.
        """

        for name in FORENSIC_EXTENSION_ATTRIBUTES:
            if not _EXTENSION_NAME_RE.match(name):
                raise ValueError(
                    f"Nome de extension attribute invalido: {name!r}. "
                    "Deve ser lowercase alphanumeric, sem underscore/hifen."
                )

    def priority(self) -> Priority:
        """Retorna a `Priority` associada ao `type` deste evento (default P3)."""

        return EVENT_TYPE_PRIORITY.get(self.type, Priority.P3)

    def to_pubsub_bytes(self) -> bytes:
        """Serializa o evento para bytes UTF-8 prontos para publicacao no Pub/Sub."""

        return json.dumps(self.model_dump(), ensure_ascii=False).encode("utf-8")


# Validacao em tempo de importacao: os nomes das extensions sao imutaveis e
# devem respeitar a especificacao antes de qualquer uso do modelo.
CloudEvent._assert_extension_names_valid()
