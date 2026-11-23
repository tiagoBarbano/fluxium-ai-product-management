# 03 - Padrões de API REST e FastAPI

Este documento define as diretrizes obrigatórias para APIs REST com Python
3.13+, FastAPI, Pydantic 2+ e OpenAPI.

## 1. Princípios

Toda API deve ser RESTful, versionada, segura, observável, documentada e
compatível com OpenAPI. Priorize recursos e evite endpoints orientados a ações
quando um recurso representar corretamente o comportamento.

## 2. Recursos e URLs

Utilize substantivos no plural, kebab-case e no máximo dois níveis de
hierarquia:

```text
/api/v1/customers
/api/v1/customers/{id}/addresses
```

Evite `/getCustomers`, `/createCustomer`, snake_case e hierarquias profundas.

## 3. Métodos e status HTTP

| Método | Uso |
|---|---|
| GET | Consulta |
| POST | Criação ou comando assíncrono explícito |
| PUT | Atualização completa |
| PATCH | Atualização parcial |
| DELETE | Remoção |

Utilize 200, 201, 202, 204, 400, 401, 403, 404, 409, 422, 429 e 500 conforme
o significado da operação. Não retorne HTTP 200 para representar erro.

## 4. Routers

Routers FastAPI devem receber requisições, validar schemas, extrair parâmetros,
chamar Services e converter resultados em respostas. Não devem conter regras
de negócio, acesso ao banco, SQL, queries MongoDB ou chamadas externas.

```python
@router.post("/customers", response_model=CustomerResponse, status_code=201)
async def create_customer(
    request: CreateCustomerRequest,
    service: CustomerService = Depends(get_customer_service),
) -> CustomerResponse:
    return await service.create(request)
```

## 5. Schemas de entrada e saída

Toda comunicação deve utilizar schemas Pydantic. Nunca exponha entidades de
domínio ou documentos de persistência diretamente.

```python
class CreateCustomerRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr


class CustomerResponse(BaseModel):
    id: str
    name: str
    email: EmailStr
```

Use modelos separados para request, response e persistência. A validação de
contrato ocorre no Pydantic; regras de negócio permanecem no Service/domínio.

## 6. Erros RFC 7807

As respostas de erro devem utilizar `application/problem+json`, com status,
title, detail, timestamp e traceId quando disponível. Centralize o tratamento
com `@app.exception_handler` ou handlers registrados na aplicação. Nunca
exponha stack traces ao cliente.

## 7. Paginação, filtros e ordenação

Consultas potencialmente grandes devem utilizar `limit`, cursor estável,
ordenação determinística e limites máximos. Filtros devem ser query
parameters. Campos de ordenação devem ser explicitamente autorizados.

```python
@router.get("/customers", response_model=CustomerPage)
async def list_customers(
    limit: int = Query(default=20, ge=1, le=100),
    cursor: str | None = None,
) -> CustomerPage:
    return await service.list_customers(limit=limit, cursor=cursor)
```

## 8. Idempotência

Operações críticas e comandos assíncronos devem aceitar `X-Idempotency-Key`.
O resultado da primeira execução deve ser reutilizado para requisições
repetidas com a mesma chave e escopo.

## 9. Segurança

Utilize HTTPS, autenticação no header `Authorization`, autorização por recurso
e validação de entrada. Nunca envie segredos em URLs, query parameters ou logs.
Derive tenant e workspace do contexto autenticado, não de valores confiados
enviados pelo cliente.

Nunca utilize origem CORS curinga em produção; configure origens explícitas.

## 10. OpenAPI e headers

Mantenha a especificação OpenAPI gerada pelo FastAPI atualizada. Considere
`Authorization`, `Correlation-Id`, `Trace-Id`, `Accept`, `Content-Type` e
`X-Idempotency-Key` quando aplicável.

## 11. Assincronismo

Operações longas, como assessments e geração de contexto de IA, devem ser
assíncronas. Retorne 202 com identificador de job quando não puder concluir
rapidamente. Para streaming, utilize SSE ou WebSocket conforme o contrato.

## 12. Checklist

- [ ] Router sem regra de negócio ou acesso direto à infraestrutura
- [ ] Schemas Pydantic de entrada e saída definidos
- [ ] Status HTTP e erros RFC 7807 corretos
- [ ] Paginação e limites aplicados
- [ ] Autenticação, autorização e isolamento tenant-scoped revisados
- [ ] CorrelationId, TraceId e logs estruturados preservados
- [ ] OpenAPI atualizado
- [ ] Timeouts, idempotência e processamento assíncrono avaliados
