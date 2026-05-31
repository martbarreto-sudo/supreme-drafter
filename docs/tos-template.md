# Termos de Uso — Nexus by Tigre (TEMPLATE)

> **STATUS: rascunho técnico para você redigir com advogado(a).**
>
> Este arquivo lista os pontos que o TOS final precisa cobrir, com sugestão
> de linguagem. **Não é o TOS pronto.** Antes de qualquer usuário aceitar,
> precisa de revisão jurídica por especialista em direito digital + OAB.
>
> Versão atual do TOS no código: **1** (constante `TOS_VERSION_ATUAL` em
> `engine/src/nexus/legal/disclaimer.py`). Quando você publicar a versão
> definitiva, incremente para 2 ou superior; usuários existentes
> precisarão re-aceitar.

---

## 1. Cláusula de qualificação do contratante

> "Ao se cadastrar na plataforma Nexus by Tigre, o(a) USUÁRIO(A) declara,
> sob as penas da lei:
> 
> (a) ser pessoa natural maior e capaz, advogado(a) regularmente inscrito(a)
>     na Ordem dos Advogados do Brasil, com inscrição ativa na seccional
>     informada no cadastro;
> 
> (b) estar atuando no exercício regular da advocacia, dentro dos limites
>     éticos do Estatuto da OAB (Lei 8.906/94) e do Código de Ética e
>     Disciplina da OAB;
> 
> (c) ser o(a) único(a) responsável técnico(a) por toda e qualquer peça
>     jurídica gerada com auxílio da plataforma, devendo revisá-la
>     integralmente antes de protocolá-la sob sua assinatura."

## 2. Natureza do serviço (CRUCIAL para enquadramento OAB)

> "A plataforma Nexus by Tigre é exclusivamente uma **ferramenta de
> produtividade computacional**. Não exerce advocacia, não emite parecer
> jurídico, não substitui análise técnica humana, não responde por decisões
> processuais.
> 
> Toda peça gerada constitui **minuta de trabalho** sujeita à revisão,
> ajuste e assinatura do(a) advogado(a)-operador(a) cadastrado(a),
> que assume integral responsabilidade técnica perante o cliente, o juízo
> e a OAB."

## 3. Limites de uso

> "É vedado ao(à) USUÁRIO(A):
> 
> (a) usar a plataforma para captar clientela em violação ao art. 5º do
>     Código de Ética da OAB;
> 
> (b) compartilhar suas credenciais de acesso com terceiros, incluindo
>     estagiários, sócios ou clientes;
> 
> (c) inserir na plataforma dados pessoais de terceiros sem amparo legal
>     ou consentimento (art. 7º da LGPD);
> 
> (d) utilizar a plataforma para gerar peças em causas em que esteja
>     impedido(a) ou suspenso(a)."

## 4. Modelo comercial

> "O serviço é prestado mediante assinatura mensal recorrente, com volume
> de peças incluído conforme plano contratado. A cobrança é feita via
> Stripe; falha de pagamento suspende o acesso conforme cláusula §X."

(Definir: planos, valores, condições de upgrade/downgrade/cancelamento.)

## 5. Trial gratuito

> "O cadastro inicial concede acesso por 14 (catorze) dias corridos, com
> direito a até 3 (três) peças geradas. Após o término do trial, o acesso
> é interrompido até a contratação de plano pago."

## 6. Privacidade e LGPD

Remeter à Política de Privacidade (`docs/lgpd.md`) e reproduzir os pontos
essenciais:
- Que dados são coletados
- Para que são usados
- Direitos do titular (art. 18 LGPD)
- Tempo de retenção
- Encarregado/DPO

## 7. Propriedade intelectual

> "O motor analítico, os prompts proprietários, o protocolo doutrinário, a
> base de vulnerabilidades catalogadas e demais componentes técnicos da
> plataforma são de propriedade exclusiva do CONTRATANTE.
> 
> Os textos das peças geradas são de uso livre pelo(a) advogado(a) que
> as gerou, no exercício de suas atividades profissionais."

## 8. Limitação de responsabilidade

> "A plataforma não responde por:
> 
> (a) decisões processuais tomadas com base em minutas geradas;
> 
> (b) resultados de causas, defesas ou recursos;
> 
> (c) prazos perdidos por falha de revisão humana;
> 
> (d) consequências de divulgação não autorizada de dados sigilosos pelo(a)
>     USUÁRIO(A);
> 
> (e) interrupções decorrentes de manutenção programada ou eventos de
>     força maior."

## 9. Suporte e SLA

(Definir: canais de suporte, tempo médio de resposta, escalonamento.)

## 10. Foro

> "Para qualquer questão decorrente deste contrato, fica eleito o Foro da
> Comarca de Recife/PE, com renúncia expressa a qualquer outro, por mais
> privilegiado que seja."

## 11. Aceite

> "Ao clicar em 'Aceito os Termos de Uso e a Política de Privacidade', o
> USUÁRIO declara ter lido, compreendido e concordado com este instrumento.
> O aceite eletrônico é registrado com data, hora UTC e versão deste TOS,
> nos termos do art. 5º, II do Código Civil e do Marco Civil da Internet."

---

## Bandeiras vermelhas que o advogado(a) revisor(a) deve confirmar

1. Enquadramento como "ferramenta de produtividade", não consultoria —
   precisa estar inequívoco para sobreviver à OAB.
2. Responsabilidade técnica integralmente do advogado-operador OAB.
3. Cláusula de uso vedado para captação (art. 5º Cód. Ética).
4. Compatibilidade da estrutura de cobrança com regras de honorário (não
   pode parecer com "consulta jurídica avulsa").
5. Conformidade com LGPD em todos os pontos do tratamento de dados.
6. Mecanismo de evidência de aceite (data + hora + versão) — já
   implementado: ver `User.tos_aceito_em` e `User.tos_version`.

## Quando re-aceite é necessário

Mudanças que **EXIGEM** re-aceite:
- Mudança de modelo de negócio
- Inclusão de novos compartilhamentos de dados
- Mudança de base legal para tratamento
- Mudança de operadores subcontratados relevantes (ex: trocar Anthropic)

Mudanças cosméticas (correção de typo, melhor redação) podem manter a versão.
