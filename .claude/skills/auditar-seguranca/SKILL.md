---
name: auditar-seguranca
description: Auditoria estática, somente leitura, contra vazamento de credenciais e riscos de cadeia de suprimentos em workflows e dependências. Use quando o usuário pedir revisão de segurança do repositório ou antes de um commit.
disable-model-invocation: true
allowed-tools: Read Grep Glob Bash(git ls-files *) Bash(git diff --name-only *)
---

# Auditoria de segurança e conformidade

Escopo pedido pelo usuário: $ARGUMENTS

Sem escopo informado, audite o repositório inteiro. Com `alterados`, audite só os arquivos de `git diff --name-only HEAD`.

## Regras de execução

1. Somente leitura. Não edite, não crie arquivos e não corrija nada sem instrução expressa do usuário.
2. Nunca reproduza o valor de um segredo. Cite `arquivo:linha` e, no máximo, os 4 primeiros caracteres seguidos de `…`.
3. O relatório é sensível: descreve brechas ainda abertas. Entregue-o só na conversa. Não o publique em PR, issue ou commit de repositório público.
4. Não encerre com erro nem interrompa a tarefa por causa de um achado. Todo achado vai para o relatório.
5. Afirme só o que leu. O que não puder ser verificado estaticamente vai para a seção "Não verificado", marcado `[CONFERIR]`.

## Onde procurar

Liste os arquivos versionados com `git ls-files --cached` e priorize:

- `.github/workflows/` e `.github/scripts/`
- workflows aninhados fora da raiz (ex.: `services/runtime/.github/workflows/`): o GitHub não os executa; registre isso como achado
- `.env*`, `*.json`, `*.yaml`, `*.yml`, `docker-compose*`, `Dockerfile*`, charts em `deploy/helm/`
- manifestos de dependência: `requirements*.txt`, `package.json`, `package-lock.json`, `pyproject.toml`
- código: `nexum_engine/`, `services/`, `tools/`, `public/`
- `.gitignore`

## Verificações

### 1. Credenciais

- Arquivos sensíveis versionados: `.env*`, `*.pem`, `*.key`, `*.p12`, `*.pfx`, `id_rsa*`, `credentials*.json`, `.npmrc`, `.pypirc`, `.netrc`.
- Tokens por formato (Grep em todo o repositório):

  ```
  sk-ant-[A-Za-z0-9_-]{10,}|AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{35}|gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|xox[baprs]-[A-Za-z0-9-]{10,}|-----BEGIN [A-Z ]*PRIVATE KEY
  ```

- Atribuição literal a nomes como `API_KEY`, `SECRET`, `PASSWORD`, `TOKEN`, `SENHA`. Placeholders evidentes (`sua_chave`, `changeme`, `<...>`) contam como OK.
- `.gitignore` cobre `.env*`, chaves privadas e arquivos de credencial?
- `public/` e qualquer frontend: nenhuma chave, nenhum cabeçalho `Authorization` fixo.
- Scripts não imprimem variáveis de ambiente de credenciais em log.

### 2. Workflows do GitHub Actions

- **Código não confiável com privilégio.** Para cada gatilho `pull_request_target`, `issue_comment` ou `workflow_run`: o job faz checkout do head de um PR e depois executa código ou instala dependências desse checkout? Há `secrets.*`, token com escrita ou `id-token: write` ao alcance desses passos? Existe filtro de autor (`author_association` ou equivalente) antes?
- **Injeção em `run:`.** Expressões `${{ ... }}` com dados controláveis por terceiros (título, corpo, comentário, nome de branch ou de arquivo, saídas derivadas deles) interpoladas direto no script, em vez de passadas por `env:`.
- **Fixação de actions.** Cada `uses:` aponta para SHA de 40 caracteres ou para tag mutável (`@v4`)? Liste primeiro as actions de terceiros e as que rodam em jobs com escrita ou segredo.
- **Permissões.** Bloco `permissions` ausente, ou mais amplo que o necessário para o job.
- **Segredo em trânsito.** Token embutido em URL de clone, gravado em disco ou repassado a passos que não precisam dele.

### 3. Dependências e instalação

- `curl ... | sh`, `wget ... | sh` e equivalentes.
- `pip install`, `npm install`, `npx`, `apt-get install` sem versão fixa.
- `requirements*.txt` com `>=` ou sem versão, sem hashes; `npm install` onde existe `package-lock.json` (o correto é `npm ci`).
- Imagens em `FROM` e `image:` sem digest; uso de `latest`.

## Severidade

- **[CRÍTICO]** Segredo real em arquivo versionado, ou caminho pelo qual alguém sem permissão de escrita no repositório executa código com acesso a segredo, token de escrita ou OIDC.
- **[AVISO]** Endurecimento preventivo: tags mutáveis, versões soltas, permissões largas, `.gitignore` incompleto, credenciais padrão de ambiente de desenvolvimento.
- **[OK]** Item verificado, sem achado.

## Formato do relatório

Uma linha de resumo com a contagem por severidade e, em seguida:

| Severidade | Local | Achado | Correção sugerida |
|---|---|---|---|

Ordene por severidade. Em "Local", use `arquivo:linha`. Feche com a seção **Não verificado**, listando o que depende de configuração fora do repositório (segredos cadastrados, configurações de Actions, IAM de nuvem).
