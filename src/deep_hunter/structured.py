"""Deriva o JSON Schema estrito da Anthropic (output_config.format) a partir de um
modelo Pydantic — fonte única de verdade, aposentando o schema JSON duplicado.

Structured outputs da Messages API exige, em cada objeto, `additionalProperties:
false` e `required` completo, e NÃO suporta restrições de string/numéricas
(pattern, minLength, minimum, ...).

Duas regras de segurança governam este conversor:

1. **Restrição removida é restrição preservada na descrição.** Descartar o
   `pattern` do NPU em silêncio deixava o modelo sem qualquer indicação do
   formato do CNJ — e a validação client-side (`model_validate_json`) rejeitava
   a resposta depois de a auditoria já ter sido paga. O que a API não aceita como
   palavra-chave segue anexado à `description`, como faz o próprio SDK.
2. **Só nós de schema são filtrados.** As chaves de `properties`/`$defs` são
   nomes de campos, não palavras-chave: filtrá-las apagava do contrato, sem erro
   algum, qualquer campo chamado `pattern`, `maxLength`, `minimum`...
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

# Restrições não suportadas por structured outputs — retiradas das palavras-chave
# do schema e reexpostas ao modelo dentro da `description`.
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

# Chaves cujo valor é um mapa `nome → subschema` (as chaves são nomes de campos).
_MAPAS_DE_SUBSCHEMA = {"properties", "$defs", "definitions"}
# Chaves cujo valor é dado literal do domínio, não schema — não se recorre nelas.
_LITERAIS = {"enum", "const", "default", "examples", "title", "description"}


def _com_restricoes(descricao: Any, descartadas: dict) -> str:
    """Anexa à descrição as restrições que a API não aceita como palavra-chave."""
    sufixo = "{" + ", ".join(f"{k}: {v}" for k, v in descartadas.items()) + "}"
    return f"{descricao}\n\n{sufixo}" if descricao else sufixo


def _normalize(node: Any) -> Any:
    if isinstance(node, list):
        return [_normalize(x) for x in node]
    if not isinstance(node, dict):
        return node

    out: dict = {}
    descartadas: dict = {}
    for k, v in node.items():
        if k in _UNSUPPORTED:
            descartadas[k] = v
        elif k in _MAPAS_DE_SUBSCHEMA:
            out[k] = {nome: _normalize(sub) for nome, sub in v.items()}
        elif k in _LITERAIS:
            out[k] = v
        else:
            out[k] = _normalize(v)

    if descartadas:
        out["description"] = _com_restricoes(out.get("description"), descartadas)

    if out.get("type") == "object":
        out["additionalProperties"] = False
        out["required"] = list(out.get("properties", {}))  # strict: todos obrigatórios
    return out


def to_anthropic_schema(model: type[BaseModel]) -> dict:
    """Converte um modelo Pydantic v2 no schema estrito aceito por output_config.format."""
    return _normalize(model.model_json_schema())
