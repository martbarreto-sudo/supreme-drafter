# Política de Privacidade — Nexus by Tigre

> **Aviso:** este documento é a **proposta operacional** do que a plataforma
> coleta, armazena e processa. **Antes de publicar** em produção, deve ser
> revisado por advogado(a) especialista em LGPD e ajustado às cláusulas
> exigidas pela ANPD. Considere como **rascunho técnico**, não documento
> jurídico final.

## 1. Controlador dos dados

Operador legal a definir (provavelmente Ribeiro & Tigre Advocacia ou pessoa
jurídica específica da Nexus). DPO/Encarregado a nomear.

Contato para tratativas LGPD: `lgpd@<dominio>` (a configurar).

## 2. Que dados coletamos

### 2.1. Dados de identificação do advogado-operador (titular)

- Nome
- E-mail (utilizado como login)
- Número OAB + UF
- Senha (armazenada como hash bcrypt, jamais em texto plano)
- Data e versão do TOS aceito

**Base legal:** execução de contrato (art. 7º, V LGPD) — necessários para
prover o serviço contratado.

### 2.2. Dados de uso

- Histórico de peças geradas (metadados: data, tipo de peça, quality score,
  modelo LLM utilizado, contagem de tokens)
- Texto das peças geradas (armazenado em disco, isolado por usuário)
- Logs de assinatura (status, plano, períodos)
- Logs de pagamento (ID Stripe, valor, status, data)

**Base legal:** execução de contrato + obrigação legal (art. 7º, II) para
registros financeiros.

### 2.3. Dados dos autos enviados

Quando o advogado-operador faz upload de PDF dos autos via `/autos`:

- Calculamos hash SHA-256 do arquivo (identificador único)
- Armazenamos o PDF em diretório isolado por `user_id`
- **Não** processamos o conteúdo via LLM no upload — apenas geramos o
  identificador `hash://` que ancora o Dado Líquido

**Conteúdo dos autos pode conter dados pessoais de terceiros** (réus,
vítimas, testemunhas, etc.). O advogado-operador é o **controlador** desses
dados; a Nexus atua como **operador** processando-os a pedido dele
(art. 5º, VII LGPD).

## 3. Para que usamos os dados

- Prover o serviço de geração de minutas jurídicas para o advogado-operador
- Cobrar pelo serviço (via Stripe)
- Calcular cota mensal de peças do plano
- Auditoria interna de custo (tokens LLM vs cobrança)
- Resposta a obrigações legais (fiscal, ordem judicial específica)

**Não usamos para:**
- Marketing externo
- Treinamento de modelos LLM (Anthropic API com prompt caching, sem opt-in
  para treino)
- Cessão a terceiros (exceto Stripe para processamento de pagamento e
  Anthropic para geração — operadores subcontratados)

## 4. Com quem compartilhamos

- **Anthropic** (geração de minutas) — texto da requisição é enviado ao
  modelo Claude. Por contrato Anthropic, dados de API não são usados para
  treinar modelos.
- **Stripe** (pagamentos) — apenas dados de pagamento (e-mail, valor,
  método de pagamento processado pela Stripe). PCI compliance é da Stripe.
- **Plataforma de hospedagem** (Railway, no MVP) — todos os dados em
  trânsito e em repouso passam pela infraestrutura do provedor.

## 5. Tempo de retenção

| Categoria | Retenção | Após anonimização? |
|---|---|---|
| Conta ativa | enquanto durar | — |
| Conta encerrada (DELETE /user/me) | imediato | Sim, PII removida |
| Textos das minutas | enquanto conta ativa | Removidos no DELETE |
| Pagamentos | mínimo 5 anos (fiscal) | Permanecem anonimizados |
| Logs de auditoria | 12 meses | — |

## 6. Direitos do titular (LGPD art. 18)

### Implementados no MVP

- **Acesso (art. 18 II):** `GET /user/me/export` retorna JSON com todos os
  dados pessoais armazenados.
- **Exclusão / anonimização (art. 18 VI):** `DELETE /user/me` anonimiza a
  conta imediatamente, mantendo apenas registros financeiros (obrigação
  legal) sem PII.

### A implementar (Fase G)

- **Correção:** PATCH /user/me (atualização de e-mail, nome, OAB)
- **Portabilidade estruturada:** export com schema padronizado
- **Confirmação de tratamento:** endpoint informando categorias e bases legais
- **Oposição:** opt-out de processamentos específicos (a definir)

## 7. Segurança

- Senhas: bcrypt (custo padrão 12)
- Comunicação: HTTPS obrigatório em produção (TLS terminado pelo provedor)
- Tokens JWT: HS256 com secret de ≥ 32 chars; expiração 15 min
- Webhooks Stripe: assinatura HMAC validada (`STRIPE_WEBHOOK_SECRET`)
- Rate limiting: 5/min em /auth/login, 3/min em /auth/signup
- Isolamento por usuário: arquivos em `CASO_DATA_DIR/{user_id}/...`

## 8. Incidente com dados pessoais

Em caso de incidente que envolva risco aos titulares, notificaremos:
- A ANPD em prazo razoável (a definir — 72h é prática padrão)
- Os titulares afetados quando o risco for relevante

Procedimento de resposta a incidentes (a definir) deve cobrir: detecção,
contenção, comunicação, investigação, mitigação, lições aprendidas.

## 9. Mudanças nesta política

Versão atual: **1**. Mudanças materiais incrementam a versão e podem exigir
re-aceite do TOS pelo usuário.

## 10. O que esta política não cobra

- **Conduta do advogado-operador** com dados de seus clientes —
  responsabilidade dele perante OAB, LGPD e o cliente final.
- **Decisões jurídicas** baseadas em minutas geradas — sempre humanas, do
  advogado-operador OAB.
- **Conteúdo das minutas** geradas — síntese estatística do modelo LLM, não
  parecer jurídico da plataforma.
