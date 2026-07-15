from unittest.mock import MagicMock

from nexus.casos.data import FEITOS
from nexus.llm import (
    MODEL_DEFAULT,
    SYSTEM_PROMPT,
    gerar_minuta,
    validar_feito_hbm,
)
from nexus.models import Fato, FontePrimaria


def _mock_response(text: str):
    msg = MagicMock()
    text_block = MagicMock()
    text_block.type = "text"
    text_block.text = text
    msg.content = [text_block]
    msg.usage = MagicMock(
        input_tokens=100,
        cache_read_input_tokens=80,
        cache_creation_input_tokens=20,
        output_tokens=500,
    )
    return msg


def _fato_liquido(id_: str = "f1") -> Fato:
    return Fato(
        id=id_,
        proposto="Reconhecimento por foto",
        verificado="Reconhecimento por foto isolada, sem fila, sem termo",
        fonte=FontePrimaria(uri="certidao://feito-hbm/inquerito-fls-12"),
    )


def test_system_prompt_contains_protocol_keywords():
    for kw in [
        "HALT Ex-Officio",
        "Dado Líquido",
        "Temperatura Zero",
        "Auditoria de Silêncio",
        "KAKAY",
        "Toron",
        "Tofic",
        "Assinatura Tigre",
    ]:
        assert kw in SYSTEM_PROMPT, f"Faltando no system prompt: {kw}"


def test_gerar_minuta_chama_anthropic_com_caching_e_adaptive():
    client = MagicMock()
    client.messages.create.return_value = _mock_response("texto da minuta")

    minuta = gerar_minuta(
        FEITOS["Feito-HBM"], [_fato_liquido()], "HC", client=client
    )

    kwargs = client.messages.create.call_args.kwargs
    assert kwargs["model"] == MODEL_DEFAULT
    assert kwargs["thinking"] == {"type": "adaptive"}
    assert kwargs["output_config"] == {"effort": "high"}
    assert isinstance(kwargs["system"], list)
    assert kwargs["system"][0]["cache_control"] == {"type": "ephemeral"}
    assert kwargs["system"][0]["text"] == SYSTEM_PROMPT
    assert minuta.texto == "texto da minuta"
    assert minuta.modelo == MODEL_DEFAULT
    assert minuta.cache_read_tokens == 80
    assert minuta.cache_creation_tokens == 20


def test_gerar_minuta_respeita_env_var_modelo(monkeypatch):
    monkeypatch.setenv("NEXUS_MODEL", "claude-sonnet-4-6")
    client = MagicMock()
    client.messages.create.return_value = _mock_response("...")

    minuta = gerar_minuta(
        FEITOS["Feito-HBM"], [_fato_liquido()], "HC", client=client
    )
    assert client.messages.create.call_args.kwargs["model"] == "claude-sonnet-4-6"
    assert minuta.modelo == "claude-sonnet-4-6"


def test_user_message_inclui_dados_do_feito():
    client = MagicMock()
    client.messages.create.return_value = _mock_response("...")
    gerar_minuta(FEITOS["Feito-HBM"], [_fato_liquido()], "HC", client=client)

    user_msg = client.messages.create.call_args.kwargs["messages"][0]["content"]
    assert "Feito-HBM" in user_msg
    assert "Tema 1.258" in user_msg
    assert "certidao://feito-hbm" in user_msg
    assert "[PERTINAZ]" in user_msg


def test_user_message_omite_fato_argumentativo():
    client = MagicMock()
    client.messages.create.return_value = _mock_response("...")
    fato_disp = _fato_liquido("disp")
    fato_arg = Fato(id="hipotese", proposto="...", dispositivo=False)
    gerar_minuta(
        FEITOS["Feito-HBM"], [fato_disp, fato_arg], "HC", client=client
    )

    user_msg = client.messages.create.call_args.kwargs["messages"][0]["content"]
    assert "**disp**" in user_msg
    assert "**hipotese**" not in user_msg


def test_modo_default_e_pertinaz_no_user_message():
    client = MagicMock()
    client.messages.create.return_value = _mock_response("...")
    gerar_minuta(FEITOS["Feito-HBM"], [_fato_liquido()], "HC", client=client)

    user_msg = client.messages.create.call_args.kwargs["messages"][0]["content"]
    assert "Modo redacional [PERTINAZ]" in user_msg
    # diretriz concreta do modo, não só o rótulo
    assert "nulidades de ordem pública e mérito" in user_msg


def test_modo_prequestionador_injeta_diretriz_de_prequestionamento():
    client = MagicMock()
    client.messages.create.return_value = _mock_response("...")
    gerar_minuta(
        FEITOS["Feito-HBM"], [_fato_liquido()], "RHC",
        modo="PREQUESTIONADOR", client=client,
    )

    user_msg = client.messages.create.call_args.kwargs["messages"][0]["content"]
    assert "[PREQUESTIONADOR]" in user_msg
    assert "PLANTE PREQUESTIONAMENTO" in user_msg
    assert "REsp/RExt" in user_msg


def test_modo_custodia_poe_tese_cautelar_no_topo():
    client = MagicMock()
    client.messages.create.return_value = _mock_response("...")
    gerar_minuta(
        FEITOS["Feito-HBM"], [_fato_liquido()], "HC",
        modo="CUSTODIA", client=client,
    )
    user_msg = client.messages.create.call_args.kwargs["messages"][0]["content"]
    assert "[CUSTODIA]" in user_msg
    assert "liberdade IMEDIATA" in user_msg


def test_modo_desconhecido_cai_em_pertinaz():
    """gerar_minuta é permissivo: modo fora do enum usa a diretriz PERTINAZ."""
    client = MagicMock()
    client.messages.create.return_value = _mock_response("...")
    gerar_minuta(
        FEITOS["Feito-HBM"], [_fato_liquido()], "HC",
        modo="INEXISTENTE", client=client,
    )
    user_msg = client.messages.create.call_args.kwargs["messages"][0]["content"]
    # rótulo ecoa o que foi pedido, mas a diretriz é a de PERTINAZ (fallback)
    assert "nulidades de ordem pública e mérito" in user_msg


def test_validar_feito_hbm_aprova_minuta_completa():
    minuta_ok = """
    II. TABELA DE VULNERABILIDADES
    | ... |

    III. DO DIREITO
    Distinguishing estrito contra o Tema 1.258/STF. Conforme HC 598.887/SC (STJ)...
    """
    assert validar_feito_hbm(minuta_ok) == []


def test_validar_feito_hbm_reprova_sem_precedente():
    falhas = validar_feito_hbm("Sem distinguishing relevante.")
    assert len(falhas) == 3
    assert any("Tema 1.258" in f for f in falhas)
    assert any("598.887" in f for f in falhas)
    assert any("vulnerabilidades" in f.lower() for f in falhas)


def test_validar_feito_hbm_aceita_grafias_alternativas():
    minuta = "Tema 1258 e HC 598887 e TABELA DE VULNERABILIDADES"
    assert validar_feito_hbm(minuta) == []
