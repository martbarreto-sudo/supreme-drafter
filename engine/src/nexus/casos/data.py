from __future__ import annotations

from ..models import Feito, FontePrimaria, StatusFato, Vulnerabilidade

# Catálogo em memória — em produção carrega de $CASO_DATA_DIR (volume controlado, fora do repo)
FEITOS: dict[str, Feito] = {
    "Feito-HBM": Feito(
        id="Feito-HBM",
        quadrante="Reconhecimento fotográfico",
        eixo_dogmatico=(
            "Tema 1.258/STF (distinguishing) + HC 598.887/SC, STJ "
            "(reconhecimento foto isolada = nulidade) + HC 712.781/RJ, STJ "
            "(contágio probatório / frutos da árvore envenenada) + "
            "art. 226, II e III, CPP"
        ),
        vulnerabilidades=[
            Vulnerabilidade(
                fato_id="reconhecimento-inicial",
                proposto="Reconhecimento fotográfico em sede policial conforme art. 226 CPP",
                realidade_verificada="Reconhecimento por foto isolada, sem fila e sem termo",
                fonte=FontePrimaria(uri="certidao://feito-hbm/inquerito-fls-12"),
                status=StatusFato.LIQUIDO,
                impacto="Vício de origem no sumário da culpa — distinguishing Tema 1.258",
            ),
            Vulnerabilidade(
                fato_id="termo-ausente",
                proposto="Ato formal de reconhecimento lavrado conforme art. 226, II e III, CPP",
                realidade_verificada="PENDENTE — auditar inexistência de termo formal de "
                "reconhecimento nos autos (auditoria de silêncio documental)",
                fonte=None,
                status=StatusFato.PENDENTE,
                impacto="Quebra do procedimento legal — nulidade autônoma além do Tema 1.258",
            ),
            Vulnerabilidade(
                fato_id="reconhecimento-em-juizo-viciado",
                proposto="Reconhecimento posterior em juízo como ato autônomo e válido",
                realidade_verificada="PENDENTE — verificar se a vítima/testemunha foi exposta "
                "à fotografia ANTES da audiência (contágio probatório)",
                fonte=None,
                status=StatusFato.PENDENTE,
                impacto="Nulidade derivada — Teoria dos Frutos da Árvore Envenenada "
                "(STJ HC 712.781/RJ)",
            ),
        ],
    ),
    "Feito-RC": Feito(
        id="Feito-RC",
        quadrante="Telemática / interceptação",
        eixo_dogmatico=(
            "Tema 977/STF (cadeia de custódia de prova digital) + "
            "RHC 143.169/RJ, STJ (prova digital sem hash = nulidade) + "
            "art. 158-A, CPP (cadeia de custódia)"
        ),
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
        quadrante="Medidas protetivas — nulidade de origem",
        eixo_dogmatico=(
            "Tema 1249/STJ (escudo procedimental MP) + art. 315, §2º, CPP "
            "(nulidade por fundamentação genérica) + art. 93, IX, CRFB "
            "(motivação obrigatória)"
        ),
        vulnerabilidades=[
            # Anonimizado. fonte=None + PENDENTE: o HALT exige auditoria contra
            # fonte primária no ambiente do operador antes de qualquer minuta.
            Vulnerabilidade(
                fato_id="representacao-mismatch",
                proposto="Representação/FONAR como substrato probatório apto contra o Paciente",
                realidade_verificada="PENDENTE — auditar titularidade nominal do documento "
                "contra o nome do Paciente no PJe",
                fonte=None,
                status=StatusFato.PENDENTE,
                impacto="Ausência material de justa causa se confirmado mismatch subjetivo "
                "(Geraldo Prado: contaminação por derivação)",
            ),
            Vulnerabilidade(
                fato_id="liminar-generica",
                proposto="Decisão liminar como regular exercício da tutela de urgência",
                realidade_verificada="PENDENTE — auditar se o decisum enfrenta a divergência "
                "e fundamenta concretamente",
                fonte=None,
                status=StatusFato.PENDENTE,
                impacto="Nulidade por fundamentação genérica (Art. 93, IX, CRFB c/c Art. 315, §2º, CPP)",
            ),
        ],
    ),
}
