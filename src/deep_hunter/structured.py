"""Deriva o JSON Schema estrito da Anthropic (output_config.format) a partir de um
modelo Pydantic — fonte única de verdade, aposentando o schema JSON duplicado.

Structured outputs da Messages API exige, em cada objeto, `additionalProperties:
false` e `required` completo, e NÃO suporta restrições de string/numéricas
(pattern, minLength, minimum, ...). Este conversor normaliza o schema do Pydantic
para essas regras; a validação fina (ex.: pattern do NPU) permanece client-side
no `DossierHunterSchema.model_validate_json`.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

# Restrições não suportadas por structured outputs — removidas do schema enviado.
_UNSUPPORTED = {
    "pattern",
    "minLength",
    "maxLength",
    "minimum",
    "maximum",
    "exclusiveMinimum",
    "exclusiveMaximum",
    "multipleOf",
    "minItems",
    "maxItems",
    "uniqueItems",
}


def _normalize(node: Any) -> Any:
    if isinstance(node, dict):
        out = {k: _normalize(v) for k, v in node.items() if k not in _UNSUPPORTED}
        if out.get("type") == "object":
            props = out.get("properties", {})
            out["additionalProperties"] = False
            out["required"] = list(props.keys())  # strict: todos obrigatórios
        return out
    if isinstance(node, list):
        return [_normalize(x) for x in node]
    return node


def to_anthropic_schema(model: type[BaseModel]) -> dict:
    """Converte um modelo Pydantic v2 no schema estrito aceito por output_config.format."""
    return _normalize(model.model_json_schema())
