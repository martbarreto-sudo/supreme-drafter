#!/usr/bin/env python3
"""
Organiza arquivos do Google Drive seguindo taxonomia temática-fatual.
Uso: python organizar_drive.py --config /path/to/rclone.ini --remote manus_google_drive
"""

import subprocess
import json
import re
import argparse
from pathlib import Path
from typing import Dict, List, Tuple

# Taxonomia de Macro-Teses
TAXONOMIA = {
    "PRISAO_CAUTELAR": {
        "keywords": ["preventiv", "cautelar", "liberdade", "contemporaneidade", "excesso prazo", "revoga"],
        "precedentes": {
            "HC_143333_CONTEMPORANEIDADE": ["contemporaneidade", "tempo", "prazo"],
            "HC_152752_FUNDAMENTACAO": ["fundamenta", "genéric", "motiva"],
            "HC_137728_EXCESSO_PRAZO": ["excesso", "prazo", "demora"]
        }
    },
    "NULIDADES": {
        "keywords": ["nulidad", "ilicit", "prova ilícita", "busca", "apreens"],
        "precedentes": {
            "HC_598051_BUSCA_SEM_MANDADO": ["busca", "mandado", "domicili"],
            "HC_612234_HASH_CADEIA_CUSTODIA": ["hash", "cadeia", "custódia", "md5"],
            "HC_587456_INTERCEPTACAO": ["intercepta", "telefônic", "escuta"]
        }
    },
    "PROVAS_DIGITAIS": {
        "keywords": ["digital", "eletrônic", "whatsapp", "celular", "iped", "algoritmo", "hash"],
        "precedentes": {
            "RHC_143169_ALGORITMO_IPED": ["iped", "algoritmo", "software"],
            "RHC_51531_WHATSAPP": ["whatsapp", "mensag", "chat"],
            "HC_652284_ESPELHAMENTO": ["espelh", "cópia", "clone"]
        }
    },
    "TRIBUNAL_JURI": {
        "keywords": ["júri", "pronúncia", "impronúncia", "quesit", "soberania"],
        "precedentes": {
            "HC_PRONUNCIA_GENERICA": ["pronúncia", "genéric"],
            "HC_QUESITACAO": ["quesit", "formulação"]
        }
    },
    "CRIMES_FINANCEIROS": {
        "keywords": ["financeiro", "lavagem", "organização criminosa", "orcrim", "corrupção"],
        "precedentes": {
            "HC_LAVAGEM_DINHEIRO": ["lavagem", "dinheiro", "ocultação"],
            "HC_ORGANIZACAO_CRIMINOSA": ["organização", "criminosa", "orcrim"]
        }
    },
    "EXECUCAO_PENAL": {
        "keywords": ["execução", "progressão", "regime", "livramento", "remição"],
        "precedentes": {
            "HC_PROGRESSAO_REGIME": ["progressão", "regime"],
            "HC_LIVRAMENTO_CONDICIONAL": ["livramento", "condicional"]
        }
    }
}


def classificar_arquivo(nome_arquivo: str) -> Tuple[str, str]:
    """Classifica arquivo em macro-tese e precedente."""
    nome_lower = nome_arquivo.lower()
    
    for macro_tese, config in TAXONOMIA.items():
        # Verificar keywords da macro-tese
        if any(kw in nome_lower for kw in config["keywords"]):
            # Tentar identificar precedente específico
            for precedente, prec_keywords in config["precedentes"].items():
                if any(pk in nome_lower for pk in prec_keywords):
                    return macro_tese, precedente
            # Se não encontrou precedente específico, usar genérico
            return macro_tese, "GERAL"
    
    return "NAO_CLASSIFICADO", "TRIAGEM"


def gerar_novo_nome(nome_original: str, macro_tese: str, precedente: str) -> str:
    """Gera nome seguindo convenção [TESE]_[PRECEDENTE]_[NOME_ORIGINAL]."""
    # Limpar nome original
    nome_limpo = re.sub(r'[^\w\s.-]', '', nome_original)
    nome_limpo = re.sub(r'\s+', '_', nome_limpo)
    
    # Se já segue a convenção, não modificar
    if nome_limpo.startswith(f"{macro_tese}_"):
        return nome_original
    
    return f"{macro_tese}_{precedente}_{nome_limpo}"


def listar_arquivos_drive(config_path: str, remote: str, pasta: str) -> List[str]:
    """Lista arquivos de uma pasta do Drive."""
    cmd = f"rclone lsf '{remote}:{pasta}' --config {config_path} -R 2>/dev/null"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]


def criar_estrutura_taxonomica(config_path: str, remote: str, base_path: str = ""):
    """Cria estrutura de pastas seguindo taxonomia."""
    for macro_tese, config in TAXONOMIA.items():
        # Criar pasta da macro-tese
        pasta_macro = f"{base_path}/{macro_tese}" if base_path else macro_tese
        cmd = f"rclone mkdir '{remote}:{pasta_macro}' --config {config_path}"
        subprocess.run(cmd, shell=True)
        
        # Criar subpastas de precedentes
        for precedente in config["precedentes"].keys():
            pasta_prec = f"{pasta_macro}/{precedente}"
            cmd = f"rclone mkdir '{remote}:{pasta_prec}' --config {config_path}"
            subprocess.run(cmd, shell=True)
        
        # Criar pasta GERAL para casos sem precedente específico
        cmd = f"rclone mkdir '{remote}:{pasta_macro}/GERAL' --config {config_path}"
        subprocess.run(cmd, shell=True)


def mover_arquivo(config_path: str, remote: str, origem: str, destino: str):
    """Move arquivo no Drive."""
    cmd = f"rclone moveto '{remote}:{origem}' '{remote}:{destino}' --config {config_path}"
    return subprocess.run(cmd, shell=True, capture_output=True)


def gerar_relatorio(classificacoes: List[Dict]) -> str:
    """Gera relatório de classificação em Markdown."""
    relatorio = "# Relatório de Reorganização\n\n"
    relatorio += "## Resumo\n\n"
    
    # Contagem por macro-tese
    contagem = {}
    for c in classificacoes:
        tese = c["macro_tese"]
        contagem[tese] = contagem.get(tese, 0) + 1
    
    relatorio += "| Macro-Tese | Quantidade |\n"
    relatorio += "|------------|------------|\n"
    for tese, qtd in sorted(contagem.items()):
        relatorio += f"| {tese} | {qtd} |\n"
    
    relatorio += "\n## Detalhamento\n\n"
    for c in classificacoes:
        relatorio += f"- **{c['arquivo_original']}**\n"
        relatorio += f"  - Macro-Tese: {c['macro_tese']}\n"
        relatorio += f"  - Precedente: {c['precedente']}\n"
        relatorio += f"  - Destino: {c['destino']}\n\n"
    
    return relatorio


def main():
    parser = argparse.ArgumentParser(description="Organiza Drive com taxonomia temática")
    parser.add_argument("--config", required=True, help="Caminho do arquivo rclone.ini")
    parser.add_argument("--remote", required=True, help="Nome do remote (ex: manus_google_drive)")
    parser.add_argument("--pasta", default="", help="Pasta origem para reorganizar")
    parser.add_argument("--destino", default="ARQUIVO_TEMATICO", help="Pasta base destino")
    parser.add_argument("--dry-run", action="store_true", help="Apenas simular, não mover")
    
    args = parser.parse_args()
    
    print(f"Iniciando reorganização de: {args.pasta or 'raiz'}")
    print(f"Destino base: {args.destino}")
    
    # Criar estrutura taxonômica
    if not args.dry_run:
        print("Criando estrutura de pastas...")
        criar_estrutura_taxonomica(args.config, args.remote, args.destino)
    
    # Listar arquivos
    arquivos = listar_arquivos_drive(args.config, args.remote, args.pasta)
    print(f"Encontrados {len(arquivos)} arquivos")
    
    classificacoes = []
    for arquivo in arquivos:
        if arquivo.endswith('/'):  # Ignorar pastas
            continue
        
        macro_tese, precedente = classificar_arquivo(arquivo)
        novo_nome = gerar_novo_nome(arquivo, macro_tese, precedente)
        destino = f"{args.destino}/{macro_tese}/{precedente}/{novo_nome}"
        
        classificacao = {
            "arquivo_original": arquivo,
            "macro_tese": macro_tese,
            "precedente": precedente,
            "novo_nome": novo_nome,
            "destino": destino
        }
        classificacoes.append(classificacao)
        
        if not args.dry_run:
            origem_completa = f"{args.pasta}/{arquivo}" if args.pasta else arquivo
            print(f"Movendo: {arquivo} -> {destino}")
            mover_arquivo(args.config, args.remote, origem_completa, destino)
    
    # Gerar relatório
    relatorio = gerar_relatorio(classificacoes)
    print("\n" + relatorio)
    
    # Salvar relatório
    with open("relatorio_reorganizacao.md", "w") as f:
        f.write(relatorio)
    print("Relatório salvo em: relatorio_reorganizacao.md")


if __name__ == "__main__":
    main()
