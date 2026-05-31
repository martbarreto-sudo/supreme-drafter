from __future__ import annotations

from .dado_liquido import avaliar
from .models import DraftRequest, HaltResponse, StatusFato


def auditar(req: DraftRequest) -> HaltResponse | None:
    vicios: list[str] = []
    for fato in req.fatos:
        if not fato.dispositivo:
            continue
        status = avaliar(fato)
        if status != StatusFato.LIQUIDO:
            vicios.append(
                f"Fato '{fato.id}' em {status.value} no quadrante dispositivo "
                f"(proposto: {fato.proposto[:80]}...)"
            )
    if not vicios:
        return None
    return HaltResponse(
        motivo="Fato dispositivo sem Dado Líquido — Módulo 11 acionado",
        vicios=vicios,
        acao_purgacao=(
            "Insira fonte primária válida (log_pje://, certidao://, hash://, ...) "
            "e o campo `verificado` para cada fato listado. "
            "Reabrir a esteira após status LIQUIDO."
        ),
    )
