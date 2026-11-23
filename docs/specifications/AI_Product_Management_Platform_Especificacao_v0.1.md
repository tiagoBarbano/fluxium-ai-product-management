AI PRODUCT MANAGEMENT PLATFORM
Especificação Funcional e Técnica
Versão 0.1
Data: 2026-09-11

======================================================================
1. VISÃO DO PRODUTO
======================================================================

1.1 Objetivo

Construir uma plataforma AI-first de Product Management que preserve o
contexto de uma iniciativa desde a estratégia e descoberta até o
delivery, release e resultado no mercado.

A plataforma não tem como objetivo substituir a organização de TI,
desenvolvedores, arquitetos ou ferramentas de delivery. Seu objetivo é
acelerar e melhorar o fluxo:

Estratégia -> Oportunidade -> Discovery -> Produto -> Iniciativa ->
Delivery -> Release -> Resultado -> Aprendizado.

1.2 Posicionamento

"Uma plataforma de Product Management com IA que conecta estratégia,
descoberta, delivery e resultados."

Possíveis mensagens de posicionamento:

- Transforme uma ideia em software verificável.
- Da conversa ao software, sem perder o contexto.
- IA mantém o contexto da iniciativa desde a intenção do negócio até
  o resultado no mercado.
- Entenda o impacto antes de construir, mantenha o contexto durante o
  delivery e meça o resultado depois.

1.3 Diferencial

O diferencial não é simplesmente possuir um chatbot.

O diferencial é manter um Product Knowledge Model versionado e usar IA
para analisar esse conhecimento, identificar lacunas, avaliar impacto,
propor decisões e acompanhar o resultado.

A plataforma deve distinguir:

- Por que fazer? (Business/Strategy)
- O que fazer? (Product Management)
- Como construir? (TI/Engineering)
- Quem faz e quando? (Delivery)
- Gerou valor? (Outcomes)

======================================================================
2. PRINCÍPIOS DO PRODUTO
======================================================================

P1. Product Management é o núcleo do produto.

P2. A unidade principal de gestão é a Product Initiative, não o ticket.

P3. Capability é uma estrutura de capacidade relativamente estável do
produto.

P4. Feature representa uma capacidade observável do produto/negócio.

P5. Initiative representa uma decisão concreta de agir sobre uma
oportunidade/problema.

P6. Epic é tratado principalmente como conceito de delivery e pode ser
mapeado para uma Initiative, especialmente no Jira.

P7. A plataforma não deve virar um clone de Jira.

P8. A plataforma deve ser stack-agnostic.

P9. A plataforma deve ser model-agnostic.

P10. IA aumenta a capacidade humana e não substitui decisões críticas.

P11. IA não deve inventar requisitos, evidências ou dados ausentes.

P12. Quando houver informação insuficiente, a IA deve declarar a
incerteza e solicitar dados adicionais.

P13. O Product Model é a fonte de verdade do contexto.

P14. Assessment de IA é uma observação sobre uma versão específica do
Product Model, não a fonte de verdade.

P15. Dados e decisões importantes devem ser versionados e auditáveis.

P16. Alterações propostas pela IA devem passar por aprovação humana
quando alterarem o Product Model.

P17. A plataforma deve diferenciar impacto estimado de confiança da
estimativa.

P18. Entrega técnica e geração de valor são conceitos diferentes.

======================================================================
3. CICLO DE VIDA DO PRODUTO
======================================================================

Fluxo principal:

Strategy
  |
  v
Objective
  |
  v
Opportunity
  |
  v
Problem
  |
  v
Evidence / Hypothesis
  |
  v
Product / Capability
  |
  v
Feature
  |
  v
Initiative
  |
  v
Requirement
  |
  v
Delivery
  |
  v
Release
  |
  v
Outcome
  |
  +----------------------+
                         |
                         v
                    Discovery

O fluxo não precisa ser estritamente linear. Descoberta pode gerar
novas evidências, requisitos podem gerar novas decisões e outcomes
podem gerar novas oportunidades.

======================================================================
4. MODELO DE DOMÍNIO
======================================================================

4.1 Organization

Representa o cliente/empresa da plataforma.

Campos conceituais:

- id
- name
- status
- created_at
- updated_at

4.2 Workspace

Unidade de isolamento lógico dentro da organização.

Campos:

- id
- organization_id
- name
- status
- created_at
- updated_at

4.3 Product

Representa um produto gerenciado pela organização.

Exemplo:

Seguro Auto.

Campos:

- id
- workspace_id
- name
- description
- vision
- status
- owner
- current_version
- created_at
- updated_at

4.4 Strategy Objective

Representa um objetivo estratégico.

Exemplos:

- Aumentar conversão.
- Reduzir custo operacional.
- Reduzir tempo de atendimento.

4.5 Opportunity

Representa uma oportunidade ou ideia inicial.

A entrada deve ser simples.

Exemplo:

"O que você está tentando melhorar?"

Campos:

- id
- product_id
- title
- description
- source
- status
- created_by
- created_at
- updated_at

Status sugeridos:

NEW
DISCOVERY
QUALIFIED
REJECTED
CONVERTED

4.6 Problem

Representa o problema que precisa ser compreendido.

Campos:

- id
- opportunity_id
- product_id
- description
- audience
- impact
- evidence_ids
- status

4.7 Evidence

Representa evidência que sustenta um problema, hipótese ou decisão.

Fontes possíveis:

- Entrevista
- Analytics
- SAC
- Pesquisa
- Documento
- Experimento
- Dados operacionais
- Feedback de cliente

Campos:

- id
- type
- source
- description
- reference
- reliability
- created_at

A plataforma deve distinguir evidência declarada pelo usuário de
evidência observada/importada.

4.8 Hypothesis

Representa uma hipótese que precisa ser validada.

Campos:

- id
- statement
- expected_behavior
- expected_outcome
- evidence_ids
- confidence
- status

Status:

DRAFT
TESTING
VALIDATED
INVALIDATED
ABANDONED

4.9 Experiment

Representa uma forma de testar uma hipótese antes de construir uma
solução completa.

Campos:

- id
- hypothesis_id
- description
- method
- expected_signal
- actual_result
- status

4.10 Capability

Capability responde:

"O que o produto é capaz de fazer?"

Exemplo:

Seguro Auto
  - Cotação
  - Elegibilidade
  - Contratação
  - Emissão
  - Endosso
  - Sinistro
  - Cancelamento

Capability deve ser relativamente estável e independente da
implementação técnica.

Uma capability pode envolver:

- Frontend
- Backend
- APIs
- Plataforma de identidade
- Integrações
- Dados
- Operações
- Analytics

4.11 Feature

Feature representa uma capacidade observável pelo usuário ou negócio.

Exemplo:

Capability: Cotação

Features:
- Cotação online
- Comparação de planos
- Cálculo automático de franquia
- Recuperação de cotação

Campos:

- id
- capability_id
- name
- description
- value
- status
- initiative_ids

4.12 Initiative

É a principal unidade de planejamento e execução de Product
Management.

Uma Initiative responde:

"Vamos fazer alguma coisa sobre esse problema/oportunidade?"

Campos:

- id
- product_id
- feature_id
- opportunity_id
- problem_id
- title
- objective
- hypothesis_ids
- scope
- out_of_scope
- evidence_ids
- kpi_ids
- dependency_ids
- risk_ids
- status
- readiness_score
- delivery_confidence
- outcome_confidence
- version
- created_at
- updated_at

Status sugeridos:

DRAFT
DISCOVERY
READY_FOR_PRIORITIZATION
PRIORITIZED
READY_FOR_DELIVERY
IN_DELIVERY
READY_FOR_RELEASE
RELEASED
MEASURING
COMPLETED
CANCELLED

4.13 Requirement

Representa uma necessidade detalhada que será usada pelo delivery.

Campos:

- id
- initiative_id
- title
- description
- acceptance_criteria
- priority
- source
- status
- version

4.14 Decision

Representa uma decisão de produto.

Campos:

- id
- question
- decision
- rationale
- alternatives
- decider
- date
- affected_entity_ids

Decisions devem ser imutáveis historicamente.

4.15 KPI

Representa uma métrica de resultado.

Campos:

- id
- name
- definition
- unit
- baseline
- target
- current_value
- source
- owner

4.16 Dependency

Representa dependência entre entidades.

Exemplos:

Feature A depends_on Capability B.
Initiative A depends_on Initiative B.

4.17 Risk

Representa risco identificado.

Campos:

- id
- description
- probability
- impact
- mitigation
- status

4.18 Release

Representa uma entrega publicada.

Campos:

- id
- product_id
- version
- initiative_ids
- release_date
- status
- notes

4.19 Outcome

Representa o resultado observado após a release.

Campos:

- id
- initiative_id
- kpi_id
- baseline
- target
- current
- status
- observed_at

Status:

NOT_STARTED
PARTIALLY_ACHIEVED
ACHIEVED
NOT_ACHIEVED
UNKNOWN

======================================================================
5. PRODUCT KNOWLEDGE GRAPH
======================================================================

O sistema deve manter um grafo lógico de relações entre entidades.

Exemplos de relações:

supports
implements
depends_on
affects
measured_by
validated_by
derived_from
delivered_by
released_in
impacts
contradicts
related_to

Exemplo:

Feature A
  -> affects -> Capability B
  -> depends_on -> Capability C
  -> measured_by -> KPI D
  -> implemented_by -> Initiative E

Outro exemplo:

Initiative
  -> contains -> Requirement
  -> affects -> Capability
  -> depends_on -> Initiative
  -> measured_by -> KPI
  -> delivered_in -> Release

O Product Graph é utilizado para:

- Impact Analysis
- Change Impact
- Consistency Review
- Scope Drift
- Delivery Risk
- Outcome Analysis
- AI Product Review
- Context Retrieval para IA

======================================================================
6. VERSIONAMENTO
======================================================================

6.1 Princípio

O sistema deve preservar o histórico do Product Model.

Alterar uma entidade relevante gera uma nova versão lógica.

Exemplo:

Capability: Payment

v12
  Pix
  Cartão
  Boleto

v13
  Pix
  Cartão
  Boleto
  Pagamento recorrente

Uma avaliação executada sobre v12 continua referenciando v12.

6.2 Estrutura conceitual

Entity:

- id
- version
- status
- content
- created_by
- created_at
- updated_by
- updated_at

Version:

- entity_id
- version
- snapshot
- change_summary
- changed_by
- changed_at

6.3 Reprodutibilidade

Uma avaliação deve poder ser reconstruída a partir de:

- entidade avaliada;
- versão do Product Model;
- relações utilizadas;
- evidências;
- prompt version;
- modelo;
- parâmetros relevantes;
- timestamp.

======================================================================
7. AI ARCHITECTURE
======================================================================

7.1 AI Gateway

A aplicação não deve chamar diretamente Gemini, Groq ou Ollama.

Deve existir uma abstração:

AI Gateway
  |
  +-- Gemini Provider
  +-- Groq Provider
  +-- Ollama Provider
  +-- Future Providers

Interface conceitual:

generate(task, context, schema)
assess(type, subject, context_version)
review(type, subject, context_version)
extract(input, schema)

7.2 Provider selection

Exemplo:

product_discovery -> Gemini
quick_classification -> Groq
local_development -> Ollama
sensitive/local data -> Ollama, conforme configuração

O provider deve ser configurável.

7.3 AI Context Builder

A IA não deve acessar MongoDB diretamente.

Fluxo:

MongoDB
  |
  v
Context Builder
  |
  v
Relevant Product Context
  |
  v
AI Gateway
  |
  v
LLM

O Context Builder seleciona apenas informações relevantes.

Exemplo para "Pagamento mensal":

- Capability Payment
- Capability Billing
- Capability Contract
- Capability Cancellation
- Feature relacionadas
- Initiatives ativas
- Dependencies
- KPIs
- Decisions
- Evidence
- Releases relevantes

7.4 AI não deve inventar dados

Quando faltar informação:

- registrar missing_information;
- diminuir confidence;
- criar open_question;
- solicitar informação ao usuário.

======================================================================
8. COPILOT
======================================================================

O Copilot não deve ser apenas um chat.

Ele é uma camada transversal de inteligência sobre o Product Model.

Funções:

- Conversação
- Discovery
- Sugestões
- Assessment
- Review
- Perguntas
- Propostas de alteração
- Explicações
- Resumo de contexto
- Identificação de inconsistências

8.1 AI Proposal

A IA deve propor alterações estruturadas.

Exemplo:

{
  "action": "update_initiative",
  "changes": {
    "objective": "Reduzir tempo médio de abertura",
    "target": "< 10 minutos"
  }
}

Frontend apresenta:

[Aplicar]
[Rejeitar]

A IA não deve executar automaticamente mutações críticas.

8.2 Copilot contextual

O Copilot deve receber contexto da tela atual.

Exemplos:

Na Opportunity:
- perguntas de Discovery.

Na Initiative:
- gaps de Product Readiness.

Na Roadmap:
- conflito de prioridades.

Na Delivery:
- risco de atraso.

Na Outcome:
- análise de resultado.

======================================================================
9. AI DISCOVERY
======================================================================

Fluxo:

Nova Opportunity
  |
  v
AI Discovery
  |
  +-- Quem tem o problema?
  +-- Qual é o problema?
  +-- Quando acontece?
  +-- Qual é o impacto?
  +-- Existe evidência?
  +-- Como medir?
  +-- Qual resultado desejado?
  |
  v
Problem
  |
  v
Evidence
  |
  v
Hypothesis
  |
  v
Objective
  |
  v
KPI
  |
  v
Experiment
  |
  v
Initiative

A IA deve fazer perguntas adaptativas.

Não deve preencher lacunas inventando informação.

======================================================================
10. PRODUCT READINESS
======================================================================

Objetivo:

Responder:

"Estamos suficientemente preparados para iniciar delivery?"

Dimensões sugeridas:

Problem               15%
Evidence              15%
Hypothesis            10%
Value                 15%
KPI                   10%
Scope                 15%
UX                    10%
Technical Discovery   10%

Exemplo:

Problem              100
Evidence              90
Hypothesis            80
Value                 90
KPI                   70
Scope                 60
UX                    80
Technical Discovery   30

Resultado:

Readiness = 72/100

A plataforma deve mostrar os motivos e não somente o número.

Exemplo:

Technical Discovery:
- integração externa ainda não definida;
- dependência com Billing desconhecida.

Uma Initiative pode exigir critérios mínimos para entrar em
READY_FOR_DELIVERY.

======================================================================
11. IMPACT ASSESSMENT
======================================================================

11.1 Objetivo

Avaliar o impacto de uma nova Feature, Capability, Initiative ou
Requirement sobre o Product Model existente.

11.2 Exemplo

Nova Capability:

"Pagamento mensal"

O grafo identifica:

- Billing
- Pricing
- Contract
- Payment Gateway
- Cancellation
- Customer Portal

11.3 Dimensões

Business Impact
Product Impact
Technical Impact
Operational Impact
Risk
Data Impact
Dependency Impact
Regulatory Impact, quando aplicável
Change Scope

11.4 Score

O score deve ser explicável.

Exemplo:

Overall Impact = 82/100
Confidence = 84%

Technical Impact = 91

Motivos:
- 4 serviços afetados;
- 2 APIs precisam mudança;
- 1 integração externa;
- 3 regras existentes relacionadas;
- alteração de contrato.

11.5 Impacto x confiança

Nunca tratar:

Impact = 82

como certeza.

Pode existir:

Impact = 82
Confidence = 58%

Isso significa impacto provavelmente alto, mas com informação
insuficiente.

11.6 Assessment

Estrutura conceitual:

Assessment
- assessment_id
- type
- subject
- context_version
- model_provider
- model
- prompt_version
- score
- confidence
- findings
- evidence
- recommendations
- created_at

Tipos:

IMPACT
READINESS
CONSISTENCY
RISK
SCOPE_DRIFT
DELIVERY
OUTCOME
PRODUCT_REVIEW

======================================================================
12. CHANGE IMPACT
======================================================================

Quando uma entidade é alterada, o sistema pode comparar versões.

Exemplo:

Requirement R-102
v3 -> v4

O sistema identifica:

- 3 Features afetadas
- 2 Initiatives afetadas
- 7 Jira Stories
- 2 APIs
- 4 testes
- 1 Release
- 2 KPIs

Fluxo:

Entity v3
  |
  v
Entity v4
  |
  v
Graph Diff
  |
  v
Affected Entities
  |
  v
AI Analysis
  |
  v
Impact Report

======================================================================
13. CONSISTENCY REVIEW
======================================================================

A IA deve identificar conflitos entre:

- Decisions
- Requirements
- Initiatives
- Capabilities
- Features
- Evidence
- KPIs

Exemplo:

Decision DEC-51:
"A modalidade deve ser opcional."

Nova Initiative:
"Pagamento recorrente obrigatório."

Resultado:

CONTRADICTION

A IA deve apontar as fontes e permitir decisão humana.

======================================================================
14. SCOPE DRIFT
======================================================================

Scope Drift detecta delivery fora do escopo aprovado.

Exemplo:

Initiative:
"Comparar até 3 planos"

Jira:

PROJ-102 Comparar planos
PROJ-103 Comparar planos
PROJ-104 Criar recomendação automática
PROJ-105 Alterar pricing

Se PROJ-104 e PROJ-105 não estiverem relacionados ao escopo:

SCOPE DRIFT DETECTED

A plataforma deve mostrar:

- item;
- motivo;
- evidência;
- confidence;
- ação sugerida.

======================================================================
15. DELIVERY CONFIDENCE
======================================================================

Responde:

"Conseguimos entregar?"

Dimensões:

- Dependencies
- Technical complexity
- Delivery progress
- Blocked items
- Defects
- Test status
- Release risk

Resultado:

Delivery Confidence = 81%

Motivos:

- 80% das histórias concluídas;
- duas dependências externas abertas;
- uma história crítica bloqueada.

======================================================================
16. OUTCOME CONFIDENCE
======================================================================

Responde:

"Estamos gerando o valor esperado?"

Exemplo:

Baseline: 25 minutos
Target: < 10 minutos
Current: 12 minutos

Outcome:

PARTIALLY_ACHIEVED

O sistema deve comparar:

- baseline;
- target;
- atual;
- período;
- evidências;
- hipóteses;
- experimentos.

======================================================================
17. APRENDIZADO HISTÓRICO
======================================================================

A plataforma deve preservar:

Predição da IA
  ->
Decisão humana
  ->
Implementação
  ->
Resultado real

Exemplo:

IA:
Technical Impact = 75
Delivery Risk = 60
Outcome Confidence = 80%

Depois:

Technical Impact real = 82
Delivery Risk real = 78
Outcome real = 43%

Esses dados permitem avaliar a qualidade histórica das avaliações.

Possível evolução:

- descobrir padrões de subestimação;
- identificar tipos de iniciativa com maior risco;
- melhorar critérios;
- calibrar confidence;
- gerar benchmarks internos.

======================================================================
18. ROADMAP
======================================================================

Roadmap deve ser orientado a outcome/capability e não a tickets.

Exemplo:

Q1
  Outcome: Reduzir abandono de cotação
    Capability: Cotação
      Feature: Comparação de planos

Q2
  Outcome: Reduzir custo operacional
    Capability: Sinistro
      Feature: Automação de documentos

Roadmap deve mostrar:

- objetivo;
- outcome;
- capability;
- feature;
- initiative;
- confidence;
- dependencies;
- status.

======================================================================
19. PRIORIZAÇÃO
======================================================================

Dimensões:

- Business Impact
- Customer Value
- Strategic Alignment
- Confidence
- Effort
- Risk
- Dependencies
- Urgency

A IA pode recomendar:

Priority = High

Mas deve explicar:

- alinhamento estratégico;
- impacto;
- evidência;
- esforço;
- risco.

O Product Manager toma a decisão final.

======================================================================
20. DECISION LOG
======================================================================

Toda decisão importante deve poder ser registrada.

Formato:

Question
Decision
Rationale
Alternatives
Decider
Date
Affected Entities

Decisions são importantes para contexto histórico e para avaliações de
consistência.

======================================================================
21. FRONTEND
======================================================================

Stack recomendada:

- Next.js
- React
- TypeScript
- TanStack Query
- React Hook Form
- Zod
- Tailwind CSS
- shadcn/ui
- React Flow
- Vercel AI SDK, se adequado ao desenho final do AI Gateway

A aplicação deve ser altamente interativa.

21.1 Áreas principais

Overview
Opportunities
Discovery
Products
Roadmap
Initiatives
Delivery
Releases
Outcomes
AI Copilot
Settings

21.2 Overview

Mostrar:

- Initiatives;
- status;
- readiness;
- delivery confidence;
- outcome confidence;
- KPI;
- delivery progress;
- risks.

21.3 Nova Opportunity

Tela simples:

"O que você está tentando melhorar?"

[Continuar com IA]

21.4 AI Discovery

Interface conversacional com contexto.

Painel lateral pode mostrar:

- Problem;
- Evidence;
- Hypotheses;
- Objective;
- KPI;
- Open Questions.

21.5 Initiative Canvas

Componentes:

Problem
Audience
Objective
Hypothesis
Outcome
KPI
Evidence
Assumptions
Scope
Out of Scope
Dependencies
Risks

21.6 Product Graph

Visualização baseada em React Flow.

Exemplo:

Objective
  |
Opportunity
  |
Problem
  |
Capability
  |
Feature
  |
Initiative
  |
Requirement
  |
Jira
  |
Release
  |
Outcome

21.7 Impact Assessment UI

Mostrar:

Impact Score
Confidence

Capabilities affected
Features affected
Initiatives affected
Requirements affected
Integrations affected
KPIs affected
Releases at risk

Também mostrar a árvore de impacto e justificativas.

21.8 AI Review

Exemplo:

AI Product Review

[OK] Problem well defined
[OK] Evidence present
[WARN] KPI lacks baseline
[WARN] Hypothesis not validated
[BLOCK] Technical dependency unknown

[Resolver com IA]

======================================================================
22. UX DO COPILOT
======================================================================

O Copilot deve ser contextual e não apenas uma página de chat.

Formas:

- Side panel
- Inline suggestion
- Button "Melhorar com IA"
- Assessment card
- Warning
- Question
- Proposed change

Exemplo:

AI encontrou 3 problemas:

- KPI sem baseline
- Hipótese sem evidência
- Dependência não definida

Ações:

[Corrigir com IA]
[Ver detalhes]

======================================================================
23. BACKEND
======================================================================

Arquitetura inicial recomendada:

Modular Monolith

com componentes:

- Product API
- Discovery
- Assessment Engine
- AI Gateway
- Integration Gateway
- Versioning
- Audit

Evitar microserviços prematuros.

Arquitetura:

Next.js
  |
  | REST / SSE
  v
API
  |
  +-- Product Domain
  +-- Discovery
  +-- Assessment
  +-- AI Gateway
  +-- Integration Gateway
  |
  v
MongoDB

Integration Gateway:

- Jira
- GitHub/GitLab
- Azure DevOps
- outros futuramente

======================================================================
24. API
======================================================================

Endpoints conceituais:

POST   /opportunities
GET    /opportunities/{id}

POST   /discovery/sessions
POST   /discovery/sessions/{id}/messages

POST   /initiatives
GET    /initiatives/{id}
PATCH  /initiatives/{id}

POST   /initiatives/{id}/assessments
GET    /initiatives/{id}/assessments

GET    /initiatives/{id}/impact

GET    /products/{id}/graph
GET    /products/{id}/versions

POST   /ai/copilot
POST   /ai/actions/{id}/apply

POST   /initiatives/{id}/jira/sync

GET    /initiatives/{id}/delivery

POST   /releases
GET    /releases/{id}

GET    /outcomes/{id}

A API deve possuir OpenAPI.

======================================================================
25. MONGODB
======================================================================

Coleções iniciais:

organizations
workspaces
users
products
objectives
opportunities
problems
capabilities
features
initiatives
requirements
evidence
hypotheses
experiments
decisions
kpis
dependencies
risks
releases
outcomes
assessments
integrations
versions
audit_events

Índices devem ser definidos para:

- workspace_id;
- product_id;
- entity id;
- status;
- updated_at;
- version;
- relationship target;
- Jira external IDs.

O desenho deve evitar consultas excessivamente profundas no caminho
crítico. Para traversals frequentes, manter relações materializadas
quando necessário.

======================================================================
26. JIRA
======================================================================

Princípio:

A plataforma = Product Management.
Jira = Delivery.

Mapeamento:

Initiative <-> Jira Epic
Requirement <-> Jira Story

Platform -> Jira:

- criar Epic;
- criar Story;
- atualizar escopo aprovado;
- sincronizar metadados selecionados.

Jira -> Platform:

- status;
- sprint;
- progress;
- bugs;
- changelog;
- release/deployment, quando disponível.

MVP:

1. Conectar Jira via OAuth.
2. Selecionar projeto.
3. Mapear Initiative para Epic.
4. Mapear Requirement para Story.
5. Criar issues.
6. Sincronizar status.

Futuro:

- Sprint;
- Estimates;
- Releases;
- Bugs;
- GitHub/GitLab;
- CI/CD;
- Deployments.

A integração deve usar webhooks quando possível para reduzir polling.

======================================================================
27. DELIVERY
======================================================================

A plataforma não precisa substituir:

- Jira;
- Azure DevOps;
- Linear;
- GitHub;
- GitLab;
- ferramentas CI/CD.

Ela agrega contexto.

Exemplo:

Product Platform:
"Como está a Initiative?"

O sistema combina:

- Product readiness;
- Jira progress;
- blockers;
- Git/PR status, se integrado;
- release status;
- risks.

E apresenta:

Delivery Confidence = 74%

======================================================================
28. RELEASE
======================================================================

Uma Release agrega:

- Initiatives;
- Requirements;
- delivery status;
- defects;
- readiness;
- KPI baseline;
- expected outcome.

Antes de liberar:

AI Release Review

Verificar:

- scope;
- unresolved risks;
- blocked requirements;
- critical bugs;
- KPI instrumentation;
- dependencies.

======================================================================
29. OUTCOMES
======================================================================

Após release:

Release
  |
  v
KPI
  |
  v
Outcome

O sistema deve registrar:

- baseline;
- target;
- current;
- measurement period;
- data source;
- status.

A plataforma deve evitar confundir:

"feature entregue"

com:

"resultado obtido".

======================================================================
30. SEGURANÇA E RBAC
======================================================================

Estrutura:

Organization
  |
  Workspace
    |
    Products

Papéis sugeridos:

Admin
Product Manager
Product Owner
Business
Engineering
Viewer

Regras:

- isolamento por organization/workspace;
- autorização por recurso;
- integração externa com credenciais protegidas;
- auditoria de ações;
- IA sem permissão implícita de mutação.

Fluxo de alteração por IA:

AI
  |
  v
Proposal
  |
  v
Human approval
  |
  v
Mutation
  |
  v
Audit Event

======================================================================
31. AUDITORIA
======================================================================

Registrar:

- quem;
- o quê;
- quando;
- entidade;
- versão anterior;
- nova versão;
- motivo;
- assessment relacionado;
- modelo;
- prompt version;
- context version;
- decisão humana.

A auditoria deve permitir responder:

"Por que esta decisão foi tomada?"

======================================================================
32. OBSERVABILIDADE
======================================================================

Monitorar:

- API latency;
- AI latency;
- token usage;
- provider;
- model;
- error rate;
- assessment latency;
- Mongo latency;
- Jira API latency;
- webhook processing;
- failed AI actions.

Cada operação de IA deve possuir correlation/trace ID.

Não registrar dados sensíveis no log sem necessidade.

======================================================================
33. NON-FUNCTIONAL REQUIREMENTS
======================================================================

NFR-01 Multi-tenancy
O sistema deve isolar dados por organization/workspace.

NFR-02 Auditability
Alterações importantes devem ser auditáveis.

NFR-03 Versionability
O Product Model deve ser versionado.

NFR-04 Explainability
Assessments devem apresentar motivos e evidências.

NFR-05 Uncertainty
IA deve expor confidence e missing information.

NFR-06 Provider Independence
Troca de provider de IA não deve exigir alteração do domínio.

NFR-07 Stack Independence
O Product Model não deve depender de uma linguagem específica.

NFR-08 Integration Independence
Jira deve ser uma integração e não uma dependência do domínio.

NFR-09 Availability
O backend deve ser projetado para execução stateless quando possível.

NFR-10 Performance
Operações sem IA devem possuir latência baixa e previsível.
Operações de IA devem ser tratadas como assíncronas/streaming quando
apropriado.

NFR-11 Security
Segredos, tokens e credenciais de integração não devem ficar expostos
ao frontend.

NFR-12 Reproducibility
Assessments devem registrar contexto e versões suficientes para
reprodução/análise posterior.

======================================================================
34. MVP
======================================================================

MVP 1 - Product Discovery

- Workspace
- Products
- Opportunities
- AI Discovery
- Problems
- Evidence
- Hypotheses
- Initiatives
- Initiative Canvas
- Product Readiness
- Versioning
- AI Assessment

MVP 2 - Product Management

- Capabilities
- Features
- Roadmap
- Prioritization
- Experiments
- Decisions
- Product Graph
- Impact Analysis
- Change Impact

MVP 3 - Delivery

- Jira OAuth
- Initiative -> Epic
- Requirement -> Story
- Status synchronization
- Scope Drift
- Delivery Confidence

MVP 4 - Outcomes

- Releases
- KPIs
- Outcomes
- Outcome Confidence
- AI Product Review
- Historical assessment analysis

======================================================================
35. ROADMAP DE EVOLUÇÃO
======================================================================

Fase 1:
Product Discovery + AI Copilot

Fase 2:
Product Model + Graph + Assessments

Fase 3:
Jira + Delivery

Fase 4:
Outcomes + Feedback Loop

Fase 5:
Git/CI/CD/Architecture integration

Fase 6:
Reverse Product Engineering

Na fase de Reverse Product Engineering:

Código
  |
  v
Repository Analysis
  |
  v
Capabilities
  |
  v
Features
  |
  v
Living Specification

Isso permitiria comparar:

Requirement -> Implementation

e posteriormente:

Implementation -> Specification.

======================================================================
36. FUTURAS INTEGRAÇÕES
======================================================================

Além de Jira:

- Azure DevOps
- Linear
- GitHub
- GitLab
- Bitbucket
- CI/CD
- Product Analytics
- CRM
- Customer Support
- Data Warehouse
- Documentation systems

A arquitetura deve manter Integration Gateway desacoplado do Product
Domain.

======================================================================
37. PRINCIPAIS TELAS
======================================================================

1. Overview
2. Opportunities
3. Opportunity Detail
4. AI Discovery
5. Products
6. Product Detail
7. Capability Detail
8. Feature Detail
9. Roadmap
10. Initiative List
11. Initiative Canvas
12. Impact Assessment
13. Product Readiness
14. Prioritization
15. Experiments
16. Decision Log
17. Delivery
18. Jira Integration
19. Release
20. Outcomes
21. AI Product Review
22. Product Graph
23. Settings

======================================================================
38. EXEMPLO END-TO-END
======================================================================

Entrada:

"Quero reduzir o tempo para abertura de sinistro."

Discovery:

Problema:
A abertura de sinistro demora para o cliente.

Público:
Cliente.

Evidência:
Chamados no SAC.

Baseline:
25 minutos.

Target:
< 10 minutos.

KPI:
Tempo médio de abertura.

Hipótese:
Simplificar coleta de documentos reduzirá o tempo de abertura.

Experiment:
Teste com fluxo simplificado.

Capability:
Sinistro.

Feature:
Abertura digital simplificada.

Initiative:
"Permitir abertura simplificada de sinistro."

Product Readiness:
72/100.

Impact Assessment:

Capabilities:
- Sinistro
- Documentos
- Customer Portal

Dependencies:
- Document service
- Authentication

Depois de aprovada:

Initiative
  |
  v
Requirements
  |
  v
Jira Epic
  |
  +-- Story
  +-- Story
  +-- Story
  |
  v
Release
  |
  v
KPI

Resultado:

Baseline = 25 min
Target = <10 min
Current = 8 min

Outcome = ACHIEVED

A plataforma então registra o resultado e utiliza o histórico para
futuras análises.

======================================================================
39. ARQUITETURA FINAL DE REFERÊNCIA
======================================================================

                    +----------------------+
                    |      Next.js         |
                    | React / TypeScript   |
                    +----------+-----------+
                               |
                         REST / SSE
                               |
                    +----------v-----------+
                    |     Product API      |
                    +----------+-----------+
                               |
              +----------------+----------------+
              |                |                |
              v                v                v
       Product Domain     AI Gateway      Integration Gateway
              |                |                |
              |          +-----+-----+      +----+------+
              |          |     |     |      |    |     |
              |       Gemini Groq Ollama   Jira Git  ADO
              |
              v
           MongoDB
              |
       +------+------+
       |             |
   Product Model   Versions
       |
   Assessments
       |
   Audit Events

======================================================================
40. DECISÕES ARQUITETURAIS IMPORTANTES
======================================================================

D1. MongoDB é o Product Knowledge Store inicial.

D2. Product Graph é lógico e pode ser implementado inicialmente sobre
MongoDB sem exigir um banco de grafos dedicado.

D3. Versionamento é parte do domínio, não uma funcionalidade posterior.

D4. Assessment é entidade persistente e imutável.

D5. AI Gateway desacopla o produto dos fornecedores de modelos.

D6. Copilot é contextual e orientado a ações estruturadas.

D7. IA não possui mutação irrestrita do domínio.

D8. Jira é integração de delivery.

D9. Initiative não é sinônimo de Epic.

D10. Capability é mais estável que Feature e Initiative.

D11. Outcome é separado de Release.

D12. Product Readiness, Delivery Confidence e Outcome Confidence são
métricas distintas.

D13. Impact Score deve sempre ser acompanhado de Confidence e
justificativas.

D14. O sistema deve preservar o contexto histórico utilizado pela IA.

======================================================================
41. CRITÉRIOS DE SUCESSO DO PRODUTO
======================================================================

O produto será considerado bem-sucedido quando conseguir:

1. Transformar uma ideia pouco estruturada em uma Initiative
   estruturada.

2. Identificar lacunas antes do início do delivery.

3. Explicar por que uma Initiative está ou não pronta.

4. Avaliar o impacto de novas Features/Capabilities.

5. Mostrar dependências e efeitos transitivos.

6. Detectar inconsistências no Product Model.

7. Detectar Scope Drift no delivery.

8. Integrar Product Management ao Jira sem substituí-lo.

9. Acompanhar uma Initiative até seu Outcome.

10. Preservar histórico suficiente para explicar decisões e avaliações.

11. Permitir troca de modelo de IA sem alterar o domínio.

12. Fazer a IA trabalhar sobre contexto real e versionado, em vez de
ser apenas um chatbot.

======================================================================
42. CONCEITO CENTRAL
======================================================================

O produto deve ser construído em torno desta ideia:

"Entenda o impacto antes de construir, mantenha o contexto durante o
delivery e meça o resultado depois."

A IA é o mecanismo de inteligência.

O Product Model é o contexto.

O Product Graph é a estrutura de relacionamento.

O versionamento é a memória.

O Assessment é a análise.

O Jira é o delivery.

O Outcome é a validação de valor.

Esse conjunto forma a base de uma plataforma de Product Management
AI-first, orientada a contexto, impacto, rastreabilidade e resultados.
