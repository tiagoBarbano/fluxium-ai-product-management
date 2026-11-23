# 04 - Banco de Dados e Persistência Python

Este documento define as diretrizes para modelagem e persistência em aplicações
Python com MongoDB e, quando necessário, PostgreSQL.

## 1. Princípios

Persistência deve priorizar simplicidade, previsibilidade, baixa latência,
consistência, escalabilidade e baixo consumo de recursos. Evite consultas
desnecessárias, documentos excessivamente grandes, índices sem uso,
collection scans, transações longas e carregamento de grandes volumes.

## 2. Migrations e schema

O schema não deve ser alterado automaticamente pela aplicação em produção.
Para PostgreSQL, utilizar Alembic. Para MongoDB, utilizar migrations explícitas
para índices, validações `$jsonSchema` e transformações de dados.

Scripts devem ser versionados, revisáveis, idempotentes quando possível e
executados no pipeline de deploy. O schema da aplicação deve ser explícito,
mesmo quando o banco for schema-flexible.

## 3. Modelagem MongoDB

Modelar com base nos padrões de acesso, agregados, cardinalidade, frequência de
leitura e escrita e ciclo de vida.

Preferir documentos embutidos quando os dados forem consultados juntos,
possuírem ciclo de vida semelhante e crescimento controlado. Utilizar
referências quando a entidade tiver ciclo de vida independente, for compartilhada
ou puder crescer significativamente.

Nunca criar arrays sem crescimento controlado. Eventos, auditoria, mensagens e
histórico devem normalmente possuir collections próprias.

## 4. Identificadores e isolamento

Todo documento deve possuir `_id`. Usar ObjectId ou identificadores gerados
pela aplicação de forma consistente.

Entidades tenant-scoped devem possuir `tenant_id` e, quando aplicável,
`workspace_id`. O tenant deve vir do contexto autenticado; nunca confiar
exclusivamente em valores enviados pelo cliente.

Toda query tenant-scoped deve incluir o filtro de isolamento. Testes de acesso
entre tenants e workspaces são obrigatórios.

## 5. Collections, tipos e datas

Utilizar uma convenção única para collections. Recomenda-se plural e snake_case,
por exemplo `products`, `initiatives` e `audit_events`.

Utilizar tipos nativos do banco. Datas devem ser armazenadas em UTC como Date.
Valores monetários devem utilizar Decimal128 quando precisão decimal for
necessária. Enumerações devem ser definidas no domínio e não representadas por
strings inconsistentes.

## 6. Repositories

O acesso a MongoDB ou PostgreSQL deve permanecer nos Repositories. Routers,
componentes de apresentação e regras de negócio não podem acessar diretamente
clients, collections ou sessões de banco.

```python
class ProductRepository:
    async def find_by_id(
        self,
        tenant_id: str,
        product_id: str,
    ) -> ProductDocument | None:
        ...
```

Use modelos de persistência separados dos schemas HTTP e converta entre eles
no Mapper ou Service.

## 7. Consultas e projeções

Prioridade:

1. Métodos de Repository com filtros explícitos
2. Driver oficial do banco
3. Aggregation Pipeline
4. SQL parametrizado para PostgreSQL

Utilize projeção quando somente parte do documento for necessária. Aplique
`$match` cedo em aggregation pipelines e evite traversals profundos no caminho
crítico.

## 8. Índices

Defina índices a partir dos padrões reais de consulta. Considere filtros,
ordenação, cardinalidade e frequência de uso. Índices compostos devem começar
pelos campos de igualdade mais seletivos e incluir a ordenação quando aplicável.

Consultas críticas devem ser analisadas com `explain("executionStats")`,
avaliando `executionTimeMillis`, `totalDocsExamined`, `totalKeysExamined` e
`nReturned`.

## 9. Paginação e operações em lote

Nunca carregue grandes volumes sem limite. Utilize ordenação determinística,
cursor pagination e índices compatíveis.

Para grandes volumes, utilize operações bulk ou lotes limitados. Meça memória,
duração, locks e impacto nos índices.

## 10. Concorrência e transações

Prefira controle de versão otimista com `version` ou `updated_at`. Atualizações
devem verificar a versão esperada para evitar sobrescrita silenciosa.

Use transações MongoDB somente quando a consistência entre documentos exigir.
No PostgreSQL, coordene transações no Service e mantenha seu escopo curto.
Nunca execute chamadas HTTP, filas, e-mails ou processamento pesado dentro de
uma transação.

## 11. Exclusão lógica

Quando aplicável, utilize `deleted_at` e filtros padronizados nos Repositories.
Remoções físicas de dados críticos exigem regra explícita, autorização e
auditoria.

## 12. Assincronismo e pools

Utilize `async/await` e o driver assíncrono oficial para operações de I/O. O
pool de conexões deve possuir limites explícitos e ser dimensionado com base no
banco, concorrência e latência. Assincronismo não elimina o limite de conexões.

## 13. Observabilidade e segurança

Monitore latência, erros, pool de conexões, queries lentas, locks e tamanho de
documentos. Utilize OpenTelemetry, Prometheus e logs estruturados.

Nunca construa queries por concatenação. Utilize filtros estruturados ou SQL
parametrizado. Nunca registre segredos ou dados sensíveis sem necessidade.

## 14. Checklist

- [ ] Migrations de schema, índices e dados revisadas
- [ ] Collections e identificadores seguem convenção única
- [ ] Queries tenant-scoped filtram contexto autenticado
- [ ] Índices e projeções foram avaliados
- [ ] Paginação foi aplicada a consultas grandes
- [ ] Não há arrays de crescimento ilimitado
- [ ] Concorrência e versão otimista foram consideradas
- [ ] Transações são curtas e coordenadas no Service
- [ ] Queries críticas possuem análise de execução
- [ ] Logs não expõem dados sensíveis
