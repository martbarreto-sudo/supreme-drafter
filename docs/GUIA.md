# Guia de Configuração e Uso do Claude Code

Este guia orienta a instalação, a autenticação e a operação do Claude Code em ambientes de desenvolvimento.

> Conferido contra a documentação oficial em 03/10/2026. Comandos e requisitos mudam entre versões: em caso de divergência, prevalece a documentação (links na seção 6).

## 1. Requisitos

### Conta

O Claude Code exige uma das seguintes contas:

- Claude Pro, Max, Team ou Enterprise
- Claude Console (API)

O plano gratuito do claude.ai não inclui acesso ao Claude Code.

Também é possível usar um provedor de terceiros: Amazon Bedrock, Google Cloud's Agent Platform ou Microsoft Foundry.

### Sistema

- macOS 13.0+, Windows 10 1809+ (ou Windows Server 2019+), Ubuntu 20.04+, Debian 10+ ou Alpine Linux 3.19+
- 4 GB de RAM ou mais, processador x64 ou ARM64
- Conexão com a internet
- Node.js não é necessário para a instalação nativa

## 2. Instalação nativa

Abra o terminal. Não é necessário executá-lo como Administrador.

### macOS / Linux / WSL

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

### Windows (PowerShell)

```powershell
irm https://claude.ai/install.ps1 | iex
```

### Windows (CMD)

```batch
curl -fsSL https://claude.ai/install.cmd -o install.cmd && install.cmd && del install.cmd
```

No Windows nativo, o Git for Windows é recomendado: com ele, o Claude Code usa a ferramenta Bash. Sem ele, os comandos de shell rodam via PowerShell.

### Verificação

Abra uma nova janela de terminal e execute:

```bash
claude --version
```

Uma instalação íntegra imprime o número da versão. Para um diagnóstico mais completo:

```bash
claude doctor
```

## 3. Autenticação

1. No terminal, navegue até o diretório do projeto.
2. Inicie a ferramenta:

   ```bash
   claude
   ```

3. No primeiro acesso, siga as instruções de login no navegador.

### Chaves de API

- A chave é criada pelo titular da conta no Claude Console. Nenhum assistente a gera.
- Guarde a chave apenas em variável de ambiente ou em gerenciador de segredos.
- Nunca insira a chave em chat, código-fonte, logs ou frontend.
- Se a variável `ANTHROPIC_API_KEY` estiver definida, o Claude Code pede uma única aprovação da chave no terminal, em vez de abrir o navegador.

## 4. Comandos essenciais

Os comandos abaixo são digitados dentro da sessão interativa, sempre no início da mensagem:

| Comando | Função |
|---|---|
| `/init` | Inicializa o projeto e gera o arquivo `CLAUDE.md`. |
| `/plan` | Entra em modo de planejamento antes de uma alteração grande. Aceita uma descrição opcional, por exemplo `/plan corrigir o bug de autenticação`. |
| `/rewind` | Retrocede a conversa, o código ou ambos a um ponto de verificação anterior. |
| `/compact` | Resume a conversa para liberar contexto. |
| `/doctor` | Diagnostica problemas de instalação e configuração. |

Limite do `/rewind`: edições feitas por uma skill que roda em segundo plano (`context: fork`) ficam fora dos pontos de verificação. Para revertê-las, use o git.

### Modo não interativo

Para scripts e pipelines:

```bash
claude -p "Sua instrução aqui"
```

## 5. Skills customizadas

Uma skill é um conjunto de instruções que o Claude carrega sob demanda ou que você invoca com `/nome-da-skill`.

### Onde salvar

| Escopo | Caminho |
|---|---|
| Projeto (versionada com o repositório) | `.claude/skills/nome-da-skill/SKILL.md` |
| Pessoal (todos os seus projetos na máquina) | `~/.claude/skills/nome-da-skill/SKILL.md` |

### Estrutura do `SKILL.md`

O arquivo tem um cabeçalho YAML delimitado por `---` e, em seguida, as instruções em Markdown. O `---` de abertura deve estar na primeira linha do arquivo.

```yaml
---
name: revisar-codigo
description: Analisa um arquivo em busca de problemas de legibilidade. Use quando o usuário pedir revisão de nomenclatura ou de tamanho de funções.
disable-model-invocation: true
allowed-tools: Read Grep
---

## Instruções

Analise o arquivo indicado pelo usuário e aponte melhorias de nomenclatura e de tamanho de funções.
```

Invocação: `/revisar-codigo`.

Campos usados no exemplo:

- `description`: informa ao Claude o que a skill faz e quando usá-la.
- `disable-model-invocation: true`: somente o usuário invoca a skill; o Claude não a aciona por conta própria.
- `allowed-tools`: ferramentas que o Claude pode usar sem pedir confirmação. Liste apenas o mínimo necessário. Um `Bash` sem escopo libera qualquer comando de shell; se precisar de shell, restrinja o padrão, por exemplo `Bash(git status *)`.

Revise o `allowed-tools` de skills versionadas em um repositório antes de rodar o Claude Code nele: a concessão se aplica mesmo em pastas que você ainda não marcou como confiáveis.

### Comportamento das skills

- **Persistência:** ao ser invocada, a skill entra na conversa como uma única mensagem e permanece nos turnos seguintes. O arquivo não é relido a cada turno.
- **Permissões:** a concessão de `allowed-tools` vale apenas no turno que invocou a skill e é limpa quando o usuário envia a próxima mensagem.
- **Compactação:** após a compactação, o Claude Code reanexa a invocação mais recente de cada skill, limitada aos primeiros 5.000 tokens de cada uma, com teto combinado de 25.000 tokens. O teto é preenchido da skill mais recente para a mais antiga, de modo que skills antigas podem ser descartadas. Por isso, coloque as instruções mais importantes no início do `SKILL.md` e invoque a skill de novo se o Claude deixar de segui-la.

## 6. Referências

- Instalação e requisitos: https://code.claude.com/docs/en/setup
- Comandos: https://code.claude.com/docs/en/commands
- Skills: https://code.claude.com/docs/en/skills
