"""Gateway declarativo NEXUM — expõe o endpoint POST /draft/llm.

    [Request] ─► POST /draft/llm ─► Validação nativa Pydantic ─► 422 (falha)
                                              │
                                              ▼ (payload íntegro)
                                DraftEngine.compor_instrucao_retorica

O FastAPI valida o corpo contra `DraftRequest` (que aninha `DossierHunterSchema`),
gerando HTTP 422 nativo caso o NPU ou o payload falhem na tipagem. O endpoint compõe
a diretriz retórica sob Temperatura Zero Invariante — sem tocar em rede/credenciais.

Executar o servidor (requer `pip install uvicorn`):
    uvicorn deep_hunter.api:app --reload
"""

from __future__ import annotations

from fastapi import FastAPI, File, HTTPException, UploadFile

from core.draft_engine import DraftEngine, DraftRequest

from .mock_auditor import audit_pdf_bytes
from .pdf_ingest import MAX_PDF_BYTES

app = FastAPI(
    title="NEXUM Draft Gateway",
    description="Barramento síncrono de composição retórica (Tier 0).",
    version="0.1.0",
)

_engine = DraftEngine()

# Teto de upload do /audit. Sem ele, `await file.read()` trazia o ficheiro inteiro
# para memória — um único POST de dimensão arbitrária derruba o barramento.
MAX_UPLOAD_BYTES = MAX_PDF_BYTES
_PEDACO = 1 << 20  # 1 MiB


async def _ler_ate_ao_teto(file: UploadFile, teto: int) -> bytes:
    """Lê o upload em pedaços, abortando com 413 assim que o teto é ultrapassado."""
    pedacos: list[bytes] = []
    total = 0
    while pedaco := await file.read(_PEDACO):
        total += len(pedaco)
        if total > teto:
            raise HTTPException(
                status_code=413,
                detail=(
                    f"Autos excedem o teto de {teto / 1e6:.1f} MB. "
                    "Divida os autos em volumes antes de auditar."
                ),
            )
        pedacos.append(pedaco)
    return b"".join(pedacos)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "engine": "DraftEngine", "tier": 0}


@app.post("/audit")
async def audit(file: UploadFile = File(...)) -> dict:
    """Recebe os autos em PDF e devolve o DossierHunterSchema (mock local).

    Fecha o ciclo local Zero-Credencial:
        PDF → /audit → DossierHunterSchema → /draft/llm → minuta.

    PDF vazio ou corrompido → HTTP 422; acima do teto de upload → HTTP 413.
    Nenhuma chamada de rede/LLM é feita.
    """
    raw = await _ler_ate_ao_teto(file, MAX_UPLOAD_BYTES)
    try:
        dossie = audit_pdf_bytes(raw, filename=file.filename or "autos.pdf")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    # mode="json" → datetimes em ISO 8601, prontos para consumo por /draft/llm.
    return dossie.model_dump(mode="json")


@app.post("/draft/llm")
def draft_llm(request: DraftRequest) -> dict:
    """Valida o payload e devolve a instrução retórica composta.

    Uma requisição espúria (NPU fora do padrão CNJ, modo inválido, campo ausente)
    é barrada nativamente pelo FastAPI com HTTP 422 antes de chegar aqui.
    """
    instrucao = _engine.compor_instrucao_retorica(request)
    return {
        "modo": request.modo.value,
        "npu": request.dados_hunter.npu,
        "tribunal": request.dados_hunter.tribunal,
        "instrucao_retorica": instrucao,
    }
