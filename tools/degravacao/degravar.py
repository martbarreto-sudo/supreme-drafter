#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Degravação de audiência via Gemini (multimodal).

Recebe um arquivo de áudio/vídeo e devolve a degravação em PT-BR, com blocos de
timestamp e IDENTIFICAÇÃO DOS DEPOENTES — no padrão usado pela banca.

Uso (na sua máquina, com o Gemini logado por API key):
    export GEMINI_API_KEY="sua_chave"   # https://aistudio.google.com/apikey
    python3 degravar.py audiencia.mp4 \
        --saida degravacao.txt \
        --depoentes "Juiz: Dr. Fulano; MP: Dr. Bruno; Defesa: Dr. Ayron; Vítima: Luan; Testemunha: Renan"

Dependência:
    pip install google-genai
"""
import argparse
import os
import sys
import time

PROMPT_BASE = """Você é um degravador forense de audiências judiciais brasileiras.
Transcreva o áudio/vídeo a seguir em português do Brasil, com MÁXIMA fidelidade.

REGRAS:
1. Divida em blocos por trecho, cada um iniciado por um timestamp no formato
   "(M:SS - M:SS)" (início e fim do trecho), seguido do texto na linha de baixo.
2. IDENTIFIQUE OS DEPOENTES: prefixe cada fala com o papel/nome de quem fala
   (ex.: "Juiz:", "MP:", "Defesa:", "Vítima (Luan):", "Testemunha (Renan):").
   Use o elenco informado abaixo para nomear corretamente; se não for possível
   identificar com segurança, use "Interlocutor não identificado:".
3. Transcrição VERBATIM — não corrija gramática, não resuma, não interprete.
4. Trechos inaudíveis: marque como [inaudível] (ou [inaudível 00:00] se útil).
5. Não invente conteúdo. Se houver dúvida sobre uma palavra, use [?] após ela.
6. Não inclua comentários seus fora da transcrição.
"""

HEADER = """DEGRAVAÇÃO — {arquivo}
Gerado por Gemini ({modelo}) em {data}
{elenco}
{sep}
"""


def main():
    ap = argparse.ArgumentParser(description="Degravação de audiência via Gemini.")
    ap.add_argument("audio", help="arquivo de áudio/vídeo (mp3, m4a, wav, mp4, ...)")
    ap.add_argument("--saida", "-o", default=None, help="arquivo de saída .txt (padrão: <audio>.degravacao.txt)")
    ap.add_argument("--depoentes", "-d", default="", help="elenco: 'Papel: Nome; Papel: Nome'")
    ap.add_argument("--modelo", "-m", default="gemini-2.5-pro",
                    help="modelo Gemini (padrão gemini-2.5-pro; use gemini-2.5-flash p/ rapidez/custo)")
    args = ap.parse_args()

    if not os.path.isfile(args.audio):
        sys.exit(f"ERRO: arquivo não encontrado: {args.audio}")
    if not os.environ.get("GEMINI_API_KEY"):
        sys.exit("ERRO: defina GEMINI_API_KEY (https://aistudio.google.com/apikey).")

    try:
        from google import genai
    except ImportError:
        sys.exit("ERRO: dependência ausente. Instale com:  pip install google-genai")

    saida = args.saida or (os.path.splitext(args.audio)[0] + ".degravacao.txt")
    elenco = f"Elenco informado: {args.depoentes}" if args.depoentes else "Elenco: não informado"

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

    print(f"↑ Enviando '{args.audio}' ...", file=sys.stderr)
    f = client.files.upload(file=args.audio)

    # Aguarda o processamento do arquivo (áudios longos ficam em ESTADO 'PROCESSING')
    while getattr(f, "state", None) and str(f.state).endswith("PROCESSING"):
        time.sleep(3)
        f = client.files.get(name=f.name)
    if getattr(f, "state", None) and str(f.state).endswith("FAILED"):
        sys.exit("ERRO: o Gemini falhou ao processar o arquivo enviado.")

    prompt = PROMPT_BASE + (f"\nELENCO PARA IDENTIFICAÇÃO:\n{args.depoentes}\n" if args.depoentes else "")

    print(f"⚙  Degravando com {args.modelo} ...", file=sys.stderr)
    resp = client.models.generate_content(model=args.modelo, contents=[prompt, f])
    texto = (resp.text or "").strip()
    if not texto:
        sys.exit("ERRO: resposta vazia do modelo.")

    header = HEADER.format(
        arquivo=os.path.basename(args.audio),
        modelo=args.modelo,
        data=time.strftime("%Y-%m-%d %H:%M"),
        elenco=elenco,
        sep="=" * 60,
    )
    with open(saida, "w", encoding="utf-8") as out:
        out.write(header + "\n" + texto + "\n")
    print(f"✓ Degravação salva em: {saida}", file=sys.stderr)


if __name__ == "__main__":
    main()
