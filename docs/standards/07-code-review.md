# Pré-Code Review (Python 3.13+ • FastAPI • MongoDB)

Revise cada alteração como código de produção, priorizando bugs, riscos de
segurança, regressões, performance, operação e ausência de testes.

## 1. Diagnóstico

Classifique o resultado como `Pronto para produção` ou `Requer ajustes antes
do PR`. Liste primeiro problemas concretos, com severidade, impacto e correção.

## 2. Arquitetura

Verifique:

- Router sem regras de negócio ou acesso a banco;
- Service responsável por casos de uso e orquestração;
- Repository responsável por persistência;
- Integration responsável por rede e serviços externos;
- Domain sem dependência de FastAPI ou infraestrutura;
- fronteiras Feature-First respeitadas;
- baixo acoplamento, alta coesão e dependências direcionadas corretamente.

## 3. API e contratos

Verifique URLs, métodos HTTP, status, idempotência, paginação, filtros,
versionamento, schemas Pydantic, OpenAPI e RFC 7807. Confirme que entidades de
domínio e documentos de persistência não são expostos diretamente.

## 4. Validação e segurança

Verifique validações Pydantic e de domínio, autenticação, autorização,
isolamento tenant/workspace, CORS, limites de payload, uploads, SSRF, injeção,
segredos, dados pessoais em logs e ausência de stack traces nas respostas.

## 5. Persistência

Verifique queries tenant-scoped, índices, projeções, paginação, consultas
repetitivas, arrays sem limite, documentos grandes, migrations, concorrência,
transações curtas e uso correto de `async/await`.

Para consultas críticas, avaliar `explain("executionStats")` e a relação entre
documentos examinados e documentos retornados.

## 6. Concorrência e operação

Verifique timeouts, cancelamento, retries, circuit breaker, idempotência,
limites de pool, condições de corrida, jobs duplicados, propagação de
CorrelationId/TraceId e comportamento sob falha de dependências.

## 7. Performance e legibilidade

Analise chamadas de I/O sequenciais desnecessárias, serializações, payloads,
alocações, loops, complexidade, funções longas e uso injustificado de
abstrações. Prefira código explícito e testável.

## 8. Testes

Confirme testes unitários de regras, testes de Router, integração com banco e
integrações externas simuladas. Verifique sucesso, erro, limites, autorização,
isolamento entre tenants, concorrência e idempotência quando aplicável.

## 9. Formato da revisão

Para cada finding, informe:

- severidade: Crítico, Alto, Médio ou Baixo;
- arquivo e contexto;
- problema;
- impacto em produção;
- correção recomendada;
- teste que deve evitar regressão.

Finalize com uma única opção:

- `Aprovado`
- `Aprovado com ajustes`
- `Não aprovado`

## 10. Checklist final

- [ ] Arquitetura Feature-First respeitada
- [ ] API e schemas revisados
- [ ] Segurança e isolamento tenant-scoped revisados
- [ ] Persistência e índices revisados
- [ ] Observabilidade presente
- [ ] Testes adequados executados
- [ ] Performance e operação avaliadas
- [ ] Documentação e rastreabilidade atualizadas
