# 09 - Banco de Dados MongoDB, Persistência e Performance

Este documento define as diretrizes obrigatórias para modelagem, persistência, consultas, índices, transações, versionamento, segurança e performance utilizando MongoDB.

O objetivo é garantir uma camada de persistência **simples, performática, escalável, segura e previsível**.

---

# 1. Princípios

Toda persistência deve priorizar:

- simplicidade;
- previsibilidade;
- baixa latência;
- consistência;
- escalabilidade;
- baixo consumo de recursos.

Evitar:

- consultas desnecessárias;
- documentos excessivamente grandes;
- índices desnecessários;
- collection scans;
- operações sem filtros;
- transações longas;
- carregamento de grandes volumes.

MongoDB é **schema-flexible**, mas não deve ser tratado como **schema-less**.

O schema da aplicação deve ser explicitamente definido.

---

# 2. Persistência

- MongoDB;
- MongoDB Driver / Repository;
- migrations para versionamento de schema, índices e dados.

O acesso ao MongoDB deve permanecer isolado na camada de persistência.

Evitar acesso direto ao banco em:

- Controllers;
- handlers;
- componentes de apresentação;
- regras de negócio.

Exemplo:

```python
class ProductRepository:

    async def find_by_id(
        self,
        tenant_id: str,
        product_id: str
    ):
        ...
```

---

# 3. Modelagem de Documentos

A modelagem deve ser baseada nos **padrões de acesso**, e não na reprodução de um modelo relacional.

Considerar:

- agregados;
- frequência de leitura;
- frequência de escrita;
- cardinalidade;
- tamanho dos documentos;
- necessidade de consistência;
- ciclo de vida dos dados.

## Embedded Documents

Preferir documentos embutidos quando os dados:

- pertencem ao mesmo agregado;
- são normalmente consultados juntos;
- possuem ciclo de vida semelhante;
- não precisam ser consultados independentemente;
- possuem crescimento controlado.

## References

Utilizar referências quando:

- a entidade possui ciclo de vida independente;
- os dados são compartilhados;
- a cardinalidade pode crescer significativamente;
- os dados são consultados independentemente;
- o documento poderia crescer excessivamente.

## Arrays

Arrays devem possuir crescimento controlado.

Nunca criar arrays que possam crescer indefinidamente.

Eventos, logs, histórico ou grandes coleções de itens devem normalmente utilizar collections próprias.

---

# 4. Collections

Utilizar nomenclatura consistente.

Preferir:

```text
PRODUCTS
CUSTOMERS
OFFERS
RULES
WORKFLOWS
AUDIT_LOGS
PRODUCT_VERSIONS
```

Padrão:

- uppercase;
- plural;
- nome representando entidade ou agregado.

Evitar nomes inconsistentes ou derivados de classes técnicas.

---

# 5. Identificadores

Todo documento deve possuir `_id`.

Pode-se utilizar:

- ObjectId;
- identificador gerado pela aplicação;
- identificador com prefixo quando houver benefício arquitetural.

Exemplos:

```text
usr_
prd_
ten_
wsp_
rule_
offer_
```

Não utilizar múltiplos padrões de identificação sem justificativa arquitetural.

---

# 6. Multi-Tenancy

Entidades tenant-scoped devem possuir:

```json
{
  "tenant_id": "tenant_001"
}
```

Quando houver segregação por workspace:

```json
{
  "tenant_id": "tenant_001",
  "workspace_id": "workspace_001"
}
```

Toda consulta tenant-scoped deve considerar o tenant.

Preferir:

```javascript
db.products.find({
    tenant_id: tenantId,
    status: "ACTIVE"
})
```

Nunca confiar exclusivamente em `tenant_id` fornecido pelo cliente.

O tenant deve ser obtido do contexto autenticado e autorizado da requisição.

Testes de isolamento entre tenants são obrigatórios em aplicações multi-tenant.

---

# 7. Schema

Toda entidade persistida deve possuir schema definido na aplicação.

O schema deve definir:

- campos obrigatórios;
- campos opcionais;
- tipos;
- valores permitidos;
- versionamento;
- regras de atualização.

Para collections críticas, avaliar `$jsonSchema` no próprio MongoDB.

A validação do MongoDB não substitui a validação da API.

---

# 8. Tipos de Dados

Utilizar os tipos nativos do MongoDB sempre que possível.

| Tipo lógico | MongoDB |
|---|---|
| String | string |
| Integer | int32 / int64 |
| Decimal | Decimal128 |
| Boolean | bool |
| Data | Date |
| Lista | array |
| Objeto | document |
| Identificador | string / ObjectId |

Valores monetários devem utilizar `Decimal128` quando precisão decimal for necessária.

Evitar `double` para valores monetários.

---

# 9. Datas

Datas devem ser armazenadas como `Date`.

Utilizar UTC.

Exemplo:

```javascript
{
    created_at: ISODate("2026-09-16T10:00:00Z")
}
```

A conversão para timezone local deve ocorrer na camada de apresentação.

Evitar armazenar datas formatadas como texto.

---

# 10. Enumerações e Campos Opcionais

Valores controlados devem utilizar enums definidos pelo domínio.

Exemplo:

```text
DRAFT
ACTIVE
INACTIVE
ARCHIVED
```

Evitar múltiplas representações do mesmo estado.

Para campos opcionais:

- preferir ausência do campo quando isso representar corretamente o domínio;
- utilizar `null` somente quando possuir significado semântico.

---

# 11. Índices

Toda query relevante deve possuir estratégia de índice adequada.

Índices devem ser definidos com base nos **padrões reais de consulta**.

Considerar:

- filtros;
- ordenação;
- cardinalidade;
- frequência de uso;
- tamanho da collection.

Não criar índices indiscriminadamente.

## Índices Compostos

A ordem dos campos deve considerar os filtros e a ordenação da consulta.

Exemplo:

```javascript
{
    tenant_id: 1,
    status: 1,
    created_at: -1
}
```

## Índices Únicos

Utilizar índices únicos quando existir uma regra de unicidade.

Exemplo:

```javascript
{
    tenant_id: 1,
    workspace_id: 1,
    code: 1
}
```

O escopo da unicidade deve refletir o domínio.

---

# 12. Consultas

As queries devem permanecer na camada de persistência.

Prioridade:

1. Repository;
2. consultas simples do driver;
3. Aggregation Pipeline;
4. consultas especializadas quando necessárias.

Evitar espalhar chamadas diretas ao MongoDB pela aplicação.

## Projeção

Quando apenas alguns campos forem necessários, utilizar projeção.

Evitar carregar documentos completos sem necessidade.

## Aggregation

Utilizar Aggregation Pipeline para:

- agrupamentos;
- filtros complexos;
- cálculos;
- transformações;
- consultas analíticas.

Sempre aplicar `$match` o mais cedo possível quando isso reduzir o volume processado.

---

# 13. Performance de Consultas

Consultas críticas devem ser analisadas utilizando:

```javascript
.explain("executionStats")
```

Avaliar principalmente:

```text
executionTimeMillis
totalDocsExamined
totalKeysExamined
nReturned
```

Evitar situações onde muitos documentos são examinados para retornar poucos resultados.

Collection scans devem ser justificados.

---

# 14. Paginação

Nunca carregar grandes volumes sem limite.

Utilizar:

- `limit`;
- ordenação determinística;
- estratégia explícita de paginação.

Para grandes volumes, preferir **cursor pagination**.

A paginação deve utilizar campos estáveis e índices compatíveis.

Exemplo:

```javascript
{
    tenant_id: tenantId,
    created_at: { $lt: lastCreatedAt }
}
```

Quando necessário, utilizar `_id` como critério adicional para garantir ordenação determinística.

---

# 15. Atualizações

Preferir atualizações parciais:

```javascript
db.products.updateOne(
    {
        _id: productId,
        tenant_id: tenantId
    },
    {
        $set: {
            status: "ACTIVE",
            updated_at: new Date()
        }
    }
)
```

Evitar substituir documentos inteiros quando apenas alguns campos precisam ser alterados.

`replaceOne` deve ser utilizado somente quando a substituição integral for intencional.

---

# 16. Operações Destrutivas

Nunca executar operações destrutivas sem filtros adequados.

Evitar:

```javascript
deleteMany({})
updateMany({}, {...})
```

Operações em massa devem possuir:

- escopo definido;
- justificativa;
- testes;
- estratégia de rollback quando aplicável.

---

# 17. Concorrência e Versionamento

Quando houver risco de atualização concorrente, utilizar controle de versão.

Exemplo:

```javascript
{
    _id: "product_001",
    version: 7
}
```

A atualização deve considerar a versão esperada.

Se nenhum documento for atualizado, tratar como possível conflito de concorrência.

Entidades com histórico ou ciclo de publicação devem possuir estratégia explícita de versionamento.

Versões publicadas devem ser imutáveis quando o domínio exigir rastreabilidade.

Alterações posteriores devem criar nova versão.

---

# 18. Transações

Não utilizar transações por padrão.

Antes de utilizar uma transação, avaliar se a consistência pode ser obtida através da modelagem dos documentos.

Operações sobre um único documento são atômicas.

Preferir modelar agregados de forma que alterações que precisam de consistência ocorram no mesmo documento.

Quando uma transação for necessária:

- manter o escopo pequeno;
- evitar operações externas;
- evitar processamento pesado;
- evitar chamadas HTTP;
- evitar processamento de arquivos;
- minimizar o tempo de execução.

---

# 19. Soft Delete

Quando houver necessidade de:

- auditoria;
- histórico;
- recuperação;
- rastreabilidade;

avaliar exclusão lógica.

Exemplo:

```json
{
    "deleted_at": "2026-09-16T10:00:00Z"
}
```

Queries normais devem respeitar a política de exclusão lógica.

---

# 20. Connection Pool

O cliente MongoDB deve ser reutilizado.

Nunca criar uma nova conexão por request.

Modelo:

```text
Application
    |
MongoClient
    |
Connection Pool
    |
MongoDB
```

O pool deve considerar:

- número de réplicas;
- concorrência;
- capacidade do MongoDB;
- latência;
- volume de operações.

Mais conexões não significam necessariamente maior throughput.

---

# 21. Timeouts e Retry

Configurar timeouts explícitos.

Considerar:

```text
serverSelectionTimeoutMS
connectTimeoutMS
socketTimeoutMS
```

Os valores devem considerar o SLA da aplicação.

Retries somente devem ocorrer quando a operação puder ser repetida com segurança.

Avaliar:

- idempotência;
- duplicidade;
- timeout;
- consistência;
- tipo da operação.

---

# 22. Idempotência

Operações críticas que possam ser repetidas devem utilizar idempotência quando necessário.

Exemplo:

```text
POST /release
Idempotency-Key: abc123
```

A chave deve possuir escopo adequado e, quando necessário, índice único.

A operação deve retornar o mesmo resultado para uma mesma chave idempotente.

---

# 23. Auditoria

Operações relevantes devem permitir identificar:

- quem realizou;
- quando ocorreu;
- entidade alterada;
- operação realizada;
- alterações efetuadas.

Exemplo:

```json
{
    "entity": "product",
    "entity_id": "prd_001",
    "action": "UPDATE",
    "tenant_id": "tenant_001",
    "user_id": "user_123",
    "timestamp": "2026-09-16T10:00:00Z"
}
```

Não registrar dados sensíveis sem necessidade.

---

# 24. Observabilidade

A aplicação deve permitir identificar:

- consultas lentas;
- latência;
- quantidade de operações;
- erros;
- timeouts;
- utilização do connection pool;
- conexões;
- operações de leitura;
- operações de escrita.

Preferir:

- OpenTelemetry;
- Prometheus;
- métricas da aplicação;
- logs estruturados.

Evitar logging excessivo de documentos completos em produção.

---

# 25. Cache

Avaliar cache para:

- consultas frequentes;
- dados de referência;
- configurações;
- dados pouco alterados.

Todo cache deve possuir:

- TTL;
- estratégia de invalidação;
- consistência esperada;
- comportamento em caso de falha.

---

# 26. Segurança

Nunca construir queries diretamente a partir de input não validado.

Validar:

- tipos;
- estrutura;
- campos permitidos;
- operadores permitidos.

Não permitir que o cliente controle diretamente operadores MongoDB sem validação explícita.

Exemplo que deve ser tratado com cuidado:

```json
{
    "status": {
        "$ne": null
    }
}
```

Credenciais nunca devem permanecer no código-fonte.

Utilizar:

- environment variables;
- secrets;
- secret managers;
- Docker/Kubernetes Secrets.

---

# 27. Migrations

Alterações de schema, índices ou dados devem possuir estratégia de migration versionada.

Exemplo:

```text
migrations/
├── 001_create_products
├── 002_create_product_indexes
├── 003_add_status
└── 004_migrate_product_code
```

Toda migration deve ser:

- rastreável;
- testável;
- observável;
- idempotente quando possível.

Sempre que possível, realizar alterações backward compatible:

```text
Aplicação antiga
      ↓
Suporte ao formato antigo + novo
      ↓
Migração dos dados
      ↓
Nova versão
      ↓
Remoção do formato antigo
```

---

# 28. Backup

Produção deve possuir estratégia de backup definida.

Definir:

- frequência;
- retenção;
- armazenamento;
- criptografia;
- restauração;
- responsável.

Backups devem possuir testes periódicos de restauração.

---

# 29. Ambientes

Os ambientes devem permanecer isolados:

```text
Development
    ↓
HML
    ↓
Production
```

Nunca utilizar dados de produção diretamente em desenvolvimento sem proteção e anonimização adequadas.

---

# 30. Checklist de Pull Request

## Banco

- [ ] Collection segue o padrão de nomenclatura.
- [ ] Schema definido.
- [ ] Campos obrigatórios definidos.
- [ ] Tipos revisados.
- [ ] Datas armazenadas como `Date`.
- [ ] Migration definida quando necessária.

## Modelagem

- [ ] Embedded vs Reference avaliado.
- [ ] Arrays possuem crescimento controlado.
- [ ] Documentos não possuem crescimento ilimitado.
- [ ] Multi-tenancy corretamente definido.
- [ ] `tenant_id` utilizado quando necessário.
- [ ] `workspace_id` utilizado quando necessário.
- [ ] Versionamento definido quando necessário.

## Consultas

- [ ] Não existem queries desnecessárias.
- [ ] Projeção utilizada quando apropriado.
- [ ] Paginação aplicada.
- [ ] Ordenação determinística.
- [ ] Queries críticas possuem índices adequados.
- [ ] `explain("executionStats")` revisado quando necessário.
- [ ] Não existe collection scan desnecessário.

## Índices

- [ ] Índices necessários criados.
- [ ] Índices compostos possuem ordem adequada.
- [ ] Índices únicos possuem escopo correto.
- [ ] Não existem índices desnecessários.

## Concorrência

- [ ] Concorrência foi avaliada.
- [ ] Controle de versão utilizado quando necessário.
- [ ] Operações críticas são idempotentes quando necessário.

## Transações

- [ ] Transação utilizada somente quando necessária.
- [ ] Escopo da transação é curto.
- [ ] Modelagem não poderia resolver a consistência.
- [ ] Não existem operações externas dentro da transação.

## Performance

- [ ] Volume esperado avaliado.
- [ ] Tamanho dos documentos avaliado.
- [ ] Connection Pool revisado.
- [ ] Timeouts configurados.
- [ ] Queries críticas analisadas.

## Segurança

- [ ] Queries não utilizam input não validado.
- [ ] Operadores MongoDB não são aceitos diretamente sem validação.
- [ ] Secrets não estão no código.
- [ ] Dados sensíveis não são registrados em logs.
- [ ] Isolamento entre tenants testado quando aplicável.

## Observabilidade

- [ ] Métricas disponíveis.
- [ ] Tracing habilitado quando necessário.
- [ ] Logs estruturados.
- [ ] Queries lentas podem ser identificadas.
- [ ] Connection Pool monitorado.

---

# 31. Regras para o GitHub Copilot

Ao gerar código relacionado à persistência MongoDB, seguir obrigatoriamente:

- Utilizar Repository para acesso ao MongoDB.
- Não acessar MongoDB diretamente em Controllers ou regras de negócio.
- Definir explicitamente o schema das entidades.
- Tratar MongoDB como `schema-flexible`, não `schema-less`.
- Utilizar `tenant_id` em entidades tenant-scoped.
- Nunca confiar no `tenant_id` fornecido diretamente pelo cliente.
- Avaliar Embedded Document antes de Reference.
- Não utilizar arrays potencialmente ilimitados.
- Utilizar tipos nativos do MongoDB.
- Armazenar datas como `Date` em UTC.
- Utilizar `Decimal128` quando precisão monetária for necessária.
- Criar índices baseados em padrões reais de consulta.
- Não criar índices indiscriminadamente.
- Utilizar índices compostos considerando filtros e ordenação.
- Utilizar índices únicos para regras de unicidade.
- Utilizar projeção quando apenas parte do documento for necessária.
- Utilizar paginação para grandes volumes.
- Preferir cursor pagination para grandes conjuntos de dados.
- Nunca executar operações destrutivas sem filtros adequados.
- Evitar `deleteMany({})` e `updateMany({})` sem justificativa explícita.
- Utilizar `explain("executionStats")` para consultas críticas.
- Evitar collection scans desnecessários.
- Utilizar Aggregation Pipeline para agregações e transformações.
- Não utilizar transações por padrão.
- Avaliar modelagem antes de utilizar transações.
- Utilizar controle de versão quando houver risco de concorrência.
- Utilizar idempotência em operações críticas quando necessário.
- Não alterar versões publicadas quando forem imutáveis.
- Utilizar soft delete quando houver necessidade de auditoria ou recuperação.
- Reutilizar o MongoClient.
- Não criar conexão por request.
- Configurar connection pool adequadamente.
- Configurar timeouts explícitos.
- Utilizar retry somente quando seguro.
- Nunca construir queries a partir de input não validado.
- Não permitir operadores MongoDB diretamente do cliente sem validação.
- Nunca armazenar credentials no código.
- Não registrar dados sensíveis em logs.
- Toda alteração relevante deve possuir migration.
- Toda alteração de persistência deve possuir testes.
- Testar isolamento entre tenants.
- Priorizar código simples, performático, observável e adequado para produção.