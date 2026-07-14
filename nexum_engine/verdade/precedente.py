"""Modelo de domínio do precedente verificado e normalização de citações.

Schema derivado da base MINDJUS real (warroom-tigre/mindjus_data/*.json),
campo a campo — não de especulação. A doutrina 100/100 vale aqui em código:
um precedente só é citável se tiver fonte de verificação e não estiver em
quarentena (``verificacao_pendente``).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Precedente:
    """Um precedente verificado da base MINDJUS."""

    numero: str                      # ex.: "HC 598.051/SP", "Súmula 444/STJ"
    tese: str
    tribunal: str = ""
    relator: str = ""
    data_julgamento: str = ""
    ementa: str = ""
    resultado: str = ""
    tags: tuple[str, ...] = ()
    relevancia: str = ""
    fonte_verificacao: str = ""
    tema: str = ""                   # tema do arquivo/tabela de origem
    verificacao_pendente: bool = False
    motivo_quarentena: str = ""

    @property
    def citavel(self) -> bool:
        """Doutrina 100/100: citável = fonte oficial presente e sem quarentena."""
        return bool(self.fonte_verificacao) and not self.verificacao_pendente

    @property
    def numero_normalizado(self) -> str:
        return normalizar_citacao(self.numero)

    @classmethod
    def de_dict(cls, dados: dict[str, Any], *, tema: str = "") -> "Precedente":
        """Constrói a partir de um registro MINDJUS (JSON ou linha do banco)."""
        tags = dados.get("tags") or ()
        return cls(
            numero=str(dados.get("numero", "")).strip(),
            tese=str(dados.get("tese", "")).strip(),
            tribunal=str(dados.get("tribunal", "")).strip(),
            relator=str(dados.get("relator", "")).strip(),
            data_julgamento=str(
                dados.get("data_julgamento") or dados.get("julgamento") or ""
            ).strip(),
            ementa=str(
                dados.get("ementa") or dados.get("ementa_oficial") or ""
            ).strip(),
            resultado=str(dados.get("resultado", "")).strip(),
            tags=tuple(str(t) for t in tags),
            relevancia=str(dados.get("relevancia", "")).strip(),
            fonte_verificacao=str(dados.get("fonte_verificacao", "")).strip(),
            tema=tema or str(dados.get("tema", "")).strip(),
            verificacao_pendente=bool(dados.get("verificacao_pendente", False)),
            motivo_quarentena=str(dados.get("motivo_quarentena", "")).strip(),
        )


_PONTO_ENTRE_DIGITOS = re.compile(r"(?<=\d)\.(?=\d)")
_ESPACOS = re.compile(r"\s+")


def normalizar_citacao(citacao: str) -> str:
    """Forma canônica para comparação: caixa alta, sem pontos de milhar.

    "HC 598.051/SP" e "hc 598051/sp" normalizam para o mesmo valor; a
    comparação nunca é feita sobre a string bruta da peça.
    """
    texto = _PONTO_ENTRE_DIGITOS.sub("", citacao.strip().upper())
    texto = texto.replace("SÚMULA", "SUMULA")
    return _ESPACOS.sub(" ", texto)
