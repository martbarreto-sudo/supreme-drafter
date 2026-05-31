from __future__ import annotations

import os
from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from jinja2 import Environment, FileSystemLoader, select_autoescape

from .auth import require_bearer
from .casos.data import FEITOS
from .halt import auditar
from .models import DraftRequest, Minuta
from .upload import receber_autos

app = FastAPI(title="Nexum by Tigre — Supreme Drafter", version="0.1.0")

_TEMPLATES_DIR = Path(__file__).parent / "templates"
_jinja = Environment(
    loader=FileSystemLoader(_TEMPLATES_DIR),
    autoescape=select_autoescape(disabled_extensions=("j2", "md")),
    keep_trailing_newline=True,
)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/autos", dependencies=[Depends(require_bearer)])
async def upload_autos(
    feito_id: str = Form(...),
    arquivo: UploadFile = File(...),
):
    return await receber_autos(feito_id, arquivo)


@app.get("/casos/{feito_id}/vulnerabilidades")
def vulnerabilidades(feito_id: str):
    feito = FEITOS.get(feito_id)
    if feito is None:
        raise HTTPException(404, f"Feito '{feito_id}' não catalogado")
    return feito.vulnerabilidades


@app.post("/draft")
def draft(req: DraftRequest):
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


@app.post("/draft/llm")
def draft_llm(req: DraftRequest):
    feito = FEITOS.get(req.feito_id)
    if feito is None:
        raise HTTPException(404, f"Feito '{req.feito_id}' não catalogado")

    halt = auditar(req)
    if halt is not None:
        return JSONResponse(status_code=422, content=halt.model_dump())

    if not os.getenv("ANTHROPIC_API_KEY"):
        raise HTTPException(503, "ANTHROPIC_API_KEY ausente — engine LLM indisponível")

    from .llm import gerar_minuta, validar_feito_hbm
    from .quality import avaliar_qualidade

    minuta = gerar_minuta(feito, req.fatos, req.peca_tipo)
    qualidade = avaliar_qualidade(minuta.texto, feito, req.fatos)
    falhas = validar_feito_hbm(minuta.texto) if req.feito_id == "Feito-HBM" else []

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
    }
