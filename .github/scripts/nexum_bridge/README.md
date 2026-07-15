# Ponte NEXUM — manifesto vendorizado

`manifesto_citacoes.json` é um **snapshot** gerado no repo irmão
[`martbarreto-sudo/warroom-tigre`](https://github.com/martbarreto-sudo/warroom-tigre)
a partir da base MINDJUS verificada (`mindjus_data/`). Ele lista:

- **`verificadas`** — citações conferidas em fonte oficial (STJ/STF);
- **`na_base_sem_fonte`** — constam da base curada, fonte oficial a confirmar;
- **`fabricadas_conhecidas`** — blocklist da depuração MINDJUS (números que
  contaminaram a base uma vez e **jamais** podem ser citados).

Quem consome é o `../verificador_precedentes.py`, executado em todo PR de peça
pelo `peer-review.yml`: **citação fabricada reprova o gate TIER 0
automaticamente**, qualquer que seja o score dos LLMs.

## Como atualizar o snapshot

No warroom-tigre:

```bash
python ponte_nexum.py gerar        # regenera manifesto_citacoes.json na raiz
```

Copie o arquivo gerado para cá (mesmo nome). O selo `sha256` embutido é
verificado por `tests/test_verificador_precedentes.py` — um snapshot corrompido
ou editado à mão quebra o CI.

A fixture `../tests/fixtures/peca_ponte_nexum.txt` é **idêntica** à do
warroom-tigre (`tests/fixtures/peca_ponte_nexum.txt`); os testes dos dois repos
exigem a mesma classificação dela — é o teste ponta a ponta da ponte. Se editar
a fixture, edite nos dois repos.
