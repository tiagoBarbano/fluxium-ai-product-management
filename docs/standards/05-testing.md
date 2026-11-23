# 05 - Estratégia e Padrões de Testes

Este documento define os padrões de testes para aplicações Python 3.13+,
FastAPI e MongoDB.

## 1. Princípios

Testes devem ser rápidos, determinísticos, independentes, legíveis e
executáveis em qualquer ambiente. Código de teste possui a mesma importância
do código de produção.

## 2. Pirâmide de testes

Manter aproximadamente 70% de testes unitários, 20% de integração e 10% de
E2E. A proporção é uma orientação; regras críticas e fluxos de risco podem
exigir cobertura adicional.

## 3. Testes unitários

Validam domínio, Services, cálculos, validações e casos de uso sem banco,
rede, filesystem ou aplicação completa. Utilizar pytest, fixtures,
parametrização e `unittest.mock` apenas para dependências externas.

```python
def test_deve_calcular_desconto_quando_cliente_for_vip() -> None:
    customer = CustomerFixture.vip()

    result = service.calculate(customer)

    assert result == Decimal("10")
```

Nomes devem descrever o comportamento, por exemplo:
`test_deve_rejeitar_email_duplicado`.

## 4. Testes de Router e contrato

Utilizar `TestClient` ou `httpx.AsyncClient` para validar rotas, schemas,
serialização, autenticação, autorização, códigos HTTP e respostas RFC 7807.
Não subir infraestrutura desnecessária quando apenas o contrato HTTP estiver
sendo testado.

## 5. Testes de integração

Validar integração entre Services, Repositories, banco, migrations, filas e
integrações simuladas. Utilizar Testcontainers quando possível e o mesmo banco
da produção. Para MongoDB, validar índices, projeções e filtros de isolamento;
para PostgreSQL, executar migrations Alembic reais.

## 6. APIs externas

Nunca depender de serviços externos reais. Utilizar `respx`, `pytest_httpx`,
servidor fake local ou Testcontainers conforme o protocolo. Testes devem ser
reproduzíveis offline.

## 7. Assincronismo e concorrência

Utilizar `pytest-asyncio` quando necessário. Não utilizar `time.sleep` para
sincronizar testes; prefira eventos, polling com timeout explícito ou fixtures
determinísticas. Validar timeout, cancelamento, propagação de contexto,
exceções e idempotência em tarefas concorrentes.

## 8. Fixtures e isolamento

Centralizar fixtures reutilizáveis, sem esconder regras do cenário. Cada teste
deve preparar seus dados, executar e validar sem depender da ordem de execução
ou de dados persistidos por outro teste. Testes tenant-scoped devem verificar
explicitamente que um workspace não acessa dados de outro.

## 9. Casos obrigatórios

Todo caso de uso deve cobrir sucesso, entrada inválida, autorização negada,
recurso inexistente, conflito de versão, limites, listas vazias, valores
opcionais, timeout e falhas de dependência quando aplicável.

## 10. E2E com Playwright

Usar Playwright para fluxos críticos observáveis pelo usuário, com locators
semânticos e organização feature-first. Não testar detalhes internos do React.

## 11. Cobertura e performance

Cobertura é indicador, não objetivo isolado. Priorize regras de negócio,
fluxos críticos e erros. Evite iniciar a aplicação completa em testes unitários
e meça duração dos testes lentos.
