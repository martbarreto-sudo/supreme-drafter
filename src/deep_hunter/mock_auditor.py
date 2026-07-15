"""Auditor local em modo simulação (Zero-Credencial, sem rede, sem LLM).

Extrai texto do PDF (best-effort, puro Python) e popula um `DossierHunterSchema`
100% aderente ao contrato, de forma DETERMINÍSTICA (semeada pelo hash do conteúdo)
e com omissões intencionais derivadas dos termos encontrados no texto. Serve para
fechar o ciclo local `PDF → /audit → DossierHunterSchema → /draft/llm` sem tocar no
provedor. Não é perícia real — é uma esteira de teste previsível.

Para extração de texto real, troque `_extrair_texto` por pypdf/pdfplumber; o contrato
de saída permanece idêntico.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone

from schema.dossier_hunter import (
    AttoCronologico,
    AuditoriaJuizNatural,
    DossierHunterSchema,
    MidiaPericiaCustodia,
)

_BASE = datetime(2026, 2, 1, 9, 0, tzinfo=timezone.utc)


def _extrair_texto(raw: bytes) -> str:
    """Extração best-effort: decodifica o corpo bruto para varredura de termos."""
    return raw.decode("latin-1", errors="ignore").lower()


def _npu_sintetico(seed_hex: str) -> str:
    """NPU determinístico e aderente ao padrão CNJ, semeado pelo hash."""
    digs = str(int(seed_hex[:16], 16)).zfill(13)[:13]
    return f"{digs[0:7]}-{digs[7:9]}.2026.8.17.{digs[9:13]}"


def audit_pdf_bytes(raw: bytes, filename: str = "autos.pdf") -> DossierHunterSchema:
    """Audita (mock) os bytes de um PDF e devolve o contrato validado.

    Levanta `ValueError` para PDF vazio ou corrompido (sem magic bytes `%PDF-`).
    """
    if not raw:
        raise ValueError("PDF inválido: arquivo vazio.")
    if raw[:5] != b"%PDF-":
        raise ValueError("PDF inválido: magic bytes `%PDF-` ausentes (arquivo corrompido).")

    texto = _extrair_texto(raw)
    seed = hashlib.sha256(raw).hexdigest()
    seed_int = int(seed[:8], 16)

    tem_hash = any(t in texto for t in ("hash", "sha-256", "sha256", "md5"))
    tem_plenario = "plenário" in texto or "plenario" in texto
    tem_portaria = "portaria" in texto
    tem_contemporaneidade = "contemporaneidade" in texto

    linha_tempo = [
        AttoCronologico(
            id_documento=str(10 + i),
            data_ato=_BASE + timedelta(days=i * 3),
            tipo_documento=tipo,
            usuario_protocolo=f"cert:{seed[:6].upper()}",
        )
        for i, tipo in enumerate(["Denúncia", "Decisão", "Certidão"])
    ]

    auditoria_custodia = [
        MidiaPericiaCustodia(
            id_documento="40",
            tipo_midia="CELLEBRITE_DUMP",
            hash_declarado_estado=(seed.upper() if tem_hash else None),
            possui_quebra_custodia=not tem_hash,
        )
    ]

    auditoria_magistrados = [
        AuditoriaJuizNatural(
            juiz_prolator="Juízo da Vara Criminal",
            data_ato=_BASE + timedelta(days=1),
            portaria_designacao_hash=(seed.upper() if tem_portaria else None),
            possui_desvio=tem_portaria,  # designação extraordinária = sinal de desvio
        )
    ]

    return DossierHunterSchema(
        npu=_npu_sintetico(seed),
        tribunal="TJPE",
        orgao_julgador="Vara Criminal",
        linha_tempo_atos=linha_tempo,
        auditoria_magistrados=auditoria_magistrados,
        auditoria_custodia=auditoria_custodia,
        omissao_analise_contemporaneidade=not tem_contemporaneidade,
        ausencia_ata_plenario=not tem_plenario,
        quebra_sequencial_ids=(seed_int % 2 == 0),
    )
