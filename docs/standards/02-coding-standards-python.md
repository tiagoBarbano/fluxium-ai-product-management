# 02 - Padrões de Código

Este documento define os padrões mínimos de implementação para aplicações Python modernas, especialmente aplicações desenvolvidas com FastAPI.

O objetivo é garantir legibilidade, consistência, previsibilidade, testabilidade e manutenção sustentável em produção.

---

# 1. Princípios

Todo código deve priorizar:

- simplicidade;
- legibilidade;
- baixo acoplamento;
- alta coesão;
- previsibilidade;
- testabilidade;
- explicitude;
- facilidade de manutenção.

Evitar abstrações prematuras e complexidade desnecessária.

O código deve seguir o princípio:

```text
Explicit is better than implicit.
```

A solução mais simples que atende corretamente ao requisito deve ser preferida.

---

# 2. Convenções Gerais

Utilizar:

- Python 3.12+;
- type hints;
- nomes claros;
- funções pequenas e focadas;
- classes com responsabilidade única;
- imutabilidade quando possível;
- composição em vez de herança quando apropriado;
- `Enum` para valores finitos;
- `dataclass` para objetos de domínio simples;
- Pydantic para contratos de API;
- `async/await` para operações de I/O assíncronas.

Preferir:

```python
def calculate_price(
    amount: Decimal,
    discount: Decimal,
) -> Decimal:
    ...
```

Evitar:

```python
def calc(a, d):
    ...
```

Abreviações somente devem ser utilizadas quando forem amplamente conhecidas no domínio.

Evitar:

- classes utilitárias gigantes;
- funções gigantes;
- módulos gigantes;
- efeitos colaterais ocultos;
- variáveis globais mutáveis;
- acoplamento entre camadas;
- duplicação de regras de negócio;
- `Any` sem justificativa;
- `dict` genérico como modelo de domínio;
- código excessivamente abstrato.

---

# 3. Estrutura de Código

Seguir obrigatoriamente a organização **Feature-First** definida no documento de arquitetura.

Cada feature deve conter suas responsabilidades internas:

```text
feature/
├── router.py
├── service.py
├── repository.py
├── domain/
├── schemas/
├── mapper.py
├── validation.py
└── integration/
```

Componentes compartilhados permanecem fora das features:

```text
config/
exception/
security/
telemetry/
database/
shared/
```

Dependências entre features devem ser:

- minimizadas;
- explícitas;
- orientadas ao domínio;
- facilmente testáveis.

Responsabilidades:

- Router: entrada e saída HTTP;
- Service: casos de uso, regras de negócio e orquestração;
- Repository: persistência;
- Integration: comunicação externa;
- Domain: regras e invariantes de negócio;
- Schema: contrato externo;
- Mapper: conversão entre modelos.

Nunca colocar regra de negócio em Router.

---

# 4. Funções

Funções devem possuir uma responsabilidade clara.

Preferir:

```python
def calculate_discount(
    price: Decimal,
    percentage: Decimal,
) -> Decimal:
    ...
```

a:

```python
def process_customer_and_calculate_discount_and_save(
    ...
):
    ...
```

Evitar funções com muitas responsabilidades.

Uma função deve preferencialmente:

- receber entradas claras;
- executar uma responsabilidade;
- retornar um resultado previsível.

Evitar efeitos colaterais ocultos.

Exemplo ruim:

```python
def calculate_total(order):
    save_order(order)
    send_email(order)
    return ...
```

O nome da função não representa os efeitos colaterais executados.

Preferir:

```python
total = calculate_total(order)

save_order(order)

send_order_email(order)
```

---

# 5. Classes

Classes devem possuir responsabilidade única.

Evitar classes que concentrem:

- HTTP;
- banco;
- regras de negócio;
- integrações;
- logging;
- transformação de dados.

Exemplo inadequado:

```python
class OfertaManager:

    async def create(self):
        ...

    async def save_mongodb(self):
        ...

    async def call_external_api(self):
        ...

    async def send_email(self):
        ...
```

Preferir composição:

```text
OfertaService
    ↓
OfertaRepository

OfertaService
    ↓
OfertaIntegration

OfertaService
    ↓
NotificationService
```

Não criar classes apenas para seguir um padrão.

Se uma função simples resolver o problema de forma mais clara, preferir a função.

---

# 6. Type Hints

Type hints são obrigatórios.

Preferir:

```python
def calculate(
    value: Decimal,
    percentage: Decimal,
) -> Decimal:
    ...
```

Evitar:

```python
def calculate(value, percentage):
    ...
```

Utilizar tipos modernos:

```python
list[str]
dict[str, str]
str | None
set[int]
```

Evitar, quando o projeto utilizar Python moderno:

```python
List[str]
Dict[str, str]
Optional[str]
```

Evitar `Any`.

Quando `Any` for necessário, justificar a utilização.

---

# 7. Variáveis

Variáveis devem possuir nomes claros.

Preferir:

```python
customer_id
expiration_date
total_amount
```

Evitar:

```python
cid
dt
x
tmp
value1
```

quando o significado não estiver evidente.

Evitar reutilizar a mesma variável para representar conceitos diferentes.

---

# 8. Constantes

Valores constantes devem possuir nomes explícitos.

Preferir:

```python
DEFAULT_TIMEOUT_SECONDS = 30
MAX_RETRY_ATTEMPTS = 3
```

Evitar:

```python
timeout = 30
retry = 3
```

quando esses valores representarem constantes de aplicação.

Configurações de ambiente não devem ser implementadas como constantes hardcoded.

---

# 9. Strings Mágicas

Evitar strings repetidas representando conceitos de domínio.

Evitar:

```python
if status == "ACTIVE":
    ...
```

Preferir:

```python
if status == OfertaStatus.ACTIVE:
    ...
```

quando o valor representar um estado do domínio.

---

# 10. Enums

Utilizar `Enum` para conjuntos finitos de valores.

Exemplo:

```python
class OfertaStatus(str, Enum):

    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
```

Evitar espalhar valores literais pelo código.

---

# 11. Dataclasses

Utilizar `dataclass` quando representar objetos de domínio simples.

Exemplo:

```python
@dataclass(frozen=True)
class Money:

    amount: Decimal
    currency: str
```

Preferir:

```python
@dataclass(frozen=True)
```

quando o objeto puder ser imutável.

Não utilizar Pydantic automaticamente para todo objeto interno da aplicação.

Pydantic deve ser priorizado para contratos, validação e serialização.

---

# 12. Pydantic Schemas

Utilizar Pydantic para contratos de API.

Exemplo:

```python
class CreateOfertaRequest(BaseModel):

    nome: str = Field(
        min_length=1,
        max_length=200,
    )

    produto_id: str
```

Responses:

```python
class OfertaResponse(BaseModel):

    id: str
    nome: str
    ativa: bool
```

Não utilizar `dict` como substituto de schemas quando existir um contrato definido.

Evitar:

```python
async def create(request: dict):
    ...
```

Preferir:

```python
async def create(
    request: CreateOfertaRequest,
):
    ...
```

---

# 13. DTOs, Domain e Persistência

Não misturar os modelos:

```text
API Schema
Domain Entity
Database Model
```

Cada modelo deve possuir sua responsabilidade.

Fluxo recomendado:

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
Database Model
```

E:

```text
Database Model
      ↓
Mapper
      ↓
Domain
      ↓
Response Schema
```

Nunca retornar diretamente documentos MongoDB ou modelos SQLAlchemy como contrato público da API.

---

# 14. Injeção de Dependências

Utilizar Dependency Injection.

Preferir constructor injection:

```python
class OfertaService:

    def __init__(
        self,
        repository: OfertaRepository,
    ):
        self.repository = repository
```

No FastAPI:

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
class OfertaService:

    def __init__(self):
        self.repository = MongoOfertaRepository()
```

quando isso criar acoplamento desnecessário à infraestrutura.

Evitar também instanciar dependências diretamente dentro de Routers.

---

# 15. Async / Await

Operações de I/O devem utilizar `async/await` quando houver suporte assíncrono adequado.

Exemplos:

- HTTP;
- MongoDB;
- PostgreSQL;
- Redis;
- filas;
- serviços externos.

Preferir:

```python
async def find_customer(
    customer_id: str,
) -> Customer | None:

    return await repository.find_by_id(
        customer_id
    )
```

Evitar operações bloqueantes dentro de código assíncrono.

Exemplo inadequado:

```python
async def get_customer():

    response = requests.get(url)

    return response.json()
```

Quando existir cliente HTTP assíncrono apropriado, utilizá-lo.

---

# 16. Código Síncrono vs Assíncrono

Não utilizar `async` apenas por padrão.

Utilizar código assíncrono quando houver benefício real, principalmente em operações de I/O concorrentes.

Código síncrono pode ser apropriado para:

- funções puras;
- cálculos;
- transformações;
- regras de domínio;
- operações sem I/O.

Exemplo:

```python
def calculate_premium(
    base: Decimal,
    factor: Decimal,
) -> Decimal:
    return base * factor
```

Não transformar automaticamente em:

```python
async def calculate_premium(...):
```

sem necessidade.

---

# 17. Repository

Repositories devem conter somente lógica relacionada à persistência.

Permitido:

```python
await repository.find_by_id(id)
await repository.save(entity)
await repository.delete(id)
```

Não permitido:

```python
class OfertaRepository:

    async def save(self, oferta):

        if oferta.valor > 100000:
            ...
```

quando essa condição representa uma regra de negócio.

Regras de negócio pertencem ao Domain ou Service.

---

# 18. Service

Services devem representar casos de uso.

Exemplo:

```python
async def create_oferta(
    request: CreateOfertaRequest,
) -> Oferta:

    oferta = Oferta.create(
        nome=request.nome,
    )

    await repository.save(oferta)

    return oferta
```

O Service deve coordenar as dependências necessárias.

Evitar Services gigantes.

Quando um Service possuir dezenas de responsabilidades, avaliar divisão por casos de uso ou domínio.

---

# 19. Router

Routers devem permanecer finos.

Exemplo:

```python
@router.post(
    "/ofertas",
    response_model=OfertaResponse,
)
async def create_oferta(
    request: CreateOfertaRequest,
    service: OfertaService = Depends(
        get_oferta_service
    ),
) -> OfertaResponse:

    oferta = await service.create(request)

    return OfertaResponse.from_domain(oferta)
```

Evitar:

```python
@router.post("/ofertas")
async def create_oferta(request):

    document = await mongo.ofertas.find_one(...)

    if ...:
        ...

    await external_api.post(...)

    await mongo.ofertas.insert_one(...)

    return ...
```

Toda essa lógica deve estar distribuída nas camadas corretas.

---

# 20. Tratamento de Erros

Utilizar exceções específicas.

Preferir:

```python
class OfertaNotFoundError(
    ApplicationException
):
    pass
```

em vez de:

```python
raise Exception("Oferta não encontrada")
```

Não utilizar `Exception` genérica para representar erros de negócio.

Centralizar o mapeamento de exceções para HTTP.

Exemplo:

```text
Domain/Application Exception
        ↓
Exception Handler
        ↓
HTTP Response
```

Nunca retornar stack trace ao cliente.

---

# 21. HTTP Exceptions

`HTTPException` deve ser utilizada preferencialmente na camada HTTP.

Evitar:

```python
class OfertaService:

    async def find(self, id):
        if not oferta:
            raise HTTPException(
                status_code=404
            )
```

Preferir:

```python
class OfertaService:

    async def find(self, id):

        if not oferta:
            raise OfertaNotFoundError()
```

E realizar o mapeamento no Exception Handler.

Dessa forma, o Service permanece independente de FastAPI.

---

# 22. Logging

Preferir Structured Logging.

Exemplo:

```python
logger.info(
    "oferta_created",
    extra={
        "oferta_id": oferta.id,
    },
)
```

O formato final pode variar conforme a biblioteca de logging adotada.

Nunca utilizar:

```python
print("Oferta criada")
```

como mecanismo de logging de produção.

Evitar logs redundantes.

Não registrar:

- senhas;
- tokens;
- API keys;
- secrets;
- credenciais;
- dados sensíveis desnecessários.

---

# 23. Logging por Camada

Evitar registrar o mesmo evento em todas as camadas.

Exemplo inadequado:

```text
Router: oferta criada
Service: oferta criada
Repository: oferta criada
```

Isso produz ruído.

Preferir registrar eventos relevantes nos pontos onde existe contexto suficiente.

---

# 24. Observabilidade

Operações relevantes devem possuir observabilidade.

Considerar:

- logs;
- métricas;
- traces;
- duração;
- erros;
- dependências externas.

Integrações externas devem permitir identificar:

```text
Request
  ↓
Service
  ↓
External API
```

por meio de tracing/correlation.

---

# 25. Comentários

Comentários devem ser raros e úteis.

O código deve explicar **o que** está fazendo.

Comentários devem explicar principalmente:

- por que determinada decisão existe;
- regra de negócio não óbvia;
- workaround;
- limitação externa;
- comportamento contraintuitivo.

Evitar:

```python
# Incrementa o contador
counter += 1
```

Preferir código autoexplicativo.

---

# 26. Docstrings

Docstrings devem ser utilizadas quando agregarem valor.

São especialmente úteis para:

- APIs públicas;
- módulos reutilizáveis;
- funções complexas;
- comportamento não óbvio;
- contratos importantes.

Não criar docstrings que simplesmente repitam o nome da função.

Evitar:

```python
def calculate_total():
    """Calcula o total."""
```

quando o comportamento já for evidente.

---

# 27. Imports

Imports devem ser explícitos.

Nunca utilizar:

```python
from module import *
```

Preferir:

```python
from decimal import Decimal
from app.features.oferta.domain.entity import Oferta
```

Imports devem ser organizados automaticamente pelo formatter/linter adotado.

---

# 28. Exceções

Não utilizar exceções para controlar fluxo normal da aplicação.

Evitar:

```python
try:
    value = data["value"]
except KeyError:
    ...
```

quando uma validação explícita for mais adequada.

Exceções devem representar situações excepcionais ou violações de contrato/invariante.

---

# 29. Context Managers

Utilizar context managers para recursos que necessitam de aquisição e liberação.

Exemplo:

```python
async with transaction:
    ...
```

ou:

```python
with open(file_path) as file:
    ...
```

Evitar gerenciamento manual de recursos quando houver abstração segura disponível.

---

# 30. Mutable Defaults

Nunca utilizar objetos mutáveis como valores default.

Evitar:

```python
def process(items=[]):
    ...
```

Preferir:

```python
def process(
    items: list[str] | None = None,
):
    items = items or []
```

---

# 31. Estado Global

Evitar estado global mutável.

Evitar:

```python
cache = {}

users = []

current_tenant = None
```

quando esses objetos forem modificados por múltiplas partes da aplicação.

Preferir:

- Dependency Injection;
- objetos encapsulados;
- cache apropriado;
- contexto explícito;
- serviços especializados.

---

# 32. Configuração

Configurações devem ser centralizadas.

Preferir:

```python
class Settings(BaseSettings):

    app_name: str
    environment: str
    mongodb_uri: str
    redis_url: str
```

Evitar:

```python
os.getenv("MONGODB_URI")
```

espalhado pelo código.

Não utilizar secrets hardcoded.

---

# 33. Validação

Validação deve ocorrer no nível correto.

### Validação de contrato

Pydantic:

```python
class CreateOfertaRequest(BaseModel):
    nome: str = Field(min_length=1)
```

### Validação de negócio

Domain/Service:

```python
if oferta.is_expired():
    raise OfertaExpiredError()
```

Não concentrar todas as validações no Router.

---

# 34. Retornos

Funções devem possuir contratos claros.

Preferir:

```python
def find_customer(
    customer_id: str,
) -> Customer | None:
    ...
```

em vez de:

```python
def find_customer(...):
    ...
```

Evitar retornar tipos diferentes dependendo do fluxo:

```python
return customer
```

em um caminho e:

```python
return {"error": "..."}
```

em outro.

Erros devem ser representados por exceções ou contratos explícitos.

---

# 35. Booleanos

Variáveis booleanas devem possuir nomes que expressem condição.

Preferir:

```python
is_active
has_permission
can_execute
should_retry
```

Evitar:

```python
active_flag
permission_value
execute
```

quando o significado puder ser mais explícito.

---

# 36. Condições

Evitar condições excessivamente complexas.

Evitar:

```python
if (
    customer
    and customer.active
    and customer.account
    and customer.account.valid
    and customer.account.balance > 0
):
    ...
```

Quando a condição representar uma regra de negócio, extraí-la:

```python
if customer.can_purchase():
    ...
```

Isso melhora legibilidade e centraliza a regra.

---

# 37. List Comprehension

List comprehensions podem ser utilizadas quando melhorarem a legibilidade.

Preferir:

```python
active_ids = [
    customer.id
    for customer in customers
    if customer.active
]
```

Evitar comprehensions excessivamente complexas.

Se houver múltiplas condições e transformações, utilizar um loop explícito.

---

# 38. Código Duplicado

Evitar duplicação de regras de negócio.

Se a mesma regra aparecer em:

```text
Router
Service
Repository
```

deve ser revisada.

Entretanto, não criar abstrações prematuras apenas para eliminar poucas linhas de código.

O objetivo é evitar **duplicação de conhecimento**, não necessariamente duplicação textual.

---

# 39. Abstrações

Não criar abstrações sem necessidade.

Evitar:

```python
class AbstractOfertaService:
    ...
```

se existir apenas uma implementação e nenhuma necessidade arquitetural.

Também evitar criar:

```text
BaseRepository
BaseService
BaseController
BaseMapper
```

apenas por padrão.

Abstrações devem existir quando resolverem um problema real:

- múltiplas implementações;
- desacoplamento;
- teste;
- arquitetura;
- extensão futura comprovadamente necessária.

---

# 40. Performance

Não realizar otimizações prematuras.

Primeiro:

```text
Funcionalidade
    ↓
Corretude
    ↓
Testes
    ↓
Medição
    ↓
Otimização
```

Antes de otimizar, medir.

Quando performance for relevante, avaliar:

- latency;
- throughput;
- p95;
- p99;
- CPU;
- memória;
- banco;
- rede;
- serialização;
- cache.

---

# 41. Cache

Cache não deve esconder regras de negócio.

Preferir:

```text
Service
   ↓
Cache
   ↓
Repository
```

Cache deve possuir:

- TTL;
- estratégia de invalidação;
- tratamento de cache miss;
- fallback quando necessário.

Nunca assumir que o cache é a fonte definitiva dos dados quando a persistência principal estiver disponível.

---

# 42. Integrações

Toda integração externa deve estar encapsulada.

Preferir:

```text
Service
   ↓
Integration Client
   ↓
External API
```

Nunca:

```text
Router
   ↓
External API
```

ou:

```text
Domain
   ↓
External API
```

Integrações devem definir explicitamente:

- timeout;
- retry;
- tratamento de erro;
- autenticação;
- observabilidade.

---

# 43. Testabilidade

Código deve ser desenvolvido para ser testável.

Evitar:

```python
class Service:

    def __init__(self):
        self.repository = MongoRepository()
```

Preferir:

```python
class Service:

    def __init__(
        self,
        repository: Repository,
    ):
        self.repository = repository
```

Isso permite substituir a implementação nos testes.

---

# 44. Testes

Toda nova funcionalidade deve possuir testes adequados.

Antes de abrir PR:

```text
pytest
ruff
```

Quando aplicável:

```text
unit tests
integration tests
API tests
```

Testes devem verificar comportamento.

Evitar testes excessivamente acoplados à implementação interna.

---

# 45. Fixtures

Utilizar fixtures para preparar cenários de teste repetidos.

Preferir fixtures reutilizáveis.

Evitar duplicar a mesma preparação em dezenas de testes.

---

# 46. Testes Unitários

Testes unitários devem ser rápidos e isolados.

Priorizar:

- Domain;
- Services;
- validações;
- Mappers;
- regras de negócio.

Não depender de banco real em testes unitários.

---

# 47. Testes de Integração

Utilizar testes de integração quando for necessário validar:

- MongoDB;
- PostgreSQL;
- Redis;
- APIs externas;
- infraestrutura;
- contratos.

Testes de integração não devem substituir todos os testes unitários.

---

# 48. Qualidade Automática

O projeto deve utilizar ferramentas automáticas.

Preferencialmente:

```text
Ruff
Pytest
```

Exemplo:

```text
ruff check .
ruff format --check .
pytest
```

O CI deve impedir merge quando houver:

- falha de testes;
- erros críticos de lint;
- problemas de tipagem definidos como bloqueantes.

---

# 49. Código Morto

Antes de abrir PR:

- remover código morto;
- remover imports não utilizados;
- remover variáveis não utilizadas;
- remover funções não utilizadas;
- remover comentários obsoletos;
- remover logs de debug;
- remover código comentado.

Não manter código antigo "por garantia" no repositório.

O Git já possui histórico.

---

# 50. TODO

TODOs temporários devem ser evitados.

Se um TODO representar trabalho real:

- criar issue/tarefa correspondente;
- explicar o contexto;
- evitar TODOs vagos.

Evitar:

```python
# TODO: melhorar isso
```

Preferir uma issue rastreável.

---

# 51. Segurança

Antes de abrir PR:

- nenhuma credencial hardcoded;
- nenhum token no código;
- nenhum secret no repositório;
- nenhum dado sensível em logs;
- nenhuma stack trace exposta;
- validações de entrada implementadas;
- autorização considerada quando aplicável.

---

# 52. Pull Request

Antes de abrir PR:

- código formatado;
- lint executado;
- type checking executado;
- testes executados;
- código morto removido;
- logs de debug removidos;
- secrets removidos;
- documentação atualizada quando necessário;
- migrations incluídas quando necessárias.

---

# 53. Checklist Rápido

- [ ] Código simples e legível
- [ ] Type hints utilizados
- [ ] Responsabilidade única por função/classe
- [ ] Feature-First respeitado
- [ ] Sem regra de negócio em Router
- [ ] Sem acesso a banco fora de Repository
- [ ] Sem chamadas externas fora de Integration
- [ ] Schemas Pydantic utilizados para contratos
- [ ] Domain separado de infraestrutura
- [ ] Dependency Injection utilizada
- [ ] `async/await` utilizado corretamente para I/O
- [ ] Sem operações bloqueantes indevidas
- [ ] Exceções específicas utilizadas
- [ ] Erros tratados centralmente
- [ ] Sem stack trace exposta
- [ ] Logs estruturados
- [ ] Sem dados sensíveis nos logs
- [ ] Configurações centralizadas
- [ ] Sem secrets hardcoded
- [ ] Ruff executado
- [ ] MyPy/Pyright executado
- [ ] Testes executados
- [ ] Código morto removido
- [ ] TODOs temporários tratados
- [ ] PR pronto para revisão

---

# 54. Regras para o GitHub Copilot

Ao gerar código Python, siga obrigatoriamente estas regras:

- Siga a arquitetura Feature-First.
- Mantenha consistência com `01 - Arquitetura e Estrutura do Projeto`.
- Não crie abstrações sem necessidade.
- Priorize simplicidade e legibilidade.
- Utilize Python 3.12+.
- Utilize type hints.
- Evite `Any`.
- Utilize Pydantic para contratos externos.
- Utilize `dataclass` para objetos de domínio simples quando apropriado.
- Utilize `Enum` para estados e valores finitos.
- Mantenha Routers finos.
- Nunca coloque regras de negócio em Routers.
- Nunca acesse banco diretamente em Routers.
- Nunca faça chamadas externas diretamente em Routers.
- Utilize Services para casos de uso e orquestração.
- Utilize Repositories exclusivamente para persistência.
- Utilize Integration para comunicação externa.
- Mantenha Domain independente de FastAPI e infraestrutura.
- Utilize Dependency Injection.
- Evite instanciar infraestrutura diretamente dentro dos Services.
- Utilize `async/await` para I/O quando apropriado.
- Nunca execute operações bloqueantes indiscriminadamente dentro de código assíncrono.
- Utilize exceções específicas.
- Não utilize `HTTPException` dentro do Domain.
- Evite acoplamento do Service com HTTP.
- Centralize tratamento de exceções.
- Nunca exponha stack traces.
- Utilize structured logging.
- Nunca registre secrets ou dados sensíveis.
- Centralize configurações.
- Nunca coloque credenciais no código.
- Utilize Repository para MongoDB/SQL.
- Utilize Mapper para separar persistência e domínio.
- Não utilize documentos MongoDB diretamente como objetos de domínio.
- Não retorne modelos de persistência diretamente pela API.
- Não utilize strings mágicas para conceitos de domínio.
- Evite funções e classes gigantes.
- Evite classes utilitárias genéricas.
- Não crie `utils.py` como depósito de código.
- Evite estado global mutável.
- Evite efeitos colaterais ocultos.
- Evite abstrações prematuras.
- Escreva testes para regras de negócio.
- Utilize pytest.
- Utilize Ruff.
- Utilize MyPy ou Pyright.
- Gere código simples, explícito, testável e desacoplado.
- Priorize comportamento e legibilidade sobre complexidade arquitetural.