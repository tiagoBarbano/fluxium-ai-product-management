# Analise do MVP - Fluxium AI Product Management

**Versao:** 0.1  
**Data:** 2026-09-18  
**Status:** Em validacao  
**Base funcional:** `docs/specifications/AI_Product_Management_Platform_MVP_PRD_v0.1.md`  
**Base de UX:** `docs/specifications/AI_Product_Management_Platform_MVP_UX_v0.1.md`  
**Wireframes:** `docs/specifications/AI_Product_Management_Platform_MVP_Wireframes_v0.1.md`

## 1. Objetivo da analise

Consolidar a especificacao do MVP antes do planejamento tecnico e da
implementacao, identificando requisitos, regras, fluxos, dependencias, riscos e
pontos que ainda exigem decisao do Product Owner.

A analise adota o modelo de gestao definido no PRD:

```text
OKR
  -> Business Problem
      -> Opportunity
          -> Discovery
              -> Evidence + Hypothesis
                  -> Initiative
                      -> 5W2H / Business Plan
                          -> Product Readiness
                              -> Aprovacao humana
```

O Business Plan, neste MVP, e uma visao estruturada da Initiative. Nao e um
modulo financeiro, de roadmap, de tarefas ou de delivery.

## 2. Hipotese de produto

O Fluxium gera valor quando transforma uma entrada pouco estruturada em uma
Initiative compreensivel e auditavel, mantendo o humano no controle das
alteracoes sugeridas pela IA.

A hipotese sera considerada refutada se a jornada exigir, para funcionar, um
modulo independente de planejamento, delivery ou execucao que ainda nao esteja
no escopo do MVP.

## 3. Atores e responsabilidades

| Ator | Responsabilidades no MVP |
|---|---|
| ADMIN | Administrar workspace, membros e configuracoes permitidas |
| PRODUCT_MANAGER | Criar, editar, avaliar, aprovar e alterar artefatos autorizados |
| CONTRIBUTOR | Contribuir com dados de Discovery, evidencias e hipoteses permitidas |
| VIEWER | Consultar contexto, assessments e historico sem alterar dados |
| IA / Copilot | Fazer perguntas, resumir, apontar lacunas e propor alteracoes; nunca aprovar ou persistir mutacoes diretamente |

A matriz definitiva de permissoes por entidade, campo e transicao ainda nao foi
validada.

## 4. Requisitos funcionais analisados

### 4.0 Incremento REQ-MVP-011 - Gestao de OKRs

O requisito esta implementado com Objective pertencendo ao Product e Initiative
mantendo referencias para um ou mais Objectives. Essa direcao permite que o
mesmo Objective seja reutilizado por varias Initiatives, enquanto a validacao
de workspace e Product fica no Service de Initiative. A tela frontend dedicada
permite consultar e manter OKRs.

#### Cobertura confirmada

- Objective aceita titulo e descricao qualitativos.
- Objective exige ao menos um Key Result.
- Key Result exige metrica, alvo numerico e prazo.
- Um Objective pode conter varios Key Results.
- A API possui criacao, consulta, listagem e atualizacao parcial.
- O documento e tenant-scoped e possui indice por tenant/workspace.

#### Lacunas que este incremento deve resolver

- validar que o Product do Objective existe no tenant e pertence ao workspace;
- validar que cada Objective referenciado pela Initiative pertence ao mesmo
  workspace e Product da Opportunity;
- permitir varios Objective IDs em uma Initiative e reutilizar um Objective em
  varias Initiatives;
- preservar IDs e timestamps de Key Results em atualizacoes parciais;
- oferecer listagem, criacao e edicao de OKRs no frontend;
- cobrir sucesso, entradas invalidas, referencias inexistentes e isolamento;
- atualizar a rastreabilidade do requisito.

#### Fora do escopo

- ciclos formais de OKR;
- check-ins, historico de progresso ou calculo de percentual concluido;
- dashboards ou graficos de performance;
- vinculo direto de OKR a Opportunity, Business Problem ou Evidence;
- auditoria detalhada de cada alteracao, enquanto a infraestrutura transversal
  de auditoria de agregados ainda nao estiver integrada a este caso de uso.

### 4.1 Organizacao e contexto

- O sistema deve operar dentro de um Workspace isolado.
- Toda entidade deve possuir escopo de Workspace.
- O usuario deve selecionar ou criar um Product antes de registrar trabalho.
- O contexto atual deve permanecer visivel durante Opportunity, Discovery,
  Canvas e Readiness.
- OKR pode ser associado como contexto estrategico quando existir.

### 4.2 Business Problem e Discovery

- Um Business Problem deve registrar descricao, publico afetado, impacto,
  evidencias relacionadas e status.
- Impacto informado pelo usuario deve ser distinguido de impacto estimado pela
  IA.
- Uma Opportunity deve registrar a intencao inicial e manter seu texto
  original.
- Uma Discovery deve preservar perguntas, respostas, mensagens e contexto
  estruturado.
- A IA deve adaptar perguntas com base no contexto disponivel.
- Informacao ausente deve aparecer como lacuna ou pergunta, nunca como fato
  confirmado.
- O usuario deve conseguir continuar manualmente quando a IA estiver
  indisponivel.

#### Incremento implementado: Discovery manual

O primeiro incremento de Discovery sera manual e persistido. Uma sessao nasce
a partir de uma Opportunity autorizada, muda a Opportunity de `NEW` para
`DISCOVERY` e preserva mensagens em collection propria. O contexto estruturado
aceita somente informacoes fornecidas pelo usuario, possui versionamento
otimista e nao cria automaticamente Problem, Evidence, Hypothesis ou
Initiative. A sessao pode ser pausada, retomada e concluida sem promover a
Opportunity para `QUALIFIED`.

#### Incremento implementado: artefatos estruturados de Discovery

Business Problem, Evidence e Hypothesis são persistidos como recursos
independentes e vinculados à Opportunity no mesmo Workspace. Evidence distingue
tipo e origem (`MANUAL`, `IMPORTED`, `OBSERVED`); Hypothesis possui confiança
entre zero e um, evidências relacionadas e estados de validação; Business
Problem separa impacto informado de impacto estimado. As relações são
validadas no Service e as atualizações versionáveis usam controle otimista.
IA, Initiative, Readiness e aprovação humana permanecem fora deste incremento.

### 4.3 Evidence e Hypothesis

- Evidence deve registrar tipo, origem, autor e relacao com Problem,
  Hypothesis ou decisao.
- O sistema deve distinguir evidence manual de evidence importada ou observada.
- Hypothesis deve registrar afirmacao, comportamento esperado, resultado
  esperado, evidencias relacionadas, confianca e status.
- Confianca e uma estimativa explicavel, nunca uma certeza.

### 4.4 Initiative e Business Plan

O incremento implementado persiste Initiative como unidade versionada de
planejamento, vinculada a Product, Opportunity e, quando informado, Problem,
Hypotheses, Evidence e Objectives do mesmo Workspace. O Business Plan é uma
visão opcional da Initiative com racional, 5W2H, métricas e riscos; não contém
tarefas, delivery ou orçamento financeiro.

- Initiative deve relacionar Product, Opportunity, Business Problem, Evidence e
  Hypothesis.
- Deve conter objetivo, resultado esperado, escopo, fora de escopo, KPI ou forma
  de medicao, dependencias e riscos.
- Deve permitir associar mais de um Objective de OKR.
- Cada Initiative pode referenciar um ou mais Objectives do mesmo Product.
- Um Objective pode ser referenciado por varias Initiatives.
- Cada Objective pode possuir um ou mais Key Results quantitativos, especificos
  e com prazo definido.
- Deve permitir preencher opcionalmente o plano 5W2H: What, Why, Where, When,
  Who, How e How Much.
- Business Plan deve ser uma visao consolidada da Initiative e nao uma entidade
  de execucao independente no MVP.
- A Initiative deve possuir status, versao, autor e timestamps.

### 4.5 Product Readiness e aprovacao

O incremento implementado cria assessments imutáveis de Readiness com score
determinístico entre zero e cem, oito dimensões, justificativas, lacunas,
perguntas abertas, confiança e metadados do contexto avaliado. Proposals são
persistidas separadamente; somente `ADMIN` e `PRODUCT_MANAGER` podem aprovar
ou rejeitar, e rejeições não alteram a Initiative. O AI Gateway, os contratos
de Jobs e a auditoria das decisões humanas já possuem infraestrutura inicial;
a execução de Readiness via job de IA e a auditoria completa de todos os
agregados permanecem nos próximos incrementos.

- O sistema deve calcular score geral e score por dimensao.
- Deve apresentar justificativas, lacunas, perguntas abertas, confianca e
  contexto/versionamento avaliado.
- A entrada da Readiness deve orientar a construção do contexto em oito
  dimensões, mantendo também uma nota livre opcional. Campos vazios devem ser
  enviados como ausência de informação, sem criação de fatos pela IA.
- A confiança da avaliação é uma estimativa de qualidade/completude das
  evidências de entrada, separada do score de prontidão prevista. O cálculo
  usa confiança do provider, completude do contexto, cobertura das dimensões e
  penalidades por lacunas/perguntas abertas; não representa prontidão real
  observada.
- Deve preservar provider, modelo, prompt e timestamp da avaliacao.
- Propostas da IA devem mostrar os campos afetados e exigir aprovacao humana.
- Somente `ADMIN` e `PRODUCT_MANAGER` podem aprovar propostas da IA.
- Rejeicoes tambem devem ser auditadas.
- Assessments antigos devem permanecer imutaveis e reproduziveis.

### 4.6 Auditoria e versionamento

- Alteracoes relevantes devem gerar nova versao ou snapshot imutavel.
- Eventos devem identificar autor ou processo, versao anterior, nova versao,
  data, motivo e assessment relacionado quando aplicavel.
- Conflitos de versao nao podem sobrescrever dados silenciosamente.

O incremento atual fornece `AuditEvent` imutável, repository Mongo com índices,
correlação e contexto de provider/modelo/prompt, além de registrar aprovação e
rejeição de Proposal.

### 4.7 AI Gateway e Jobs

O AI Gateway desacopla o domínio do provider, possui adapter Ollama local,
fake offline e erros tipados para timeout ou indisponibilidade sem impedir a
edição manual. A porta de Jobs oferece estados, idempotência, retry,
correlation ID e adapters Redis/fake. A orquestração de Readiness com esses
jobs será implementada no próximo incremento.

#### Desenho operacional validado para o worker Redis de Readiness

O job é criado no Redis em estado `PENDING`, com chave de idempotência e
`correlation_id`. Um worker separado descobre e reivindica o job com lease
exclusivo; a execução passa por `RUNNING` e termina em `SUCCEEDED` após
persistir o assessment, ou em `FAILED` com erro serializado quando o provider
falha. O teste de integração usa uma instância Redis real configurada por
`FLUXIUM_REDIS_URL`, mas injeta `FakeAIProvider`, mantendo o teste determinístico
e sem dependência de Ollama.

O cenário fica desativado por padrão e só executa com
`FLUXIUM_RUN_REDIS_INTEGRATION=1`. Cada teste usa prefixo Redis único, polling
assíncrono com timeout de `FLUXIUM_REDIS_INTEGRATION_TIMEOUT_SECONDS` e remove
suas chaves ao final. O processo HTTP não executa o job; o worker pode ser
iniciado com `uv run python -m app.workers.readiness_worker`.

## 5. Requisitos nao funcionais

### Seguranca e isolamento

- Isolamento por organization/workspace em todas as consultas e mutacoes.
- Autenticacao e autorizacao por recurso e por transicao.
- Nenhum segredo de provider exposto ao frontend.
- Entradas e respostas externas devem ser validadas.
- Erros nao devem expor stack trace ou dados de outro workspace.

### Performance e disponibilidade

- Operacoes sem IA devem ter meta inicial de P95 de ate 500 ms, sujeita a
  validacao.
- Operacoes de IA devem possuir timeout, estado de execucao e tratamento de
  falha.
- Falha de provider nao pode impedir edicao manual de dados ja validaveis.
- Chamadas externas devem avaliar timeout, retry e circuit breaker.

### Consistencia e concorrencia

- Assessment deve apontar para a versao exata do contexto utilizado.
- Escrita concorrente deve usar controle de versao otimista ou mecanismo
  equivalente.
- Alteracoes relevantes devem ser auditaveis.
- Datas e eventos devem usar UTC.

### Observabilidade

- Operacoes relevantes devem preservar CorrelationId e TraceId.
- Logs devem ser estruturados e nao conter dados sensiveis desnecessarios.
- Jobs de IA devem possuir estado, timeout, retry e idempotencia quando forem
  executados de forma assincrona.

### Acessibilidade e UX

- Fluxos criticos devem funcionar por teclado.
- Campos devem possuir labels persistentes e erros associados.
- Score e status nao podem depender somente de cor.
- Loading, vazio, erro, autorizacao, sessao expirada e sucesso devem ser
  observaveis.
- A tela deve diferenciar confirmado, fonte, lacuna e sugestao da IA.

## 6. Regras de negocio

1. Uma Opportunity pertence a um Product e a um Workspace.
2. O texto original da Opportunity nao pode ser substituido pela IA.
3. Uma Opportunity pode originar uma ou mais Initiatives.
4. Converter Opportunity em Initiative nao apaga a Opportunity nem seu
   historico.
5. Uma sugestao da IA nao altera o Product Model sem aprovacao humana.
6. Aprovar uma proposta deve registrar os campos alterados e a decisao.
7. Rejeitar uma proposta nao altera o Product Model, mas gera auditoria.
8. Somente `ADMIN` e `PRODUCT_MANAGER` podem aprovar propostas da IA.
9. Evidence sem fonte ou justificativa nao deve ser apresentada como confiavel.
10. Confianca da IA deve ser apresentada separadamente do score de Readiness.
11. Uma nova avaliacao cria um novo Assessment; o anterior permanece imutavel.
12. Assessment desatualizado nao deve ser tratado como resultado corrente.
13. IA indisponivel nao bloqueia operacoes manuais validas.
14. Troca de Workspace ou Product com alteracoes nao salvas exige decisao
    explicita do usuario.
15. Business Plan no MVP organiza contexto e decisao; nao executa tarefas nem
    controla delivery.
16. Uma Initiative so pode avancar quando as pre-condicoes do status e da
    permissao estiverem atendidas.

## 7. Fluxo principal

### Pre-condicoes

- Usuario autenticado.
- Usuario possui acesso ao Workspace.
- Product existente ou permissao para cria-lo.
- Provider de IA configurado apenas quando a etapa depender de IA.

### Passos

1. Selecionar Workspace.
2. Selecionar ou criar Product.
3. Associar um OKR existente quando aplicavel.
4. Registrar Opportunity com titulo, descricao, Product e origem opcional.
5. Salvar como rascunho ou iniciar Discovery.
6. Registrar ou confirmar Business Problem, publico e impacto.
7. Registrar Evidence e Hypothesis.
8. Criar Initiative a partir do contexto confirmado.
9. Preencher objetivo, resultado, escopo, KPI, riscos e dependencias.
10. Associar OKR e preencher 5W2H / Business Plan.
11. Solicitar Product Readiness.
12. Revisar score, dimensoes, lacunas e propostas.
13. Aprovar proposta, rejeitar, editar manualmente ou manter em Discovery.
14. Avancar status quando criterios e permissao permitirem.

### Pos-condicoes

- Dados persistidos no Workspace correto.
- Relacionamentos entre artefatos preservados.
- Nova versao criada quando houver alteracao relevante.
- Assessment vinculado a uma versao especifica.
- Decisoes humanas e mutacoes da IA auditadas.

## 8. Fluxos alternativos e erros

### Opportunity salva como rascunho

A Opportunity e persistida sem iniciar IA ou Discovery automatica. O usuario
pode continuar depois.

### Dados insuficientes

A IA informa `missing_information`, reduz a confianca e apresenta pergunta
objetiva. O usuario pode responder ou preencher o campo manualmente.

### IA indisponivel

A interface informa a indisponibilidade e habilita edicao manual. O conteudo
salvo permanece disponivel; nenhuma sugestao parcial deve ser tratada como fato.

### Falha de persistencia

A interface preserva o conteudo local quando possivel, informa que a operacao
nao foi concluida e oferece nova tentativa. Nao deve mostrar sucesso falso.

### Conflito de versao

A escrita e rejeitada ou suspensa quando a versao do cliente esta desatualizada.
O usuario deve revisar a versao atual. A estrategia de merge permanece em
aberto.

### Proposta rejeitada

A proposta nao altera os dados. A decisao, o motivo quando exigido e o contexto
avaliado permanecem no historico.

### Readiness desatualizado

Se o Canvas mudar depois da avaliacao, o Assessment deve ser marcado como
historico/desatualizado e uma nova avaliacao deve ser solicitada.

### Nao autorizado ou sessao expirada

Nao exibir dados protegidos. Informar a condicao e oferecer retorno ou nova
autenticacao conforme o caso.

## 9. Validacoes

### Validacoes de entrada

- Product: nome obrigatorio.
- Opportunity: titulo, descricao e Product obrigatorios.
- Business Problem: descricao, publico e status conforme regra validada.
- Evidence: tipo, origem e relacionamento devem ser coerentes.
- Hypothesis: afirmacao e status obrigatorios.
- Initiative: relacionamentos, objetivo, contexto minimo e status devem ser
  validos.
- 5W2H: o conjunto e opcional; quando utilizado, permite What, Why, Where,
  When, Who, How e How Much.
- OKR: cada Objective deve possuir um ou mais Key Results; cada KR deve conter
  metrica quantitativa, alvo e prazo definido.
- Permissao: somente `ADMIN` e `PRODUCT_MANAGER` podem aprovar propostas.

### Validacoes de dominio

- Transicoes de Opportunity devem respeitar estado atual e permissao.
- Transicoes de Initiative devem respeitar estado atual, readiness e permissao.
- Assessment deve usar a versao corrente ou declarar explicitamente a versao
  avaliada.
- Proposal aplicada deve conter diff valido e usuario aprovador autorizado.
- Relacoes entre Workspace, Product e entidades devem ser tenant-scoped.

### Validacoes de integracao

- Resposta da IA deve conter resultado, confianca, lacunas, perguntas,
  referencias e metadados de auditoria.
- Provider com erro, timeout ou resposta invalida deve produzir estado
  recuperavel.
- Nenhuma integracao externa pode executar mutacao de negocio sem fluxo de
  aprovacao.

## 10. Dependencias e integracoes

### Dependencias internas

- Autenticacao e autorizacao.
- Modelo de Workspace e Product.
- Repositorios MongoDB tenant-scoped.
- Servico de versionamento e auditoria.
- Servico de Product Readiness.
- AI Gateway desacoplado de providers.
- Contratos de API e tratamento padronizado de erros.

### Integracoes externas

- Provider de IA por meio do AI Gateway.
- MongoDB para persistencia.
- Sistema de observabilidade para logs, metricas e traces.

Nenhuma integracao com Jira, GitHub, GitLab, Azure DevOps, delivery ou release
faz parte deste MVP.

## 11. Riscos

| Risco | Impacto | Mitigacao |
|---|---|---|
| IA apresentar sugestao como fato | Decisoes incorretas | Distincao visual, confianca, referencias e aprovacao humana |
| Escopo de Business Plan crescer para ERP/delivery | Atraso e complexidade | Limitar ao 5W2H, contexto, riscos e metricas |
| OKR nao estar disponivel em todos os workspaces | Jornada incompleta | Associacao opcional no MVP; confirmar comportamento sem OKR |
| Evidence de baixa qualidade | Readiness enganoso | Origem obrigatoria, classificacao explicita e lacunas |
| Avaliacao nao reproduzivel | Falha de auditoria | Snapshot/versionamento, provider/modelo/prompt e contexto |
| Conflito de versao | Perda de trabalho | Optimistic concurrency e bloqueio de sobrescrita silenciosa |
| Custo ou latencia de IA | Baixa adocao | Timeout, limites, estado assincrono e modo manual |
| Permissoes incompletas | Vazamento ou mutacao indevida | Matriz por recurso/campo/transicao e testes tenant-scoped |

## 12. Ambiguidades e decisoes pendentes

1. Um Product pode possuir varios ciclos de OKR ativos simultaneamente?
2. Quais metas quantitativas validarao o piloto?

### 12.1 Decisoes confirmadas pelo Product Owner

| Tema | Decisao |
|---|---|
| OKR | O sistema permite mais de um Objective. Cada Objective pode possuir varios Key Results. |
| Objective | E qualitativo, inspirador e ambicioso; representa onde se quer chegar. |
| Key Result | E quantitativo, especifico e possui prazo; mede se o Objective foi alcancado. |
| 5W2H | E opcional no Business Plan e permite What, Why, Where, When, Who, How e How Much. |
| Aprovacao | Somente `ADMIN` e `PRODUCT_MANAGER` podem aprovar propostas da IA. |

### 12.2 Decisoes de negocio adotadas

| Tema | Decisao |
|---|---|
| Status inicial da Opportunity | `Salvar e iniciar Discovery` cria em `NEW` e realiza a transicao para `DISCOVERY` na mesma operacao de dominio. |
| Transicao da Initiative | Requer Readiness valido, ausencia de lacuna critica e permissao adequada. |
| Avanco de status | `PRODUCT_MANAGER` pode aprovar e avancar; `ADMIN` administra e pode executar operacoes autorizadas; `CONTRIBUTOR` contribui; `VIEWER` somente consulta. |
| Rejeicao de Opportunity | Exige motivo obrigatorio e gera auditoria. |
| Conflito de versao | Usar controle otimista, bloquear sobrescrita silenciosa e exigir revisao manual inicialmente. |
| OKR | Comecar com Objective, Key Result, metrica, alvo, prazo e Product; ciclos formais podem ser adicionados depois. |
| Readiness | Manter oito dimensoes propostas, score de 0 a 100, score e confianca separados e assessment `STALE` apos mudanca relevante. |
| Lacuna critica | Impede o avanco da Initiative ate ser resolvida ou explicitamente tratada conforme regra de negocio. |
| Business Plan | Permanece dentro da Initiative e nao possui aprovacao separada. |
| How Much | Aceita custo, esforco ou recurso, sempre com unidade identificada. |

### 12.3 Decisoes de infraestrutura e seguranca

| Tema | Decisao |
|---|---|
| Autenticacao | Usar o mecanismo desenvolvido na plataforma de identidade, integrado por contrato desacoplado. Detalhes do contrato de claims permanecem para a implementacao da integracao. |
| IA inicial | Ollama local para testes e desenvolvimento. O dominio acessa apenas o AI Gateway. |
| Jobs assincronos | Usar Redis inicialmente como broker/estado de jobs; manter uma porta de integracao que permita substituir por RabbitMQ. |
| Retencao | Reter mensagens de Discovery, contexto, assessments e auditoria por cinco anos, sujeita a politica formal de descarte. |
| Dados enviados a IA | Todos os dados atuais do MVP podem ser enviados ao Ollama local; nao ha dados sensiveis previstos neste estagio. |
| Operacao | Ambiente local inicialmente, sem dependencia de infraestrutura externa para o piloto tecnico. |
| Seguranca futura | Mesmo sem dados sensiveis atuais, manter autorizacao, isolamento de workspace, logs sem segredos e fronteira de integracao para permitir endurecimento posterior. |

## 13. Cobertura preliminar dos requisitos

| Requisito PRD | Cobertura nesta analise | Pendencia |
|---|---|---|
| REQ-MVP-001 | Isolamento, autorizacao e tenant-scoping | Definir modelo final de organization/workspace |
| REQ-MVP-002 | Criacao e consulta de Product | Confirmar campos, status e permissoes |
| REQ-MVP-003 | Opportunity e relacionamento com Product | Resolver transicao `NEW` / `DISCOVERY` |
| REQ-MVP-004 | Discovery persistida e retomavel | Definir contrato de sessao |
| REQ-MVP-005 | BP, Evidence e Hypothesis relacionados | Definir estados e campos obrigatorios finais |
| REQ-MVP-006 | Initiative derivada do contexto | Definir pre-condicoes de criacao |
| REQ-MVP-007 | Readiness explicavel e versionado | Validar pesos e score minimo |
| REQ-MVP-008 | Aprovacao humana, diff e restricao a `ADMIN`/`PRODUCT_MANAGER` | Validar permissao para avancar status |
| REQ-MVP-009 | Versionamento e auditoria | Escolher snapshot ou versao por agregado |
| REQ-MVP-010 | Operacao manual sem IA | Definir limites de validacao sem provider |
| REQ-MVP-011 | Objectives e Key Results hierarquicos | Definir ciclos de OKR ativos por Product |
| REQ-MVP-012 | Business Plan 5W2H opcional e versionado | Definir se havera visao dedicada na Initiative Detail |

## 14. Conclusao da etapa de analise

A especificacao e coerente o suficiente para iniciar o planejamento tecnico,
mas nao para implementar sem validar as decisoes listadas na secao 12.

A arquitetura deve preservar um fluxo central e tratar OKR, Business Problem e
Business Plan como contexto e estrutura da Initiative. Nao deve criar um
modulo independente de Delivery ou um planejador financeiro no MVP.

Proxima etapa do SDD: criar `docs/plan/implementation-plan.md` somente depois
da validacao das ambiguidades criticas, ou registrar explicitamente as escolhas
provisorias no plano tecnico.
