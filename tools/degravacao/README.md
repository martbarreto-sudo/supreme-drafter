# Degravação de audiência (Gemini)

Transcreve áudio/vídeo de audiência em PT-BR, com **blocos de timestamp** e
**identificação dos depoentes** — no padrão usado pela banca.

## Pré-requisitos (na sua máquina)
```bash
pip install google-genai
export GEMINI_API_KEY="sua_chave"   # https://aistudio.google.com/apikey
```

## Uso
```bash
python3 degravar.py audiencia.mp4 \
  --saida degravacao.txt \
  --depoentes "Juiz: Dr. Fulano; MP: Dr. Bruno; Defesa: Dr. Ayron; Vítima: Luan; Testemunha: Renan"
```

Opções:
- `--saida/-o` — arquivo de saída (padrão: `<audio>.degravacao.txt`).
- `--depoentes/-d` — elenco para nomear quem fala (`Papel: Nome; ...`).
- `--modelo/-m` — `gemini-2.5-pro` (padrão, mais fiel) ou `gemini-2.5-flash` (rápido/barato).

## Saída
Arquivo `.txt` com cabeçalho + blocos:
```
(0:00 - 0:11)
Juiz: Luciene, a senhora é mãe de Luan, é isso?
Vítima (Luan): ...
```

## Notas
- **Sigilo/LGPD:** áudio de audiência contém dados sensíveis. Use uma conta/projeto
  Google com retenção/treino adequados; evite contas pessoais gratuitas para material real.
- Áudios longos são enviados pela Files API e podem levar alguns minutos.
- Transcrição automática **não substitui conferência humana** antes de uso processual.
