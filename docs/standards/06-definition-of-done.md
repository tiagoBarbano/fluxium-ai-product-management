# Definition of Done (DoD)
## Python 3.13+ • FastAPI • MongoDB

Uma funcionalidade somente está pronta quando pode operar em produção com
segurança, previsibilidade, observabilidade e manutenção sustentável.

## Arquitetura

- [ ] Router, Service, Repository, Domain e Integration possuem responsabilidades separadas
- [ ] Routers não contêm regras de negócio nem acesso à infraestrutura
- [ ] Repositories são o único acesso ao banco
- [ ] Dependências seguem Feature-First e não há imports indevidos entre features
- [ ] Type hints estão presentes e `Any` possui justificativa

## API

- [ ] Verbos, URLs e status HTTP seguem o padrão REST
- [ ] Schemas Pydantic de entrada e saída estão definidos
- [ ] Validação de contrato e regras de negócio estão separadas
- [ ] Erros seguem RFC 7807 sem stack traces
- [ ] Paginação, limites, filtros e ordenação foram revisados
- [ ] OpenAPI está atualizado
- [ ] Idempotência foi implementada quando aplicável

## Regras de negócio

- [ ] Regras estão centralizadas no Service ou domínio
- [ ] Transições de estado e pré-condições foram validadas
- [ ] Autorização por recurso foi implementada
- [ ] Isolamento entre organizations e workspaces foi validado
- [ ] Alterações relevantes geram auditoria

## Persistência

- [ ] Migrations de schema, índices e dados estão versionadas
- [ ] Queries usam filtros tenant-scoped
- [ ] Índices, projeções e paginação foram avaliados
- [ ] Não há arrays MongoDB sem crescimento controlado
- [ ] Controle de concorrência foi considerado
- [ ] Transações são curtas e não envolvem I/O externo

## Segurança

- [ ] Entrada, autenticação e autorização foram validadas
- [ ] Segredos não aparecem no frontend ou no código
- [ ] Logs não contêm dados sensíveis desnecessários
- [ ] Queries não usam concatenação insegura
- [ ] Erros não expõem detalhes internos

## Observabilidade e operação

- [ ] Logs estruturados, CorrelationId e TraceId estão disponíveis
- [ ] Métricas e tracing foram adicionados quando relevantes
- [ ] Timeouts, retries e circuit breaker foram avaliados para integrações
- [ ] Jobs assíncronos possuem estado, timeout, retry e idempotência
- [ ] Consumo de CPU, memória, conexões e latência foi avaliado

## Testes

- [ ] Testes unitários cobrem regras de negócio
- [ ] Testes de integração cobrem persistência e integrações relevantes
- [ ] Cenários inválidos, erros, limites e isolamento tenant-scoped foram testados
- [ ] Fluxos críticos possuem testes E2E quando aplicável
- [ ] Todos os testes passam sem dependências externas não controladas

## Qualidade e documentação

- [ ] Não há warnings relevantes, código morto ou TODOs esquecidos
- [ ] Documentação, OpenAPI e migrations foram atualizados
- [ ] Rastreabilidade requisito, código e teste foi atualizada
- [ ] Code review foi concluído
- [ ] Não há bugs conhecidos sem aceite formal
