# 01 - Arquitetura e Estrutura do Projeto

Este documento define a arquitetura padrão, as responsabilidades das camadas, as regras de dependência e os princípios arquiteturais obrigatórios para projetos Python modernos, especialmente APIs desenvolvidas com FastAPI.

---

# 1. Plataforma

## Linguagem

- Python 3.13 ou superior
- Utilizar type hints obrigatoriamente.
- Preferir recursos modernos da linguagem.
- Evitar APIs e padrões obsoletos.

## Framework

- FastAPI
- Pydantic 2+ ou msgspec
- Starlette
- gunicorn com asgi
- aiohttp
- aiocache
- orjson

## Persistência SQL

- Raw (Linhas SQL)
- PostgreSQL (preferencial)
- Alembic para versionamento de schema e migrations

## Persistência NoSQL

- MongoDB
- PyMongo / driver assíncrono oficial, conforme necessidade da aplicação
- Migrations específicas para índices, estruturas e dados quando aplicável

## Gerenciamento de dependências

Preferencialmente:

- uv

Alternativas aceitáveis:

- pip + requirements

O projeto deve possuir lockfile quando o gerenciador utilizado oferecer esse recurso.

## Qualidade de código

- pytest
- pytest-asyncio, quando necessário

## Observabilidade

- OpenTelemetry
- Prometheus
- Structured Logging
- Health Checks
- TraceId
- CorrelationId

---

# 2. Princípios Arquiteturais

A arquitetura deve seguir os princípios:

- SOLID
- Clean Code
- Separation of Concerns
- Dependency Inversion
- Composition over Inheritance
- Domain Driven Design, quando aplicável
- Fail Fast
- Explicit is better than implicit
- Type Safety
- Imutabilidade sempre que possível
- Baixo acoplamento
- Alta coesão
- Testabilidade

Python permite soluções extremamente compactas. Isso não deve ser utilizado como justificativa para concentrar múltiplas responsabilidades em uma única função ou classe.

Código curto não significa código simples.

---

# 3. Arquitetura

O projeto utiliza uma arquitetura em camadas com organização Feature-First.

Fluxo principal:

```text
Cliente
   │
   ▼
Router
   │
   ▼
Service
   │
   ├──────────────► Integration
   │
   ▼
Repository
   │
   ▼
Banco de Dados
```

O fluxo deve ocorrer preferencialmente nesta direção.

Uma camada não deve acessar outra pulando níveis.

Exemplos proibidos:

```text
Router → Repository
```

```text
Router → SQLAlchemy Session
```

```text
Router → MongoDB
```

```text
Router → HTTP Client
```

```text
Domain → FastAPI
```

```text
Repository → Router
```

```text
Repository → Service
```

---

# 4. Organização do Projeto

Padrão oficial:

**Feature-First com camadas internas.**

Cada domínio funcional deve agrupar seus artefatos técnicos em um pacote de feature.

Componentes transversais permanecem em pacotes compartilhados no nível raiz.

Estrutura recomendada:

```text
project/
│
├── app/
│   │
│   ├── main.py
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py
│   │   └── logging.py
│   │
│   ├── exception/
│   │   ├── __init__.py
│   │   ├── handlers.py
│   │   └── exceptions.py
│   │
│   ├── security/
│   │   ├── __init__.py
│   │   ├── authentication.py
│   │   └── authorization.py
│   │
│   ├── telemetry/
│   │   ├── __init__.py
│   │   ├── tracing.py
│   │   └── metrics.py
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   ├── sql.py
│   │   ├── mongo.py
│   │   └── migrations/
│   │
│   ├── shared/
│   │   ├── __init__.py
│   │   ├── pagination.py
│   │   ├── types.py
│   │   └── utils.py
│   │
│   └── features/
│       │
│       ├── oferta/
│       │   ├── __init__.py
│       │   │
│       │   ├── router.py
│       │   ├── service.py
│       │   ├── repository.py
│       │
│       │   ├── domain/
│       │   │   ├── entity.py
│       │   │   ├── value_objects.py
│       │   │   ├── enums.py
│       │   │   └── events.py
│       │   │
│       │   ├── schemas/
│       │   │   ├── request.py
│       │   │   └── response.py
│       │   │
│       │   ├── mapper.py
│       │   ├── validation.py
│       │   │
│       │   └── integration/
│       │       ├── external_api.py
│       │       └── clients.py
│       │
│       └── experimento/
│           ├── __init__.py
│           ├── router.py
│           ├── service.py
│           ├── repository.py
│           ├── domain/
│           ├── schemas/
│           │   ├── request.py
│           │   └── response.py
│           ├── mapper.py
│           ├── validation.py
│           └── integration/
│
├── tests/
│   ├── unit/
│   │   └── features/
│   │       ├── oferta/
│   │       └── experimento/
│   │
│   └── integration/
│       └── features/
│
├── pyproject.toml
├── uv.lock
├── alembic.ini
├── Dockerfile
└── README.md
```

---

# 5. Regras de Organização

A organização deve permanecer consistente entre todos os projetos.

Regras obrigatórias:

- Não criar `router`, `service` ou `repository` genéricos no nível raiz.
- Novas capacidades devem nascer dentro de `features/<nome-da-feature>`.
- Código específico de uma feature deve permanecer dentro dela.
- Código compartilhado entre features deve ficar em módulos transversais.
- Não criar `utils.py` gigantes.
- Não utilizar `shared` como depósito de código sem responsabilidade clara.
- Dependências entre features devem ser minimizadas.
- Uma feature não deve acessar diretamente o repository interno de outra feature.
- Integrações externas devem permanecer dentro de `integration`.

---

# 6. Responsabilidade das Camadas

## Router

O Router é responsável pela interface HTTP.

Responsabilidades:

- receber requisições;
- validar entrada;
- extrair parâmetros;
- autenticar/autorização quando aplicável;
- chamar Services;
- converter resultado em Response;
- definir status HTTP.

Não deve conter:

- regras de negócio;
- acesso ao banco;
- chamadas HTTP externas;
- SQL;
- queries MongoDB;
- cálculos de negócio;
- transações.

Exemplo:

```python
@router.post(
    "/ofertas",
    response_model=OfertaResponse,
)
async def criar_oferta(
    request: CriarOfertaRequest,
    service: OfertaService = Depends(get_oferta_service),
) -> OfertaResponse:

    oferta = await service.criar(request)

    return OfertaResponse.from_domain(oferta)
```

O Router deve permanecer fino.

---

# 7. Service

O Service é responsável pela aplicação das regras de negócio e pela orquestração dos casos de uso.

Responsabilidades:

- executar casos de uso;
- aplicar regras de negócio;
- coordenar repositories;
- coordenar integrações;
- controlar transações;
- controlar idempotência quando aplicável;
- executar validações de negócio;
- publicar eventos quando necessário.

Exemplo:

```python
class OfertaService:

    def __init__(
        self,
        repository: OfertaRepository,
        integration: OfertaIntegration,
    ):
        self.repository = repository
        self.integration = integration

    async def criar(
        self,
        request: CriarOfertaRequest,
    ) -> Oferta:

        oferta = Oferta.criar(
            nome=request.nome,
        )

        await self.repository.save(oferta)

        return oferta
```

O Service não deve conhecer detalhes de HTTP.

Não deve utilizar:

```python
Request
Response
HTTPException
status_code
```

como parte da regra de negócio.

Quando possível, exceções de domínio/aplicação devem ser independentes de FastAPI.

---

# 8. Repository

Repository é responsável exclusivamente pelo acesso aos dados.

Responsabilidades:

- persistir entidades;
- consultar dados;
- atualizar dados;
- remover dados;
- executar queries;
- mapear persistência para domínio.

Não deve conter:

- regras de negócio;
- regras de autorização;
- chamadas HTTP externas;
- decisões de negócio;
- lógica de workflow.

Exemplo:

```python
class OfertaRepository:

    def __init__(self, database):
        self.database = database

    async def find_by_id(
        self,
        oferta_id: str,
    ) -> Oferta | None:

        document = await self.database.ofertas.find_one(
            {"_id": oferta_id}
        )

        if document is None:
            return None

        return OfertaMapper.from_document(document)
```

---

# 9. Domain

O Domain representa o modelo de negócio.

Pode conter:

- Entities;
- Value Objects;
- Enums;
- Domain Events;
- Domain Services;
- invariantes;
- regras de domínio.

O Domain deve possuir o mínimo possível de dependências externas.

Evitar dependências diretas de:

- FastAPI;
- HTTP;
- MongoDB;
- SQLAlchemy;
- Redis;
- Kafka;
- bibliotecas de infraestrutura.

Exemplo:

```python
@dataclass
class Oferta:

    id: str
    nome: str
    ativa: bool

    def ativar(self) -> None:

        if self.ativa:
            raise OfertaJaAtivaError()

        self.ativa = True
```

O domínio deve proteger suas próprias invariantes.

---

# 10. Schemas

Schemas representam contratos externos da aplicação.

Utilizar Pydantic.

Exemplo:

```python
class CriarOfertaRequest(BaseModel):

    nome: str = Field(min_length=1, max_length=200)
    produto_id: str
```

Response:

```python
class OfertaResponse(BaseModel):

    id: str
    nome: str
    ativa: bool
```

Nunca retornar diretamente entidades de domínio ou modelos de persistência quando isso expuser detalhes internos.

Fluxo:

```text
Request Schema
      ↓
Router
      ↓
Service
      ↓
Domain
      ↓
Repository
      ↓
Domain
      ↓
Response Schema
```

---

# 11. Pydantic

Pydantic deve ser utilizado para:

- validação de entrada;
- configuração;
- contratos de API;
- serialização;
- desserialização.

Não utilizar Pydantic como substituto automático de todas as entidades de domínio.

Quando existir comportamento ou invariantes relevantes, preferir entidades de domínio próprias.

---

# 12. Mapper

Mappers são responsáveis pela conversão entre modelos.

Exemplos:

```text
Request Schema
      ↓
Domain Entity
```

```text
Database Document
      ↓
Domain Entity
```

```text
Domain Entity
      ↓
Response Schema
```

Não concentrar regras de negócio em Mappers.

Exemplo:

```python
class OfertaMapper:

    @staticmethod
    def from_document(document: dict) -> Oferta:
        return Oferta(
            id=str(document["_id"]),
            nome=document["nome"],
            ativa=document["ativa"],
        )
```

---

# 13. Dependency Injection

Utilizar Dependency Injection explicitamente.

Preferir:

```python
class OfertaService:

    def __init__(
        self,
        repository: OfertaRepository,
    ):
        self.repository = repository
```

E no FastAPI:

```python
def get_oferta_service(
    repository: OfertaRepository = Depends(
        get_oferta_repository
    ),
) -> OfertaService:

    return OfertaService(repository)
```

Evitar:

```python
repository = OfertaRepository()
```

espalhado pelo código.

Evitar também:

```python
class OfertaService:

    def __init__(self):
        self.repository = MongoOfertaRepository()
```

quando isso criar acoplamento desnecessário à infraestrutura.

---

# 14. Async / Await

Operações de I/O devem utilizar `async/await` quando o driver ou biblioteca utilizada possuir suporte assíncrono apropriado.

Exemplos:

- HTTP;
- MongoDB;
- PostgreSQL;
- Redis;
- filas;
- serviços externos.

Exemplo:

```python
async def buscar_oferta(
    oferta_id: str,
) -> Oferta:

    return await repository.find_by_id(oferta_id)
```

Não utilizar chamadas bloqueantes dentro de endpoints assíncronos.

Evitar:

```python
async def endpoint():
    requests.get(...)
```

quando a operação puder bloquear o event loop.

Para bibliotecas exclusivamente síncronas, utilizar mecanismos apropriados para isolamento do trabalho bloqueante.

---

# 15. Concorrência

Python não deve utilizar threads indiscriminadamente como substituição de `async/await`.

Para aplicações FastAPI:

- I/O assíncrono → `async/await`;
- CPU-bound → processo separado, worker apropriado ou infraestrutura dedicada;
- tarefas curtas bloqueantes → mecanismo apropriado de thread pool;
- tarefas assíncronas → event loop.

A escolha deve considerar o tipo de carga.

---

# 16. Transações

Transações pertencem ao Service ou a uma abstração de Unit of Work.

Nunca controlar transações diretamente no Router.

Evitar:

```python
@router.post(...)
async def endpoint():

    await db.begin()

    ...
```

Preferir:

```python
async def executar_caso_de_uso():

    async with unit_of_work:

        ...
```

ou mecanismo equivalente fornecido pela infraestrutura.

A transação deve abranger o caso de uso necessário e não toda a requisição HTTP indiscriminadamente.

---

# 17. Unit of Work

Quando houver múltiplas operações persistentes que precisam ser atômicas, utilizar Unit of Work.

Exemplo conceitual:

```python
async with unit_of_work:

    await repository.save(entity)

    await repository.save(other_entity)

    await unit_of_work.commit()
```

A implementação deve permanecer desacoplada da camada HTTP.

---

# 18. Integrações Externas

Toda comunicação externa deve estar isolada em `integration`.

Exemplos:

```text
integration/
├── payment_client.py
├── customer_client.py
├── kafka_client.py
└── redis_client.py
```

Responsabilidades:

- comunicação HTTP;
- autenticação externa;
- serialização externa;
- timeout;
- retry;
- circuit breaker;
- tratamento de erros de infraestrutura;
- observabilidade.

Jamais espalhar chamadas HTTP pelo projeto.

Proibido:

```python
async def criar_oferta():
    await http_client.post(...)
```

quando essa chamada representa uma integração externa que deveria estar encapsulada.

Preferir:

```python
await customer_integration.create_customer(...)
```

---

# 19. HTTP Clients

Toda chamada HTTP externa deve possuir:

- timeout explícito;
- tratamento de erros;
- retry quando apropriado;
- circuit breaker quando necessário;
- logs;
- métricas;
- tracing.

Nunca utilizar chamadas HTTP sem timeout.

Evitar:

```python
await client.get(url)
```

sem política de timeout definida.

---

# 20. Tratamento de Exceções

Exceções devem ser classificadas.

Exemplos:

```text
DomainException
ApplicationException
ValidationException
NotFoundException
ConflictException
IntegrationException
InfrastructureException
```

Exceções de domínio não devem depender de FastAPI.

Exemplo:

```python
class OfertaNaoEncontradaError(
    ApplicationException
):
    pass
```

O mapeamento para HTTP deve ocorrer em handlers centralizados.

Exemplo:

```python
@app.exception_handler(
    OfertaNaoEncontradaError
)
async def handle_oferta_nao_encontrada(
    request,
    exc,
):
    return JSONResponse(
        status_code=404,
        content={
            "code": "OFERTA_NOT_FOUND",
            "message": "Oferta não encontrada",
        },
    )
```

Nunca retornar stack trace para o cliente.

Nunca capturar exceções apenas para executar:

```python
print(exc)
```

---

# 21. Logging

Utilizar Structured Logging.

Preferir:

```json
{
  "level": "INFO",
  "event": "oferta_created",
  "oferta_id": "123",
  "trace_id": "..."
}
```

Evitar:

```python
print("Oferta criada")
```

Logs devem permitir correlação por:

- request_id;
- correlation_id;
- trace_id;
- tenant_id, quando aplicável;
- user_id, quando apropriado e permitido.

Nunca registrar:

- senhas;
- tokens;
- secrets;
- credenciais;
- dados sensíveis desnecessários.

---

# 22. Observabilidade

Toda aplicação deve possuir:

- OpenTelemetry;
- tracing;
- métricas;
- structured logging;
- health checks;
- readiness;
- liveness;
- correlation_id;
- trace_id.

Exemplos de métricas:

```text
http_requests_total
http_request_duration_seconds
database_operation_duration_seconds
external_api_requests_total
external_api_errors_total
```

A instrumentação deve permitir identificar:

```text
HTTP
 ↓
Service
 ↓
Database
 ↓
External API
```

dentro do mesmo trace quando aplicável.

---

# 23. Health Checks

A aplicação deve possuir pelo menos:

```text
/health
```

e, quando necessário:

```text
/ready
```

Health check deve distinguir:

- aplicação funcionando;
- aplicação pronta para receber tráfego;
- dependência indisponível.

Não utilizar um health check complexo que transforme uma falha de dependência temporária em indisponibilidade total sem necessidade.

---

# 24. Segurança

Toda API deve possuir:

- autenticação;
- autorização;
- validação de entrada;
- proteção de informações sensíveis;
- controle de acesso;
- rate limiting quando necessário;
- validação de tokens;
- configuração segura de CORS.

Nunca confiar em dados enviados pelo cliente.

Nunca colocar:

```python
SECRET_KEY = "..."
```

diretamente no código.

Utilizar configuração externa:

```python
class Settings(BaseSettings):

    secret_key: str
```

Secrets devem ser fornecidos por:

- environment variables;
- secret manager;
- infraestrutura segura.

Nunca versionar secrets no Git.

---

# 25. Configuração

Configurações devem ser centralizadas.

Exemplo:

```python
class Settings(BaseSettings):

    app_name: str
    environment: str

    mongodb_uri: str

    redis_url: str

    jwt_secret: str

    model_config = SettingsConfigDict(
        env_file=".env"
    )
```

Utilizar:

```python
settings = Settings()
```

Não espalhar:

```python
os.getenv(...)
```

por todo o projeto.

---

# 26. Banco de Dados

O código de negócio não deve depender diretamente da implementação específica do banco.

Exemplo proibido:

```python
async def criar_oferta():
    await db.ofertas.insert_one(...)
```

dentro de um Service.

Preferir:

```python
await oferta_repository.save(oferta)
```

O Repository encapsula detalhes da persistência.

---

# 27. MongoDB

Para MongoDB:

- Repository encapsula queries;
- índices devem ser definidos e versionados;
- queries devem possuir critérios claros;
- evitar consultas sem filtros em coleções grandes;
- utilizar projeções quando apropriado;
- evitar retornar documentos gigantes desnecessariamente;
- controlar paginação;
- considerar índices para consultas críticas.

Não espalhar objetos `dict` de MongoDB pelo domínio.

Converter:

```text
Mongo Document
      ↓
Mapper
      ↓
Domain Entity
```

---

# 28. SQL

Quando utilizado PostgreSQL/SQL:

- SQLAlchemy 2+;
- Alembic;
- Repository para acesso;
- transações controladas pelo Service/Unit of Work;
- migrations versionadas.

Não executar SQL diretamente dentro de Routers.

Não espalhar `Session` pela aplicação.

---

# 29. DTOs e Entidades

Não confundir:

```text
API Schema
```

com:

```text
Domain Entity
```

nem com:

```text
Database Model
```

A arquitetura preferencial é:

```text
Request Schema
      ↓
Domain
      ↓
Repository
      ↓
Database Model
```

e:

```text
Database Model
      ↓
Domain
      ↓
Response Schema
```

Essa separação permite alterar a API ou o banco sem alterar necessariamente o domínio.

---

# 30. Tipagem

Type hints são obrigatórios.

Preferir:

```python
def calcular(
    valor: Decimal,
    percentual: Decimal,
) -> Decimal:
    ...
```

Evitar:

```python
def calcular(valor, percentual):
    ...
```

Evitar `Any` sem justificativa.

Quando `Any` for inevitável, documentar o motivo.

Preferir:

```python
list[str]
dict[str, str]
str | None
```

em vez de:

```python
List[str]
Dict[str, str]
Optional[str]
```

em código compatível com Python moderno.

---

# 31. Dataclasses

Utilizar `dataclass` quando apropriado para objetos de domínio simples.

Exemplo:

```python
@dataclass(frozen=True)
class Money:

    amount: Decimal
    currency: str
```

Preferir objetos imutáveis quando não houver necessidade de mutabilidade.

---

# 32. Enums

Utilizar enums para estados e valores finitos.

Exemplo:

```python
class OfertaStatus(str, Enum):

    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
```

Evitar espalhar strings mágicas:

```python
if status == "ACTIVE":
```

quando o valor representar um conceito de domínio.

Preferir:

```python
if status == OfertaStatus.ACTIVE:
```

---

# 33. Regras de Dependência

## Permitido

```text
Router
   ↓
Service
   ↓
Repository
```

```text
Service
   ↓
Integration
```

```text
Service
   ↓
Mapper
```

```text
Service
   ↓
Domain
```

```text
Repository
   ↓
Mapper
   ↓
Domain
```

---

# 34. Proibido

```text
Router
   ↓
Repository
```

```text
Router
   ↓
MongoDB
```

```text
Router
   ↓
SQLAlchemy
```

```text
Router
   ↓
External API
```

```text
Repository
   ↓
Service
```

```text
Repository
   ↓
Router
```

```text
Domain
   ↓
FastAPI
```

```text
Domain
   ↓
MongoDB
```

```text
Domain
   ↓
HTTP Client
```

---

# 35. Feature-to-Feature

Features devem possuir baixo acoplamento.

Evitar:

```text
Oferta
   ↓
ExperimentoRepository
```

Preferir:

```text
Oferta
   ↓
ExperimentoService
```

quando a regra realmente representar uma dependência de negócio.

Quando a comunicação entre features tornar-se complexa, considerar:

- Domain Events;
- Application Events;
- mensagens;
- contratos explícitos;
- módulo compartilhado.

---

# 36. Background Tasks

Tarefas assíncronas não devem ser utilizadas para esconder operações críticas.

Para tarefas simples e curtas:

```text
FastAPI BackgroundTasks
```

pode ser suficiente.

Para tarefas:

- longas;
- críticas;
- reprocessáveis;
- distribuídas;
- com retry;
- com garantia de entrega;

preferir mecanismos dedicados:

- Celery;
- RabbitMQ;
- Kafka;
- Redis Streams;
- outro mecanismo apropriado.

---

# 37. Idempotência

Endpoints que representam operações críticas devem considerar idempotência.

Exemplo:

```text
POST /payments
```

pode utilizar:

```text
Idempotency-Key
```

A responsabilidade deve permanecer na camada apropriada da aplicação/infraestrutura.

O Service deve garantir que a operação de negócio não seja executada duas vezes quando o contrato exigir idempotência.

---

# 38. Testes

Toda funcionalidade deve possuir testes adequados.

Estrutura:

```text
tests/
├── unit/
└── integration/
```

Testes unitários devem testar:

- regras de domínio;
- Services;
- validações;
- Mappers.

Testes de integração devem testar:

- banco;
- APIs;
- integrações;
- configuração;
- contratos relevantes.

---

# 39. Testes de Router

Routers devem ser testados separadamente dos Services quando necessário.

Evitar transformar todo teste de API em teste de integração.

Quando o objetivo for testar o comportamento HTTP:

```text
HTTP
 ↓
Router
 ↓
Mock Service
```

Quando o objetivo for testar regra de negócio:

```text
Service
 ↓
Mock Repository
```

---

# 40. Mocking

Mocks devem ser utilizados com moderação.

Preferir:

- dependency injection;
- fake repositories;
- fixtures;
- test doubles explícitos.

Evitar mockar internals excessivamente.

O teste deve verificar comportamento, não detalhes de implementação.

---

# 41. Qualidade de Código

Todo projeto deve utilizar ferramentas automáticas de qualidade.

Preferencialmente:

```text
Ruff
pytest
```

Exemplo:

```text
ruff check .
ruff format --check .
pytest
```

O pipeline CI deve falhar quando houver erros críticos de qualidade ou testes.

---

# 42. Formatação

Utilizar formatação automática.

Preferir:

```text
Ruff Formatter
```

Não discutir formatação manualmente em Pull Requests quando a regra puder ser automatizada.

Código deve ser formatado automaticamente antes do commit ou no CI.

---

# 43. Imports

Imports devem ser organizados automaticamente.

Evitar:

```python
import *
```

Nunca utilizar:

```python
from module import *
```

Preferir imports explícitos.

---

# 44. Funções

Funções devem possuir responsabilidade única.

Evitar funções gigantes:

```python
async def processar_oferta():
    # 300 linhas
```

Preferir composição:

```python
async def processar_oferta():

    oferta = await carregar_oferta()

    validar_oferta(oferta)

    resultado = await executar_regras(oferta)

    await persistir_resultado(resultado)

    return resultado
```

---

# 45. Classes

Classes devem possuir responsabilidade clara.

Evitar classes que concentram:

- HTTP;
- banco;
- regras;
- integração;
- logging;
- transformação;

simultaneamente.

Preferir composição.

---

# 46. Programação Funcional

Python permite utilizar funções como objetos de primeira classe.

Utilizar:

- funções puras;
- composição;
- imutabilidade;

quando isso tornar o código mais simples.

Não utilizar padrões funcionais excessivamente complexos apenas para evitar classes.

A legibilidade deve ser prioridade.

---

# 47. Tratamento de Null / None

Nunca assumir que valores opcionais existem.

Evitar:

```python
value = user.name.upper()
```

quando `name` puder ser `None`.

Preferir validação explícita:

```python
if user.name is None:
    raise InvalidUserError()
```

---

# 48. Configuração de Ambiente

Ambientes devem ser separados:

```text
local
desenvolvimento
teste
homologacao
producao
```

Configurações específicas de ambiente não devem ser hardcoded.

Exemplo:

```text
APP_ENV=production
MONGODB_URI=...
REDIS_URL=...
```

---

# 49. Docker

Aplicações devem possuir Dockerfile apropriado.

Preferir imagens pequenas.

Não executar aplicação como `root` quando possível.

Exemplo conceitual:

```text
Python Base Image
      ↓
Install Dependencies
      ↓
Copy Application
      ↓
Run Gunicor
```

Para produção, avaliar:

```text
gunicor
```

diretamente ou um gerenciador de processos apropriado à infraestrutura utilizada.

O python é single thread, com isso utilziar apenas 1 workers e escalar via HPA:

- CPU;
- memória;
- natureza da aplicação;
- concorrência;
- uso de async;
- infraestrutura de deployment.

Não assumir que "mais workers = mais performance".

---

# 50. Performance

Performance deve ser medida antes de otimizada.

Priorizar:

1. algoritmo;
2. I/O;
3. banco;
4. rede;
5. serialização;
6. cache;
7. CPU.

Evitar micro-otimizações prematuras.

Para workloads de alta performance:

- medir latency;
- medir throughput;
- medir p95;
- medir p99;
- identificar gargalos;
- utilizar profiling.

---

# 51. Cache

Cache deve possuir responsabilidade clara.

Exemplos:

```text
Service
   ↓
Cache
   ↓
Repository
```

Quando aplicável, utilizar:

- Redis;
- cache local;
- TTL;
- eviction policy.

Nunca utilizar cache como fonte definitiva de verdade quando o sistema exigir persistência.

Cache deve possuir estratégia para:

- invalidação;
- expiração;
- consistência;
- fallback.

---

# 52. Segurança de Dados

Nunca registrar em logs:

- senha;
- token;
- API key;
- secret;
- credential;
- dados sensíveis desnecessários.

Nunca retornar exceções internas diretamente ao cliente.

Evitar:

```python
return {"error": str(exc)}
```

para exceções internas.

---

# 53. API Design

APIs devem possuir:

- versionamento quando necessário;
- contratos explícitos;
- schemas;
- status HTTP adequados;
- mensagens de erro padronizadas;
- paginação;
- filtros;
- ordenação;
- idempotência quando aplicável.

Exemplo:

```text
GET /api/v1/ofertas
POST /api/v1/ofertas
GET /api/v1/ofertas/{id}
PUT /api/v1/ofertas/{id}
DELETE /api/v1/ofertas/{id}
```

---

# 54. Documentação da API

FastAPI deve gerar documentação OpenAPI.

Endpoints devem possuir:

- descrição;
- response_model;
- status codes;
- parâmetros tipados;
- exemplos quando úteis.

Evitar endpoints sem contrato explícito.

---

# 55. Versionamento

Mudanças incompatíveis na API devem possuir estratégia explícita.

Nunca alterar silenciosamente:

- nomes de campos;
- tipos;
- semântica;
- status codes;

quando clientes existentes puderem ser afetados.

---

# 56. Git

Commits devem ser pequenos e relacionados a uma alteração lógica.

Pull Requests devem permitir identificar:

- problema;
- solução;
- impacto;
- testes;
- riscos.

Não misturar:

```text
refactor gigante
+
nova feature
+
alteração de banco
+
formatação de todo projeto
```

em uma única mudança sem necessidade.

---

# 57. Regras para o GitHub Copilot

Ao gerar código Python, siga obrigatoriamente estas diretrizes:

- Organize o projeto conforme a estrutura Feature-First definida.
- Novas capacidades devem nascer dentro de `features/<feature>`.
- Não criar `router`, `service` ou `repository` genéricos no nível raiz.
- Mantenha Routers finos.
- Nunca coloque regras de negócio em Routers.
- Nunca acesse banco diretamente a partir de Routers.
- Nunca faça chamadas HTTP externas diretamente em Routers.
- Utilize Services para casos de uso e orquestração.
- Utilize Repositories exclusivamente para persistência.
- Utilize Integration para serviços externos.
- Utilize Pydantic para contratos de API.
- Não utilize entidades de domínio como DTOs sem justificativa.
- Não exponha modelos de persistência diretamente nas APIs.
- Utilize type hints.
- Evite `Any`.
- Prefira `dataclass` para objetos de domínio simples.
- Prefira imutabilidade quando possível.
- Utilize Dependency Injection.
- Não instancie dependências de infraestrutura dentro do domínio.
- Utilize `async/await` para operações de I/O quando houver suporte adequado.
- Nunca utilize operações bloqueantes indiscriminadamente dentro de código assíncrono.
- Centralize tratamento de exceções.
- Nunca exponha stack traces para clientes.
- Centralize configuração.
- Nunca coloque secrets no código.
- Utilize structured logging.
- Utilize OpenTelemetry.
- Utilize métricas e health checks.
- Utilize Repository para encapsular acesso a MongoDB/SQL.
- Utilize migrations para bancos que exigem versionamento.
- Escreva testes unitários para regras de negócio.
- Escreva testes de integração quando necessário.
- Utilize Ruff.
- Utilize MyPy ou Pyright.
- Utilize pytest.
- Gere código simples, explícito, testável e desacoplado.
- Não introduza abstrações desnecessárias.
- Não criar classes ou camadas apenas por padrão quando não houver responsabilidade real.
- Priorize legibilidade e manutenção.
- Siga SOLID e Separation of Concerns.
- Nunca introduza dependências de infraestrutura dentro do Domain.
- Não utilizar `utils.py` como depósito genérico de funções.
- Não duplicar regras de negócio entre Router, Service e Repository.
- Sempre considerar idempotência em operações críticas.
- Sempre considerar timeout em integrações externas.
- Sempre considerar observabilidade em operações externas.
- Sempre manter compatibilidade com a versão de Python definida pelo projeto.