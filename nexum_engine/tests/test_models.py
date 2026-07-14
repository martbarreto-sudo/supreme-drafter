"""Cânone de modelos: valores, validação e formato Vertex."""

import pytest

from nexum_engine import models


def test_canone_de_roteamento():
    assert models.MODELO_AGENTE_PARALELO == "claude-sonnet-4-6"
    assert models.MODELO_CONSOLIDADOR == "claude-opus-4-8"
    assert models.MODELOS_PERMITIDOS == {
        models.MODELO_AGENTE_PARALELO,
        models.MODELO_CONSOLIDADOR,
    }


def test_validar_modelo_aceita_canone():
    for m in models.MODELOS_PERMITIDOS:
        assert models.validar_modelo(m) == m


def test_validar_modelo_rejeita_aposentados():
    for proibido in models.MODELOS_PROIBIDOS:
        with pytest.raises(models.ModeloInvalidoError, match="aposentado"):
            models.validar_modelo(proibido)


def test_validar_modelo_rejeita_desconhecidos():
    with pytest.raises(models.ModeloInvalidoError, match="fora do cânone"):
        models.validar_modelo("claude-imaginario-9")


def test_modelo_para_vertex_usa_id_puro_por_padrao():
    # Modelos de geração atual no Vertex usam o ID puro, sem @data.
    assert models.modelo_para_vertex("claude-opus-4-8") == "claude-opus-4-8"


def test_modelo_para_vertex_snapshot_datado():
    assert (
        models.modelo_para_vertex("claude-sonnet-4-6", "20260101")
        == "claude-sonnet-4-6@20260101"
    )


def test_modelo_para_vertex_valida_o_canone():
    with pytest.raises(models.ModeloInvalidoError):
        models.modelo_para_vertex("claude-3-5-" + "sonnet-20241022")
