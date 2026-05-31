from __future__ import annotations

import os
from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy.ext.asyncio import AsyncSession

from .auth.deps import get_current_user
from .auth.routes import router as auth_router
from .billing.routes import router as billing_router
from .billing.service import (
    AssinaturaInativa,
    PeriodoExpirado,
    QuotaExcedida,
    SemAssinatura,
    assert_pode_consumir_peca,
    consumir_peca,
)
from .casos.data import FEITOS
from .db.models import User
from .db.session import get_session
from .halt import auditar
from .models import DraftRequest, Minuta
from .upload import receber_autos

app = FastAPI(title="Nexus by Tigre — Supreme Drafter", version="0.1.0")
app.include_router(auth_router)
app.include_router(billing_router)

_TEMPLATES_DIR = Path(__file__).parent / "templates"
_jinja = Environment(
    loader=FileSystemLoader(_TEMPLATES_DIR),
    autoescape=select_autoescape(disabled_extensions=("j2", "md")),
    keep_trailing_newline=True,
)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/autos")
async def upload_autos(
    feito_id: str = Form(...),
    arquivo: UploadFile = File(...),
    user: User = Depends(get_current_user),
):
    """Upload de PDF dos autos. JWT obrigatório.

    Não consome peça (storage é parte do plano). O fonte_uri retornado
    pode ser usado em /draft/llm para gerar a minuta com cobrança.
    """
    return await receber_autos(user.id, feito_id, arquivo)


@app.get("/casos/{feito_id}/vulnerabilidades")
def vulnerabilidades(feito_id: str):
    feito = FEITOS.get(feito_id)
    if feito is None:
        raise HTTPException(404, f"Feito '{feito_id}' não catalogado")
    return feito.vulnerabilidades


@app.post("/draft")
def draft(req: DraftRequest):
    """Path determinístico via Jinja2 — sem LLM, sem cobrança.

    Mantido aberto: serve para validar pipeline + HALT em dev. O custo real
    (Anthropic API) está no /draft/llm que é o endpoint comercial com JWT.
    """
    feito = FEITOS.get(req.feito_id)
    if feito is None:
        raise HTTPException(404, f"Feito '{req.feito_id}' não catalogado")

    halt = auditar(req)
    if halt is not None:
        return JSONResponse(status_code=422, content=halt.model_dump())

    template_name = f"{req.peca_tipo.lower()}.md.j2"
    try:
        template = _jinja.get_template(template_name)
    except Exception:
        raise HTTPException(501, f"Template '{template_name}' ainda não implementado")

    texto = template.render(feito=feito, fatos=req.fatos)
    return Minuta(
        feito_id=req.feito_id,
        peca_tipo=req.peca_tipo,
        texto=texto,
        fatos_usados=[f.id for f in req.fatos],
        auditoria_silencio=[
            "Certidão de trânsito em julgado",
            "Cadeia incremental de hashes da fonte primária",
            "Termo de desinteresse de órgão auxiliar (NUDEM/DPPE, quando aplicável)",
        ],
    )


def _quota_exception_para_http(exc: Exception) -> HTTPException:
    """Mapeia exceções de billing para 402 com mensagens consistentes."""
    if isinstance(exc, SemAssinatura):
        return HTTPException(402, "Sem assinatura ativa")
    if isinstance(exc, AssinaturaInativa):
        return HTTPException(402, f"Assinatura inativa ({exc.status.value})")
    if isinstance(exc, PeriodoExpirado):
        return HTTPException(402, "Período do plano expirado")
    if isinstance(exc, QuotaExcedida):
        return HTTPException(402, "Cota de peças esgotada no período")
    return HTTPException(500, "Erro de billing inesperado")


@app.post("/draft/llm")
async def draft_llm(
    req: DraftRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Geração via LLM. JWT obrigatório + cobra 1 peça da assinatura.

    HALT (422) NÃO cobra peça — antes da chamada ao LLM. Cobra apenas
    em sucesso, depois da geração.
    """
    feito = FEITOS.get(req.feito_id)
    if feito is None:
        raise HTTPException(404, f"Feito '{req.feito_id}' não catalogado")

    halt = auditar(req)
    if halt is not None:
        return JSONResponse(status_code=422, content=halt.model_dump())

    if not os.getenv("ANTHROPIC_API_KEY"):
        raise HTTPException(503, "ANTHROPIC_API_KEY ausente — engine LLM indisponível")

    # cota só é validada após HALT e config de LLM — ordem reduz "uso" de cota
    # em chamadas que iriam falhar de qualquer jeito
    try:
        sub = await assert_pode_consumir_peca(session, user)
    except (SemAssinatura, AssinaturaInativa, PeriodoExpirado, QuotaExcedida) as exc:
        raise _quota_exception_para_http(exc) from exc

    from .llm import gerar_minuta, validar_feito_hbm
    from .quality import avaliar_qualidade

    minuta = gerar_minuta(feito, req.fatos, req.peca_tipo)
    qualidade = avaliar_qualidade(minuta.texto, feito, req.fatos)
    falhas = validar_feito_hbm(minuta.texto) if req.feito_id == "Feito-HBM" else []

    # consumir só após geração bem-sucedida
    await consumir_peca(session, sub)

    return {
        "feito_id": req.feito_id,
        "peca_tipo": req.peca_tipo,
        "texto": minuta.texto,
        "modelo": minuta.modelo,
        "usage": {
            "input_tokens": minuta.input_tokens,
            "cache_read_tokens": minuta.cache_read_tokens,
            "cache_creation_tokens": minuta.cache_creation_tokens,
            "output_tokens": minuta.output_tokens,
        },
        "quality": qualidade.to_dict(),
        "assertions_falhas": falhas,
        "billing": {
            "pecas_consumidas_no_periodo": sub.pecas_consumidas_no_periodo,
            "pecas_incluidas": sub.pecas_incluidas,
        },
    }
