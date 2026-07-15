"""Contrato de dados entre Deep Hunter (auditor) e Supreme Drafter (redator).

O Deep Hunter emite estritamente este payload. O Supreme Drafter só trabalha sobre
a base fática aqui contida — nunca inventa factos ou precedentes fora deste dossiê.
"""

from __future__ import annotations

# JSON Schema entregue à API via output_config.format (structured outputs).
# Restrições de structured outputs: additionalProperties:false + required em todo
# objeto; sem min/maxLength, sem min/maximum.
DOSSIE_SCHEMA: dict = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "resumo_executivo": {
            "type": "string",
            "description": "Síntese fria e técnica do estado da prova digital nos autos.",
        },
        "modo": {
            "type": "string",
            "enum": ["CRONOS", "FORENSE", "POLIGRAFO", "SIMBIOSE"],
        },
        "cronologia": {
            "type": "array",
            "description": "Linha do tempo dos eventos relevantes da cadeia de custódia.",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "data": {"type": "string", "description": "Data/hora do evento ou 'INDETERMINADA'."},
                    "evento": {"type": "string"},
                    "fls": {"type": "string", "description": "Folha dos autos (fls.) que ancora o evento, ou 'NÃO LOCALIZADA'."},
                },
                "required": ["data", "evento", "fls"],
            },
        },
        "dossie_vulnerabilidades": {
            "type": "array",
            "description": "Cada falha técnica detectada, com ancoragem em fls.",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "id": {"type": "string", "description": "Identificador curto, ex. VULN-01."},
                    "categoria": {
                        "type": "string",
                        "enum": [
                            "CADEIA_CUSTODIA",
                            "MESMIDADE_HASH",
                            "COMPETENCIA",
                            "CONTEMPORANEIDADE",
                            "CONTRADICAO_DEPOIMENTO",
                            "EXTRACAO_ILEGAL",
                            "AUSENCIA_LAUDO",
                            "OUTRO",
                        ],
                    },
                    "descricao": {"type": "string", "description": "Descrição técnica da falha."},
                    "fls": {"type": "string", "description": "Folha dos autos que comprova a falha."},
                    "gravidade": {"type": "string", "enum": ["NUCLEO_FIDEDIGNIDADE", "VALOR_EPISTEMICO", "FORMAL"]},
                    "impacto": {
                        "type": "string",
                        "description": "Consequência processual (nulidade absoluta / redução do valor probatório / desentranhamento).",
                    },
                },
                "required": ["id", "categoria", "descricao", "fls", "gravidade", "impacto"],
            },
        },
        "tabela_nulidades": {
            "type": "array",
            "description": "Nulidades arguíveis, cada uma com o precedente-âncora (Sniper Precedent).",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "vulnerabilidade_id": {"type": "string", "description": "Referência ao id da vulnerabilidade."},
                    "tese": {"type": "string", "description": "Tese jurídica de nulidade."},
                    "dispositivo": {"type": "string", "description": "Norma violada (ex. Art. 158-B CPP, ISO 27037)."},
                    "sniper_precedent": {
                        "type": "string",
                        "description": "Precedente do STJ/STF que sustenta a tese (ex. AgRg no HC 828.054-RN).",
                    },
                    "fls_ancora": {"type": "string", "description": "Folha dos autos que dá base fática à nulidade."},
                },
                "required": ["vulnerabilidade_id", "tese", "dispositivo", "sniper_precedent", "fls_ancora"],
            },
        },
        "lacunas_de_grounding": {
            "type": "array",
            "description": "Alegações que NÃO puderam ser ancoradas em fls. — sinalizadas honestamente, nunca inventadas.",
            "items": {"type": "string"},
        },
    },
    "required": [
        "resumo_executivo",
        "modo",
        "cronologia",
        "dossie_vulnerabilidades",
        "tabela_nulidades",
        "lacunas_de_grounding",
    ],
}
