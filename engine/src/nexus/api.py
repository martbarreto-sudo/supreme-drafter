from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from jinja2 import Environment, FileSystemLoader, select_autoescape
from slowapi.errors import RateLimitExceeded
from sqlalchemy.ext.asyncio import AsyncSession

from .audits.romaneio import compor_romaneio
from .audits.routes import router as audits_router
from .audits.service import CasoDataDirAusente, gravar_audit, gravar_romaneio
from .auditor import auditar_adversarial
from .user_data.routes import router as user_data_router
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
from .legal.disclaimer import prepend_disclaimer
from .middleware import limiter, rate_limit_exception_handler
from .models import DraftRequest, Minuta
from .upload import receber_autos

app = FastAPI(title="Nexus by Tigre — Supreme Drafter", version="0.1.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exception_handler)

# CORS — origens permitidas via env CORS_ORIGINS (comma-separated).
# Em desenvolvimento, deixe vazio (sem CORS). Em produção com frontend,
# liste explicitamente os domínios do frontend.
_cors_raw = os.getenv("CORS_ORIGINS", "").strip()
if _cors_raw:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in _cors_raw.split(",") if o.strip()],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
        max_age=600,
    )

app.include_router(auth_router)
app.include_router(billing_router)
app.include_router(audits_router)
app.include_router(user_data_router)

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
@limiter.limit("60/minute")
async def upload_autos(
    request: Request,
    feito_id: str = Form(...),
    arquivo: UploadFile = File(...),
    user: User = Depends(get_current_user),
):
    """Upload de PDF dos autos. JWT obrigatório. Rate-limited 60/min/IP.

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
@limiter.limit("30/minute")
async def draft_llm(
    request: Request,
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

    minuta = gerar_minuta(
        feito, req.fatos, req.peca_tipo, modo=req.modo_redacional.value
    )
    # quality_score é avaliado sobre o TEXTO ORIGINAL do LLM (sem disclaimer),
    # para que gates como "submissão burocrática" não sofram interferência do
    # cabeçalho. Disclaimer é cosmético/legal, não afeta avaliação técnica.
    qualidade = avaliar_qualidade(minuta.texto, feito, req.fatos)
    falhas = validar_feito_hbm(minuta.texto) if req.feito_id == "Feito-HBM" else []

    # disclaimer obrigatório — toda peça gerada carrega o cabeçalho que
    # nomeia o advogado-operador responsável e explicita que é minuta,
    # não peça final. Aplicado ANTES de persistir e ANTES de responder.
    data_iso = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")
    texto_final = prepend_disclaimer(minuta.texto, user, data_iso)

    # AUDITOR adversarial (Camada 4 do TIER 0) — roda sobre o TEXTO ORIGINAL
    # (sem disclaimer; disclaimer é cabeçalho cosmético) para não distorcer
    # heurísticas como vocabulário vetado ou endereçamento. NÃO bloqueia
    # entrega: apenas sinaliza para o curador humano decidir.
    parecer_adversarial = auditar_adversarial(minuta.texto, req.fatos)

    # consumir cota só após geração bem-sucedida
    await consumir_peca(session, sub)

    # registrar audit (texto em disco + metadados em DB). Falha aqui ainda
    # devolve a minuta ao usuário — peça já foi cobrada e LLM já correu;
    # melhor responder do que abortar.
    audit_id: str | None = None
    try:
        audit = await gravar_audit(
            session,
            user_id=user.id,
            feito_id=req.feito_id,
            peca_tipo=req.peca_tipo,
            minuta_texto=texto_final,  # com disclaimer no topo
            quality_score=qualidade.score,
            modelo=minuta.modelo,
            input_tokens=minuta.input_tokens,
            cache_read_tokens=minuta.cache_read_tokens,
            cache_creation_tokens=minuta.cache_creation_tokens,
            output_tokens=minuta.output_tokens,
        )
        audit_id = audit.id
        # Romaneio de Revisão — par com a minuta. Composto APÓS gravar_audit
        # porque depende do audit.id (referencia na cabeçalho a peça-alvo
        # pelo ID que o operador hit no endpoint /user/audits/{id}/romaneio).
        romaneio_texto = compor_romaneio(
            audit_id=audit.id,
            feito=feito,
            peca_tipo=req.peca_tipo,
            modelo=minuta.modelo,
            quality=qualidade,
            auditor=parecer_adversarial,
            assertions_falhas=falhas,
            data_iso=data_iso,
            modo_redacional=req.modo_redacional.value,
        )
        gravar_romaneio(audit, romaneio_texto)
    except CasoDataDirAusente:
        pass  # sem CASO_DATA_DIR, segue sem persistir; resposta inclui audit_id=None

    return {
        "audit_id": audit_id,
        "feito_id": req.feito_id,
        "peca_tipo": req.peca_tipo,
        "modo_redacional": req.modo_redacional.value,
        "texto": texto_final,  # com disclaimer
        "modelo": minuta.modelo,
        "usage": {
            "input_tokens": minuta.input_tokens,
            "cache_read_tokens": minuta.cache_read_tokens,
            "cache_creation_tokens": minuta.cache_creation_tokens,
            "output_tokens": minuta.output_tokens,
        },
        "quality": qualidade.to_dict(),
        "assertions_falhas": falhas,
        "auditor_adversarial": parecer_adversarial.to_dict(),
        "billing": {
            "pecas_consumidas_no_periodo": sub.pecas_consumidas_no_periodo,
            "pecas_incluidas": sub.pecas_incluidas,
        },
    }
