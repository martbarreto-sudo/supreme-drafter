from __future__ import annotations

from ..models import Feito, FontePrimaria, StatusFato, Vulnerabilidade

# Catálogo em memória — em produção carrega de $CASO_DATA_DIR (volume controlado, fora do repo)
FEITOS: dict[str, Feito] = {
    "Feito-HBM": Feito(
        id="Feito-HBM",
        quadrante="Reconhecimento fotográfico",
        eixo_dogmatico="Tema 1.258/STF + HC 598.887/SC (STJ)",
        vulnerabilidades=[
            Vulnerabilidade(
                fato_id="reconhecimento-inicial",
                proposto="Reconhecimento fotográfico em sede policial conforme art. 226 CPP",
                realidade_verificada="Reconhecimento por foto isolada, sem fila e sem termo",
                fonte=FontePrimaria(uri="certidao://feito-hbm/inquerito-fls-12"),
                status=StatusFato.LIQUIDO,
                impacto="Vício de origem no sumário da culpa — distinguishing Tema 1.258",
            ),
        ],
    ),
    "Feito-RC": Feito(
        id="Feito-RC",
        quadrante="Telemática / interceptação",
        eixo_dogmatico="Tema 977/STF",
        vulnerabilidades=[
            Vulnerabilidade(
                fato_id="marco-temporal",
                proposto="Marco telemático fixado em 25/06/2025",
                realidade_verificada="Pendente — extração bit-a-bit do PJe",
                fonte=None,
                status=StatusFato.PENDENTE,
                impacto="Litigância de má-fé caso divirja do log auditado",
            ),
        ],
    ),
    "Feito-FB": Feito(
        id="Feito-FB",
        quadrante="Robotização penal punitiva",
        eixo_dogmatico="Tema 1249/STJ",
        vulnerabilidades=[],
    ),
}
