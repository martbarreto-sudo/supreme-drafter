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
    # Um repetitivo tem DUAS citações legítimas — o número do recurso e o
    # número do tema ("REsp 2.048.687/BA" e "Tema 1.260"). Indexar só uma
    # fazia o gate bloquear a peça que citasse a outra, embora verificada.
    identificadores_alternativos: tuple[str, ...] = ()

    @property
    def citavel(self) -> bool:
        """Doutrina 100/100: citável = fonte oficial presente e sem quarentena.

        O campo ``fonte_verificacao`` é texto livre, e bases reais o usam para
        registrar a PENDÊNCIA em vez da verificação ("PENDENTE — validar antes
        de citar"). Lido como mera presença de string, esse aviso virava prova
        de verificação e o gate aprovava a citação que a base proibia. Por isso
        a pendência é detectada também no texto e no número, não só na flag.
        """
        if self.verificacao_pendente or _em_quarentena(self.numero):
            return False
        fonte = self.fonte_verificacao.strip()
        return bool(fonte) and not _texto_indica_pendencia(fonte)

    @property
    def numero_normalizado(self) -> str:
        return normalizar_citacao(self.numero)

    @property
    def chaves_de_indice(self) -> tuple[str, ...]:
        """Todas as formas pelas quais este precedente pode ser citado."""
        chaves = [self.numero_normalizado]
        chaves += [normalizar_citacao(a) for a in self.identificadores_alternativos]
        return tuple(dict.fromkeys(c for c in chaves if c))

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
            identificadores_alternativos=tuple(
                str(a).strip() for a in (dados.get("identificadores_alternativos") or ())
            ),
        )


_PONTO_ENTRE_DIGITOS = re.compile(r"(?<=\d)\.(?=\d)")
_ESPACOS = re.compile(r"\s+")

# Marcações que as bases MINDJUS usam para declarar que um registro NÃO está
# verificado. Aparecem no início de ``fonte_verificacao`` ou como prefixo do
# ``numero``; em ambos os casos o registro está em quarentena, não liberado.
_SENTINELAS_DE_PENDENCIA = (
    "PENDENTE",
    "A CONFERIR",
    "CONFERIR",
    "NAO-VERIFICADO",
    "NÃO-VERIFICADO",
    "NAO VERIFICADO",
    "NÃO VERIFICADO",
    "SEM NUMERO",
    "SEM NÚMERO",
)


def _texto_indica_pendencia(texto: str) -> bool:
    """Verdadeiro quando o texto declara pendência em vez de verificação."""
    cabeca = texto.strip().lstrip("[(*- ").upper()
    return any(cabeca.startswith(s) for s in _SENTINELAS_DE_PENDENCIA)


def _em_quarentena(numero: str) -> bool:
    """Número prefixado com marcação de quarentena (ex.: '[A CONFERIR] ...')."""
    bruto = numero.strip().upper()
    if not bruto.startswith(("[", "(")):
        return False
    return any(s in bruto[:40] for s in _SENTINELAS_DE_PENDENCIA)


def normalizar_citacao(citacao: str) -> str:
    """Forma canônica para comparação: caixa alta, sem pontos de milhar.

    "HC 598.051/SP" e "hc 598051/sp" normalizam para o mesmo valor; a
    comparação nunca é feita sobre a string bruta da peça.
    """
    texto = _PONTO_ENTRE_DIGITOS.sub("", citacao.strip().upper())
    texto = texto.replace("SÚMULA", "SUMULA")
    return _ESPACOS.sub(" ", texto)
