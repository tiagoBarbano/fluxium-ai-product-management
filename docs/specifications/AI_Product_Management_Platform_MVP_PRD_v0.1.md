# PRD - Fluxium AI Product Management MVP

**Versão:** 0.1  
**Data:** 2026-09-18  
**Status:** Proposta para validação  
**Fonte de contexto:** `AI_Product_Management_Platform_Especificacao_v0.1.txt`

## 1. Resumo

O MVP deve ajudar equipes de produto a transformar uma oportunidade pouco
estruturada em uma Initiative suficientemente compreendida para ser discutida,
priorizada e aprovada para o próximo estágio.

O fluxo central é:

```text
Workspace
  -> Product
  -> Opportunity
  -> Discovery
  -> Problem
  -> Evidence
  -> Hypothesis
  -> Initiative
  -> Product Readiness
  -> Aprovação humana
```

O MVP não substitui ferramentas de delivery. Seu objetivo é preservar contexto,
expor lacunas e apoiar decisões de Product Management com IA explicável.

## 2. Problema

Informações de produto normalmente estão dispersas em conversas, documentos,
chamados e ferramentas de delivery. Isso dificulta responder:

- qual problema está sendo resolvido;
- para quem o problema existe;
- quais evidências sustentam a oportunidade;
- qual hipótese está sendo testada;
- como medir valor;
- se a iniciativa está preparada para avançar.

A IA deve acelerar a descoberta, mas não pode inventar requisitos, evidências,
dados ou decisões.

## 3. Objetivo do MVP

Validar se o Fluxium consegue transformar uma entrada inicial simples em uma
Initiative estruturada, com lacunas visíveis, avaliação de Product Readiness e
aprovação humana auditável.

### 3.1 Resultados esperados

1. Uma oportunidade pode ser registrada em poucos passos.
2. A Discovery conduz perguntas relevantes e adaptativas.
3. O usuário consegue registrar problema, público, evidências e hipótese.
4. Uma Initiative reúne contexto, objetivo, escopo e resultado esperado.
5. O sistema explica por que uma Initiative está ou não pronta.
6. Sugestões da IA podem ser aceitas ou rejeitadas pelo usuário.
7. O histórico das alterações e avaliações permanece disponível.

### 3.2 Modelo de gestão adotado

O MVP utilizará padrões de Product Management já conhecidos, sem transformar o
Fluxium em uma ferramenta genérica de planejamento corporativo:

| Conceito | Papel no Fluxium | Momento da jornada |
|---|---|---|
| OKR | Contexto estratégico com um ou mais Objectives; cada Objective possui um ou mais Key Results | Antes ou durante a Initiative |
| Business Problem (BP) | Problema de negócio observável, com público, impacto e evidências | Discovery |
| Opportunity | Possibilidade de intervenção derivada de um BP | Após a identificação do problema |
| Initiative | Unidade de decisão e investimento relacionada ao BP e ao OKR | Após Discovery |
| 5W2H | Estrutura operacional opcional da Initiative: What, Why, Where, When, Who, How e How Much | Initiative / Business Plan |
| Business Plan | Visão consolidada da Initiative, seu racional, plano 5W2H, riscos e métricas | Após a Initiative, antes do avanço |

No MVP, Business Plan será uma visão estruturada da Initiative, e não um módulo
financeiro ou de orçamento completo. O 5W2H deve organizar a decisão, mas não
substitui Delivery, Roadmap ou gestão de tarefas.

## 4. Usuários e permissões

### 4.1 Personas

| Persona | Necessidade principal |
|---|---|
| Product Manager | Estruturar oportunidades e tomar decisões de produto |
| Product Owner | Refinar escopo e preparar a iniciativa para execução |
| Contributor | Contribuir com evidências, hipóteses e informações |
| Viewer | Consultar contexto e avaliações sem alterar dados |
| Admin | Administrar workspace, membros e configurações |

### 4.2 Papéis do MVP

- `ADMIN`: gerencia workspace, membros e configurações.
- `PRODUCT_MANAGER`: cria, edita, avalia e aprova artefatos de produto.
- `CONTRIBUTOR`: cria e complementa dados permitidos no Discovery.
- `VIEWER`: acesso somente leitura.

Somente `ADMIN` e `PRODUCT_MANAGER` podem aprovar propostas geradas pela IA.

A matriz definitiva de permissões por campo e transição permanece como ponto de
validação antes da implementação.

## 5. Escopo funcional

### 5.1 Organização e workspace

O sistema deve permitir trabalhar dentro de um workspace isolado. Todas as
entidades do MVP devem estar associadas ao workspace e não podem ser acessadas
por usuários sem autorização.

### 5.2 Product

O usuário autorizado deve poder:

- criar um Product;
- informar nome, descrição e visão;
- visualizar Products do workspace;
- consultar as oportunidades e iniciativas relacionadas.

### 5.3 Opportunity

O usuário deve poder criar uma oportunidade com uma entrada simples:

> O que você está tentando melhorar?

Campos mínimos:

- título;
- descrição;
- Product;
- origem;
- autor;
- status;
- datas de criação e atualização.

Estados:

```text
NEW -> DISCOVERY
DISCOVERY -> QUALIFIED
DISCOVERY -> REJECTED
QUALIFIED -> CONVERTED
```

Uma Opportunity pode gerar uma ou mais Initiatives. A conversão não deve
apagar o histórico da oportunidade.

### 5.4 Discovery Session

O sistema deve permitir iniciar uma sessão de Discovery associada a uma
Opportunity. A sessão deve preservar mensagens, perguntas, respostas e
informações estruturadas identificadas.

Perguntas sugeridas:

- Quem tem o problema?
- Qual é o problema observado?
- Quando ele acontece?
- Qual é o impacto?
- Existe evidência?
- Como o resultado será medido?
- Qual comportamento ou resultado é esperado?

A IA deve adaptar as perguntas conforme as informações já disponíveis. Ela não
deve preencher campos sem evidência fornecida pelo usuário ou por uma fonte
importada explicitamente.

### 5.5 Problem

O usuário deve poder registrar um problema relacionado à Opportunity e ao
Product, contendo no mínimo:

- descrição;
- público afetado;
- impacto informado;
- evidências relacionadas;
- status.

O impacto informado pelo usuário deve ser distinguido de impacto estimado pela
IA.

### 5.6 Evidence

O usuário deve poder registrar evidências que sustentem problema, hipótese ou
decisão.

Tipos iniciais:

- entrevista;
- analytics;
- SAC;
- pesquisa;
- documento;
- experimento;
- dado operacional;
- feedback de cliente.

Cada evidência deve registrar sua origem e se foi declarada manualmente ou
observada/importada pelo sistema. O MVP não deve afirmar que uma evidência é
confiável sem informação que sustente essa classificação.

### 5.7 Hypothesis

O usuário deve poder registrar uma hipótese com:

- afirmação;
- comportamento esperado;
- resultado esperado;
- evidências relacionadas;
- confiança;
- status.

Estados:

```text
DRAFT
TESTING
VALIDATED
INVALIDATED
ABANDONED
```

A confiança deve ser apresentada como estimativa, nunca como certeza.

### 5.8 Initiative

A Initiative é a unidade principal de planejamento do MVP. Deve reunir:

- título;
- Product;
- Opportunity relacionada;
- Problem relacionada;
- objetivo;
- hipótese;
- resultado esperado;
- escopo;
- fora de escopo;
- evidências;
- KPIs ou forma de medição;
- um ou mais Objectives de OKR, cada um com um ou mais Key Results;
- plano 5W2H opcional, quando aplicável;
- dependências e riscos informados;
- status;
- versão;
- autor e datas.

Estados do MVP:

```text
DRAFT -> DISCOVERY
DISCOVERY -> READY_FOR_PRIORITIZATION
READY_FOR_PRIORITIZATION -> PRIORITIZED
PRIORITIZED -> READY_FOR_DELIVERY
READY_FOR_DELIVERY -> CANCELLED
```

Os estados `IN_DELIVERY`, `READY_FOR_RELEASE`, `RELEASED`, `MEASURING` e
`COMPLETED` ficam fora do MVP e serão tratados no módulo de Delivery/Outcomes.

### 5.9 Product Readiness

O sistema deve avaliar se a Initiative possui informação suficiente para
avançar.

Dimensões iniciais:

| Dimensão | Peso proposto |
|---|---:|
| Problem | 15% |
| Evidence | 15% |
| Hypothesis | 10% |
| Value | 15% |
| KPI | 10% |
| Scope | 15% |
| UX | 10% |
| Technical Discovery | 10% |

O resultado deve incluir:

- score entre 0 e 100;
- score por dimensão;
- justificativas;
- informações ausentes;
- perguntas abertas;
- confiança da avaliação;
- versão do contexto avaliado;
- data, provider, modelo e versão do prompt.

Os pesos, o score mínimo para `READY_FOR_DELIVERY` e a obrigatoriedade de UX e
Technical Discovery ainda precisam de validação do Product Owner.

### 5.10 OKR

O sistema deve permitir cadastrar e relacionar mais de um Objective ao contexto
de Product ou Initiative. Cada Objective deve permitir cadastrar um ou mais Key
Results.

Um Objective deve ser qualitativo, inspirador e ambicioso. Um Key Result deve
ser quantitativo, específico, possuir alvo e prazo definido.

### 5.11 Business Plan e 5W2H

O Business Plan deve ser uma visão estruturada da Initiative. Seu bloco 5W2H e
opcional e, quando utilizado, deve permitir cadastrar What, Why, Where, When,
Who, How e How Much.

O Business Plan não inclui tarefas, quadro de delivery, release ou orçamento
financeiro completo no MVP.

## 6. Copilot e IA

### 6.1 Capacidades do MVP

O Copilot poderá:

- fazer perguntas de Discovery;
- resumir contexto existente;
- apontar informações ausentes;
- sugerir melhoria de texto;
- gerar uma avaliação de Product Readiness;
- propor alterações estruturadas.

### 6.2 Limites obrigatórios

A IA não pode:

- alterar o Product Model sem aprovação;
- inventar evidências, métricas, requisitos ou decisões;
- tratar confiança como certeza;
- esconder informação ausente;
- acessar diretamente o banco;
- executar ações externas.

Fluxo de mutação:

```text
IA -> AI Proposal -> Aprovação humana -> Alteração -> Audit Event
```

### 6.3 Resposta mínima da IA

Toda operação relevante de IA deve preservar:

```json
{
  "result": {},
  "confidence": 0.0,
  "missing_information": [],
  "open_questions": [],
  "evidence_refs": [],
  "provider": "",
  "model": "",
  "prompt_version": "",
  "context_version": ""
}
```

O formato definitivo dos schemas será definido no plano de implementação.

## 7. Versionamento e auditoria

Alterações relevantes em Product, Opportunity, Problem, Evidence, Hypothesis e
Initiative devem criar uma nova versão lógica ou registrar snapshot imutável,
conforme decisão técnica posterior.

Um Assessment deve continuar referenciando exatamente o contexto utilizado em
sua execução. Deve ser possível identificar:

- usuário ou processo que alterou o dado;
- versão anterior;
- nova versão;
- data;
- motivo;
- assessment relacionado;
- provider, modelo e prompt quando houver IA.

Assessments são imutáveis. Uma nova avaliação cria um novo registro.

## 8. Fluxo principal

1. Usuário seleciona ou cria um Workspace.
2. Usuário cria ou seleciona um Product.
3. Usuário registra uma Opportunity.
4. Usuário inicia Discovery.
5. Sistema faz perguntas e registra respostas.
6. Usuário confirma Problem, Evidence e Hypothesis.
7. Usuário cria uma Initiative a partir do contexto.
8. Sistema calcula Product Readiness.
9. Usuário revisa lacunas e sugestões.
10. Usuário aprova, corrige ou mantém a Initiative em Discovery.
11. Sistema registra a versão e o evento de auditoria.

## 9. Fluxos alternativos

### 9.1 Informação insuficiente

A IA deve informar `missing_information`, reduzir a confiança e formular uma
pergunta objetiva. Não deve preencher o campo automaticamente.

### 9.2 Sugestão rejeitada

A proposta rejeitada permanece registrada com o resultado da decisão humana,
mas não altera o Product Model.

### 9.3 Conflito de versão

Se o usuário editar uma versão desatualizada, o sistema deve rejeitar a
sobrescrita silenciosa e informar que o conteúdo mudou. O comportamento de
merge ainda precisa ser definido.

### 9.4 Falha do provider de IA

O usuário deve poder continuar a edição manual. A falha deve ser registrada
sem perder o conteúdo já salvo.

### 9.5 Falha de persistência

A alteração não deve ser apresentada como concluída se não tiver sido
persistida. O usuário deve receber uma mensagem acionável e a operação deve
ser rastreável por CorrelationId.

## 10. Requisitos funcionais

### REQ-MVP-001 - Isolamento do workspace

O sistema deve impedir que usuários consultem ou alterem dados fora dos
workspaces autorizados.

**Aceite:** uma tentativa de acesso cruzado retorna erro de autorização ou
recurso inexistente sem revelar dados do workspace protegido.

### REQ-MVP-002 - Gestão de Product

O sistema deve permitir criar, consultar e atualizar Products autorizados.

**Aceite:** Product válido é salvo, aparece no workspace correto e possui
identificação, status e datas.

### REQ-MVP-003 - Registro de Opportunity

O sistema deve permitir registrar uma oportunidade com entrada simples e
relacioná-la a um Product.

**Aceite:** Opportunity válida inicia em `NEW`, pertence ao workspace correto e
mantém autor e timestamps.

### REQ-MVP-004 - Sessão de Discovery

O sistema deve permitir iniciar e continuar uma Discovery associada a uma
Opportunity.

**Aceite:** mensagens e respostas permanecem disponíveis após recarregar a
sessão; perguntas não inventam dados ausentes.

### REQ-MVP-005 - Registro de Problem, Evidence e Hypothesis

O sistema deve permitir criar e relacionar os artefatos de Discovery.

**Aceite:** cada artefato preserva origem, autor, relacionamentos e status;
evidência manual é distinguida de evidência importada/observada.

### REQ-MVP-006 - Criação de Initiative

O sistema deve permitir criar uma Initiative usando o contexto confirmado da
Discovery.

**Aceite:** a Initiative mantém relacionamentos com Opportunity, Problem,
Evidence e Hypothesis e permite definir escopo e fora de escopo.

### REQ-MVP-007 - Product Readiness

O sistema deve gerar uma avaliação explicável da preparação da Initiative.

**Aceite:** o resultado apresenta score, dimensões, justificativas, confiança,
informações ausentes e versão do contexto.

#### Semântica da confiança estimada

O score de Readiness representa a prontidão prevista da Initiative, enquanto a
confiança representa a qualidade e a completude das informações usadas para
produzir a avaliação. Os valores não são intercambiáveis e a confiança não
deve ser apresentada como certeza nem como prontidão real observada.

Para avaliações geradas por IA, a confiança estimada é determinística e fica
limitada ao intervalo `[0,1]`:

```text
confidence = clamp(
    0.40 * provider_confidence
  + 0.30 * context_completeness
  + 0.30 * dimension_completeness
  - min(0.40, 0.05 * missing_information_count)
  - min(0.20, 0.05 * open_questions_count),
  0,
  1
)
```

`context_completeness` considera a presença de contexto da Initiative, do
contexto enviado na solicitação e do conteúdo manual. `dimension_completeness`
considera as oito dimensões com justificativas não vazias. A confiança
declarada pelo provider é apenas um sinal de entrada e não substitui as
validações do domínio. Até existir um resultado observado de execução, o MVP
não calcula calibração entre prontidão prevista e prontidão real; essa medição
fica para uma evolução futura de Outcomes/Product Analytics.

### REQ-MVP-008 - Aprovação humana

O sistema deve permitir aceitar ou rejeitar propostas estruturadas da IA.

**Aceite:** somente uma aprovação autorizada altera o Product Model; rejeição
não altera os dados e ambas as decisões são auditadas. A aprovação deve ser
permitida somente para `ADMIN` e `PRODUCT_MANAGER`.

### REQ-MVP-009 - Versionamento e auditoria

O sistema deve preservar o histórico das alterações e assessments relevantes.

**Aceite:** um assessment antigo continua reproduzível e não é alterado por
edições posteriores.

### REQ-MVP-010 - Operação sem IA

O usuário deve conseguir criar e editar os artefatos principais manualmente
quando a IA estiver indisponível.

**Aceite:** falha ou indisponibilidade do provider não impede salvar conteúdo
manual já validado.

### REQ-MVP-011 - Gestão de OKRs

O sistema deve permitir cadastrar mais de um Objective e relacionar um ou mais
Key Results a cada Objective.

**Aceite:** Objective qualitativo é salvo com seus Key Results quantitativos,
específicos, com alvo e prazo definido, e pode ser associado ao Product ou à
Initiative autorizada.

### REQ-MVP-012 - Business Plan 5W2H opcional

O sistema deve permitir preencher opcionalmente um Business Plan associado à
Initiative, com os campos What, Why, Where, When, Who, How e How Much.

**Aceite:** a Initiative pode ser salva sem 5W2H; quando informado, o conteúdo
fica associado à Initiative, versionado e auditável.

## 11. Requisitos não funcionais

- **NFR-MVP-001:** dados devem ser isolados por organization/workspace.
- **NFR-MVP-002:** alterações importantes devem ser auditáveis.
- **NFR-MVP-003:** operações sem IA devem possuir latência previsível, com meta inicial P95 de até 500 ms, sujeita a validação.
- **NFR-MVP-004:** operações de IA devem possuir timeout, estado de execução e tratamento de falha.
- **NFR-MVP-005:** segredos e credenciais de providers não podem chegar ao frontend.
- **NFR-MVP-006:** API deve ser stateless sempre que possível; sessões de Discovery são persistidas.
- **NFR-MVP-007:** todas as operações relevantes devem preservar CorrelationId e TraceId.
- **NFR-MVP-008:** o sistema deve permitir trocar o provider de IA sem alterar regras do domínio.
- **NFR-MVP-009:** dados e eventos devem utilizar UTC.
- **NFR-MVP-010:** testes devem cobrir regras, erros, isolamento e fluxos críticos.

## 12. Fora do escopo do MVP

- Capabilities e Features como módulos completos.
- Product Graph visual e traversals avançados.
- Impact Analysis e Change Impact.
- Roadmap e priorização avançada.
- Experiments como módulo próprio.
- Integração Jira, GitHub, GitLab e Azure DevOps.
- Delivery, Releases e Outcomes.
- Scope Drift e Delivery Confidence.
- Product Analytics e feedback loop histórico.
- Reverse Product Engineering.
- Execução automática de ações pela IA.
- Múltiplos providers avançados e roteamento sofisticado.

## 13. Critérios de sucesso

O MVP será considerado validado quando equipes piloto conseguirem:

1. registrar uma oportunidade real;
2. concluir uma Discovery com contexto suficiente;
3. gerar uma Initiative estruturada;
4. identificar lacunas antes de avançar;
5. entender a justificativa do Product Readiness;
6. aprovar ou rejeitar sugestões da IA;
7. recuperar o histórico de alterações e avaliações.

As metas quantitativas de adoção, tempo de conclusão, qualidade da avaliação e
redução de retrabalho ainda precisam ser definidas com o Product Owner.

## 14. Dependências e riscos

### Dependências

- mecanismo de autenticação e autorização desenvolvido na plataforma de identidade;
- persistência MongoDB;
- Ollama local para testes iniciais de IA;
- Redis para execução inicial de jobs, com possibilidade de substituição por RabbitMQ;
- observabilidade básica;
- definição dos contratos de IA;
- definição da política de versionamento;
- política de retenção de cinco anos para mensagens, contexto, assessments e auditoria.

### Riscos

- escopo de Discovery crescer além do MVP;
- avaliações de IA parecerem mais precisas do que realmente são;
- versionamento insuficiente para reproduzir assessments;
- baixa qualidade das evidências inseridas;
- custo e latência de chamadas de IA;
- permissões incompletas permitirem vazamento entre workspaces.

## 15. Questões em aberto

1. Qual score mínimo permite avançar para `READY_FOR_DELIVERY`?
2. Os pesos de Product Readiness são definitivos?
3. UX e Technical Discovery serão avaliados no MVP mesmo sem módulos dedicados?
4. O versionamento será por entidade, por agregado ou por snapshot do Product Model?
5. O Product Manager pode excluir dados ou somente arquivá-los?
6. Qual meta de ativação e sucesso deve ser usada no piloto?
7. Qual é o contrato de claims e escopos fornecido pelo provedor de identidade?
8. Quantos ciclos formais de OKR poderão estar ativos por Product em versão futura?

### 15.1 Decisões confirmadas

- A autenticação inicial será integrada ao mecanismo desenvolvido na plataforma de identidade.
- O provider inicial de IA para testes será Ollama local.
- Redis será usado inicialmente para jobs, mantendo possibilidade de substituição por RabbitMQ.
- Mensagens, contexto de Discovery, assessments e auditoria serão retidos por cinco anos.
- Os dados atuais do MVP não são classificados como sensíveis e poderão ser enviados ao Ollama local.
- A operação inicial será local.

## 16. Próxima etapa SDD

Este PRD define o que o MVP deve fazer. Antes da implementação, devem ser
produzidos:

1. `docs/plan/analysis.md` com análise funcional completa;
2. `docs/plan/implementation-plan.md` com arquitetura e contratos técnicos;
3. matriz de rastreabilidade requisito, código e teste;
4. validação das questões em aberto pelo Product Owner.
