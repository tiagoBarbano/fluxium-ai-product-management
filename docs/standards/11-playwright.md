# 11 - Testes de Interface com Playwright

Este documento define os padrões para implementação de testes automatizados de interface utilizando Playwright.

O objetivo é garantir que as telas e os principais fluxos da aplicação funcionem corretamente sob a perspectiva do usuário.

Os testes devem validar comportamento observável da aplicação, evitando acoplamento desnecessário à implementação interna do frontend.

---

# 1. Objetivos

Os testes de interface devem validar principalmente:

- navegação;
- carregamento de telas;
- interação com componentes;
- preenchimento de formulários;
- validações;
- mensagens de erro;
- mensagens de sucesso;
- tabelas;
- filtros;
- paginação;
- modais;
- seleção de opções;
- upload de arquivos;
- downloads;
- autenticação;
- autorização;
- fluxos completos;
- comportamento responsivo quando aplicável.

O teste deve responder:

> "Um usuário consegue executar corretamente este fluxo?"

---

# 2. Princípios

Os testes devem priorizar:

- comportamento do usuário;
- estabilidade;
- legibilidade;
- independência entre testes;
- execução determinística;
- baixa manutenção;
- isolamento;
- evidência clara em caso de falha.

Evitar testar detalhes internos do código.

Não testar:

- implementação interna de componentes;
- estado interno do React;
- funções privadas;
- estrutura específica de componentes;
- classes CSS sem necessidade;
- detalhes de implementação que o usuário não percebe.

Preferir testar:

```text
Usuário
   ↓
Tela
   ↓
Interação
   ↓
Resultado observável
```

---

# 3. Tecnologia

Utilizar:

- Playwright;
- Playwright Test;
- TypeScript.

Instalação:

```bash
npm install -D @playwright/test
npx playwright install
```

Preferir TypeScript para os testes.

---

# 4. Estrutura

A estrutura recomendada:

```text
tests/
└── e2e/
    ├── auth/
    │   ├── login.spec.ts
    │   └── logout.spec.ts
    │
    ├── oferta/
    │   ├── oferta-list.spec.ts
    │   ├── oferta-create.spec.ts
    │   ├── oferta-edit.spec.ts
    │   └── oferta-delete.spec.ts
    │
    ├── experimento/
    │   └── experimento.spec.ts
    │
    ├── fixtures/
    │   ├── auth.fixture.ts
    │   └── test.fixture.ts
    │
    ├── pages/
    │   ├── LoginPage.ts
    │   ├── OfertaPage.ts
    │   └── ExperimentoPage.ts
    │
    └── utils/
        └── test-data.ts

playwright.config.ts
```

A organização deve seguir **Feature-First**.

---

# 5. Testes por Feature

Cada feature deve possuir seus próprios testes.

Exemplo:

```text
features/
└── oferta/

tests/
└── e2e/
    └── oferta/
        ├── oferta-list.spec.ts
        ├── oferta-create.spec.ts
        ├── oferta-edit.spec.ts
        └── oferta-delete.spec.ts
```

Não criar um único arquivo gigantesco:

```text
tests/e2e/all.spec.ts
```

---

# 6. Naming

Arquivos devem utilizar nomes descritivos.

Preferir:

```text
login.spec.ts
oferta-create.spec.ts
oferta-edit.spec.ts
oferta-list.spec.ts
```

Evitar:

```text
test1.spec.ts
test2.spec.ts
misc.spec.ts
general.spec.ts
```

Os nomes devem permitir identificar rapidamente o fluxo testado.

---

# 7. Estrutura do Teste

Um teste deve possuir uma estrutura clara:

```text
Arrange
   ↓
Act
   ↓
Assert
```

Exemplo:

```typescript
test("deve criar uma oferta", async ({ page }) => {

  // Arrange
  await page.goto("/ofertas");

  // Act
  await page.getByRole("button", {
    name: "Nova oferta",
  }).click();

  await page.getByLabel("Nome").fill("Oferta Teste");

  await page.getByRole("button", {
    name: "Salvar",
  }).click();

  // Assert
  await expect(
    page.getByText("Oferta criada com sucesso")
  ).toBeVisible();
});
```

---

# 8. Locators

Preferir locators orientados ao comportamento do usuário.

Ordem preferencial:

1. `getByRole`
2. `getByLabel`
3. `getByPlaceholder`
4. `getByText`
5. `getByTestId`

Exemplo:

```typescript
page.getByRole("button", {
  name: "Salvar",
});
```

Preferir:

```typescript
page.getByLabel("Nome")
```

a:

```typescript
page.locator("#input-name")
```

---

# 9. Test IDs

Utilizar `data-testid` quando não existir um locator semântico adequado.

Exemplo:

```tsx
<button data-testid="offer-save">
  Salvar
</button>
```

Teste:

```typescript
page.getByTestId("offer-save")
```

Não utilizar `data-testid` indiscriminadamente.

Se o elemento possuir uma identificação semântica adequada, preferir:

```typescript
getByRole()
getByLabel()
getByText()
```

---

# 10. CSS Selectors

Evitar seletores baseados em CSS quando houver alternativa semântica.

Evitar:

```typescript
page.locator(
  ".container > div:nth-child(2) button"
)
```

Evitar:

```typescript
page.locator(
  "#root .MuiButton-root"
)
```

Esses testes ficam excessivamente acoplados à implementação visual.

Preferir:

```typescript
page.getByRole("button", {
  name: "Salvar",
})
```

---

# 11. XPath

Não utilizar XPath como padrão.

Evitar:

```typescript
page.locator(
  "//div[@class='container']//button"
)
```

Utilizar somente quando não existir alternativa adequada.

---

# 12. Assertions

Todo teste deve possuir assertions relevantes.

Exemplo:

```typescript
await expect(
  page.getByRole("heading", {
    name: "Ofertas",
  })
).toBeVisible();
```

Evitar testes que apenas executam ações:

```typescript
test("criar oferta", async ({ page }) => {

  await page.goto("/ofertas");

  await page.getByRole("button", {
    name: "Nova oferta",
  }).click();
});
```

O teste deve verificar o resultado.

---

# 13. Assertions de URL

Quando a navegação fizer parte do comportamento esperado:

```typescript
await expect(page).toHaveURL(
  /\/ofertas/
);
```

Evitar:

```typescript
expect(page.url()).toContain(
  "/ofertas"
);
```

quando uma assertion nativa do Playwright for suficiente.

---

# 14. Assertions de Texto

Preferir verificar mensagens observáveis.

Exemplo:

```typescript
await expect(
  page.getByRole("alert")
).toHaveText(
  "Oferta criada com sucesso"
);
```

Evitar validar estruturas internas sem necessidade.

---

# 15. Formulários

Testes de formulário devem validar:

- preenchimento;
- campos obrigatórios;
- formato inválido;
- mensagens de validação;
- envio;
- sucesso;
- erro.

Exemplo:

```typescript
test("deve validar nome obrigatório", async ({
  page,
}) => {

  await page.goto("/ofertas/nova");

  await page.getByRole("button", {
    name: "Salvar",
  }).click();

  await expect(
    page.getByText("Nome é obrigatório")
  ).toBeVisible();
});
```

---

# 16. Fluxos de Sucesso

Cada funcionalidade crítica deve possuir pelo menos um fluxo principal de sucesso.

Exemplo:

```text
Login
 ↓
Dashboard
 ↓
Ofertas
 ↓
Nova Oferta
 ↓
Preencher
 ↓
Salvar
 ↓
Oferta criada
```

O teste deve validar o resultado final.

---

# 17. Fluxos de Erro

Funcionalidades críticas devem possuir testes para erros relevantes.

Exemplos:

- credenciais inválidas;
- recurso inexistente;
- conflito;
- erro de validação;
- API indisponível;
- timeout;
- falta de autorização.

Exemplo:

```typescript
test("deve exibir erro para credenciais inválidas", async ({
  page,
}) => {

  await page.goto("/login");

  await page.getByLabel("Email")
    .fill("usuario@example.com");

  await page.getByLabel("Senha")
    .fill("senha-invalida");

  await page.getByRole("button", {
    name: "Entrar",
  }).click();

  await expect(
    page.getByRole("alert")
  ).toBeVisible();
});
```

---

# 18. Autenticação

Fluxos autenticados devem reutilizar uma sessão quando possível.

Não realizar login completo antes de cada teste se isso não for necessário.

Utilizar `storageState`.

Exemplo:

```typescript
await page.context().storageState({
  path: "playwright/.auth/user.json",
});
```

Configuração:

```typescript
use: {
  storageState: "playwright/.auth/user.json",
}
```

Isso reduz tempo de execução e evita duplicação.

---

# 19. Teste de Login

O login deve possuir testes específicos para:

- login válido;
- usuário inexistente;
- senha inválida;
- campos obrigatórios;
- sessão;
- logout;
- expiração quando aplicável.

Não utilizar o login como parte de todos os testes se a sessão puder ser reutilizada.

---

# 20. Autorização

Quando existirem diferentes perfis de usuário, testar as permissões relevantes.

Exemplo:

```text
Usuário autorizado
    ↓
Pode acessar tela

Usuário não autorizado
    ↓
Acesso negado
```

Validar comportamento observável:

- botão não disponível;
- rota bloqueada;
- mensagem de autorização;
- redirecionamento.

Não confiar apenas na existência/ausência visual do botão.

A autorização real deve ser garantida pelo backend.

---

# 21. API Mocking

Utilizar mocking somente quando necessário.

Exemplo:

```typescript
await page.route(
  "**/api/ofertas",
  async route => {

    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        items: [],
      }),
    });
  }
);
```

Mocking é apropriado para:

- cenários difíceis de reproduzir;
- APIs externas;
- erros específicos;
- testes isolados de frontend;
- cenários determinísticos.

Não substituir todos os testes reais por mocks.

---

# 22. Testes E2E Reais

Fluxos críticos devem possuir testes utilizando a aplicação e APIs reais quando possível.

Exemplo:

```text
Playwright
    ↓
Frontend
    ↓
Backend
    ↓
Database
```

Esses testes devem validar o comportamento integrado.

Mocks não devem esconder problemas de integração.

---

# 23. Dados de Teste

Dados de teste devem ser previsíveis.

Evitar depender de dados criados manualmente.

Evitar:

```text
"usuário que já existe na base"
```

sem controle sobre o estado da base.

Preferir:

- fixtures;
- seed;
- API de preparação;
- banco de testes isolado;
- dados gerados pelo teste.

---

# 24. Isolamento

Testes devem ser independentes.

Evitar:

```text
Teste A cria oferta
       ↓
Teste B depende da oferta criada pelo A
```

Preferir:

```text
Teste A
  ↓
Setup próprio

Teste B
  ↓
Setup próprio
```

A ordem de execução dos testes não deve alterar o resultado.

---

# 25. Limpeza de Dados

Dados criados durante testes devem ser removidos ou isolados.

Opções:

- banco dedicado;
- tenant dedicado;
- fixture;
- teardown;
- API de limpeza;
- reset de ambiente.

A estratégia deve ser definida de acordo com o ambiente de execução.

---

# 26. Page Objects

Utilizar Page Objects quando houver repetição significativa de interações.

Exemplo:

```typescript
export class LoginPage {

  constructor(
    private readonly page: Page,
  ) {}

  async login(
    email: string,
    password: string,
  ) {

    await this.page
      .getByLabel("Email")
      .fill(email);

    await this.page
      .getByLabel("Senha")
      .fill(password);

    await this.page
      .getByRole("button", {
        name: "Entrar",
      })
      .click();
  }
}
```

Utilizar Page Objects para:

- fluxos recorrentes;
- telas complexas;
- componentes reutilizados;
- operações comuns.

Não criar Page Objects excessivamente abstratos.

---

# 27. Page Object vs Teste Direto

Para testes simples:

```typescript
test("deve abrir ofertas", async ({ page }) => {

  await page.goto("/ofertas");

  await expect(
    page.getByRole("heading", {
      name: "Ofertas",
    })
  ).toBeVisible();
});
```

Não é necessário criar:

```text
OfertaPage
OfertaPageService
OfertaPageRepository
```

apenas para encapsular três linhas.

A abstração deve ser proporcional à complexidade.

---

# 28. Fixtures

Fixtures devem encapsular preparação recorrente.

Exemplo:

```typescript
const test = base.extend<{
  authenticatedPage: Page;
}>({
  authenticatedPage: async ({
    browser,
  }, use) => {

    // preparação

    await use(page);
  },
});
```

Utilizar fixtures para:

- autenticação;
- dados;
- contexto;
- configurações;
- objetos reutilizáveis.

---

# 29. Esperas

Nunca utilizar `waitForTimeout` como estratégia normal de sincronização.

Evitar:

```typescript
await page.waitForTimeout(3000);
```

Preferir assertions:

```typescript
await expect(
  page.getByText("Oferta criada")
).toBeVisible();
```

Ou aguardar um comportamento específico:

```typescript
await page.waitForURL(
  /\/ofertas/
);
```

O Playwright possui auto-waiting e deve ser utilizado.

---

# 30. Seletores Estáveis

A interface deve fornecer identificadores estáveis quando necessário.

Preferir:

```html
<button>
  Salvar
</button>
```

ou:

```html
<button data-testid="save-offer">
  Salvar
</button>
```

Evitar depender de:

```text
classes geradas
IDs aleatórios
posição do elemento
estrutura DOM
```

---

# 31. Responsividade

Quando a aplicação possuir requisitos responsivos, testar os principais breakpoints.

Exemplo:

```typescript
test.use({
  viewport: {
    width: 390,
    height: 844,
  },
});
```

Testar principalmente:

- menu;
- navegação;
- tabelas;
- formulários;
- modais;
- overflow;
- componentes críticos.

Não é necessário testar todas as combinações possíveis.

---

# 32. Acessibilidade

Sempre que possível, utilizar locators baseados em acessibilidade:

```typescript
getByRole()
getByLabel()
```

Isso cria testes mais próximos da experiência real do usuário e também incentiva uma estrutura de acessibilidade adequada.

Quando acessibilidade for requisito explícito, utilizar ferramentas específicas de análise, como axe, além dos testes funcionais.

---

# 33. Screenshots

Screenshots devem ser utilizados principalmente para diagnóstico ou testes visuais.

Em caso de falha:

```text
test-results/
```

deve armazenar evidências quando configurado.

Não utilizar screenshots como única forma de assertion funcional.

---

# 34. Testes Visuais

Quando houver necessidade de validar aparência, utilizar screenshot comparison do Playwright.

Exemplo:

```typescript
await expect(page).toHaveScreenshot(
  "ofertas.png"
);
```

Testes visuais devem ser utilizados para telas/componentes em que alterações visuais sejam relevantes.

Evitar criar snapshots para todas as telas indiscriminadamente.

---

# 35. Responsabilidade dos Testes

Um teste deve validar uma capacidade clara.

Preferir:

```text
deve criar oferta
deve editar oferta
deve excluir oferta
deve filtrar ofertas
```

Evitar:

```text
deve funcionar corretamente
```

como descrição genérica.

---

# 36. Testes Grandes

Evitar testes extremamente longos.

Evitar:

```text
Login
 ↓
Criar cliente
 ↓
Criar produto
 ↓
Criar oferta
 ↓
Editar oferta
 ↓
Excluir produto
 ↓
Logout
```

em um único teste.

Dividir em cenários independentes quando possível.

Um teste longo pode ser utilizado quando o próprio fluxo de negócio for indivisível.

---

# 37. Testes Críticos

Cada feature deve identificar seus fluxos críticos.

Exemplo:

```text
Oferta

✓ listar
✓ criar
✓ editar
✓ consultar
✓ excluir
✓ validar
✓ filtrar
```

Nem toda variação precisa ser um teste E2E.

Testes unitários e de integração devem complementar os testes Playwright.

---

# 38. Pirâmide de Testes

Playwright não deve substituir os demais tipos de teste.

Estrutura recomendada:

```text
          E2E
        /     \
      poucos testes
     /             \
 Integração       Integração
     \             /
       Unitários
      muitos testes
```

Preferir:

- muitos testes unitários;
- testes de integração para componentes relevantes;
- poucos E2E cobrindo fluxos críticos.

---

# 39. Testes de API vs UI

Playwright pode testar APIs diretamente quando necessário.

Porém:

```text
API Test
```

não substitui:

```text
UI Test
```

quando o objetivo for validar o fluxo real do usuário.

Da mesma forma:

```text
UI Test
```

não substitui testes específicos do backend.

---

# 40. Configuração

Exemplo:

```typescript
import {
  defineConfig,
  devices,
} from "@playwright/test";

export default defineConfig({

  testDir: "./tests/e2e",

  fullyParallel: true,

  forbidOnly: !!process.env.CI,

  retries: process.env.CI ? 2 : 0,

  workers: process.env.CI ? 1 : undefined,

  reporter: [
    ["html"],
    ["list"],
  ],

  use: {

    baseURL:
      process.env.BASE_URL ??
      "http://localhost:3000",

    trace: "on-first-retry",

    screenshot: "only-on-failure",

    video: "retain-on-failure",
  },

  projects: [

    {
      name: "chromium",
      use: {
        ...devices["Desktop Chrome"],
      },
    },

  ],
});
```

A configuração deve ser adaptada à infraestrutura do projeto.

---

# 41. Execução

Executar todos os testes:

```bash
npx playwright test
```

Executar um arquivo:

```bash
npx playwright test tests/e2e/oferta/oferta-create.spec.ts
```

Executar em modo UI:

```bash
npx playwright test --ui
```

Executar com browser visível:

```bash
npx playwright test --headed
```

Executar um teste específico:

```bash
npx playwright test -g "deve criar uma oferta"
```

---

# 42. CI/CD

Os testes Playwright devem ser executados no pipeline CI.

Fluxo recomendado:

```text
Build
  ↓
Unit Tests
  ↓
Integration Tests
  ↓
Deploy Test Environment
  ↓
Playwright
  ↓
Build/Deploy
```

Em ambientes apropriados, testes E2E podem ser executados antes da promoção para produção.

---

# 43. Evidências de Falha

Quando um teste falhar, preservar evidências suficientes para diagnóstico.

Preferencialmente:

- screenshot;
- trace;
- vídeo quando necessário;
- logs;
- URL;
- informações do teste.

Configuração recomendada:

```typescript
use: {
  trace: "on-first-retry",
  screenshot: "only-on-failure",
  video: "retain-on-failure",
}
```

Não utilizar vídeo para todos os testes sem necessidade devido ao custo de armazenamento.

---

# 44. Flaky Tests

Testes instáveis devem ser tratados como defeitos.

Não resolver flaky test simplesmente aumentando:

```typescript
waitForTimeout(...)
```

ou aumentando indiscriminadamente retries.

Investigar:

- sincronização;
- dados;
- concorrência;
- ambiente;
- dependências;
- seletores;
- estado compartilhado.

Retries podem reduzir impacto operacional, mas não substituem a correção da causa.

---

# 45. Dados Determinísticos

Testes devem utilizar dados previsíveis.

Evitar dependência de:

```text
hora atual
ordem aleatória
dados externos
serviços instáveis
estado manual do ambiente
```

quando isso não fizer parte do comportamento testado.

Quando necessário, controlar:

- data;
- hora;
- randomização;
- ambiente;
- dados.

---

# 46. Testes Paralelos

Os testes devem ser preparados para execução paralela sempre que possível.

Isso exige:

- dados isolados;
- usuários independentes;
- tenants independentes quando aplicável;
- ausência de estado global compartilhado.

Não assumir que os testes serão executados sequencialmente.

---

# 47. Regras para o GitHub Copilot

Ao gerar testes Playwright, siga obrigatoriamente estas diretrizes:

- Utilize Playwright Test.
- Utilize TypeScript.
- Organize testes por Feature-First.
- Crie testes orientados ao comportamento do usuário.
- Não teste detalhes internos do React.
- Não teste implementação interna de componentes.
- Prefira `getByRole`.
- Prefira `getByLabel`.
- Prefira `getByPlaceholder`.
- Utilize `getByTestId` quando necessário.
- Evite seletores CSS frágeis.
- Evite XPath.
- Não utilize `waitForTimeout` como mecanismo normal de sincronização.
- Utilize o auto-waiting do Playwright.
- Toda ação importante deve possuir uma assertion relevante.
- Testes devem ser independentes.
- Não dependa da ordem de execução.
- Não dependa de dados criados por outro teste.
- Utilize fixtures para preparação recorrente.
- Utilize `storageState` para sessões autenticadas quando apropriado.
- Utilize Page Objects somente quando houver benefício real.
- Não criar abstrações desnecessárias.
- Utilize mocks somente quando fizer sentido.
- Não substituir todos os testes E2E por mocks.
- Fluxos críticos devem possuir testes integrados com APIs reais quando possível.
- Utilize dados determinísticos.
- Evite testes excessivamente longos.
- Divida cenários independentes em testes independentes.
- Teste fluxos de sucesso.
- Teste erros relevantes.
- Teste validações relevantes.
- Teste autorização quando aplicável.
- Teste responsividade quando fizer parte do requisito.
- Utilize screenshot comparison somente quando houver necessidade de validação visual.
- Preserve trace e screenshot em falhas.
- Trate flaky tests como defeitos.
- Não utilize retries como solução definitiva para instabilidade.
- Não utilize screenshots como única assertion.
- Não utilize classes CSS geradas como locator.
- Não utilizar posição do elemento como critério de seleção.
- Mantenha testes legíveis para pessoas não especialistas em Playwright.
- Nomeie testes descrevendo o comportamento esperado.
- Mantenha os testes alinhados às especificações funcionais do SDD.

---

# 48. Checklist Rápido

- [ ] Teste representa um comportamento do usuário
- [ ] Teste possui Arrange / Act / Assert
- [ ] Teste possui assertions
- [ ] Locator preferencialmente semântico
- [ ] Sem seletores CSS frágeis
- [ ] Sem XPath desnecessário
- [ ] Sem `waitForTimeout`
- [ ] Dados determinísticos
- [ ] Teste independente
- [ ] Sem dependência da ordem
- [ ] Autenticação reutilizada quando apropriado
- [ ] Fixtures utilizadas quando necessário
- [ ] Page Object utilizado somente quando agrega valor
- [ ] Fluxo de sucesso coberto
- [ ] Erros relevantes cobertos
- [ ] Validações relevantes cobertas
- [ ] Autorização coberta quando aplicável
- [ ] Responsividade coberta quando aplicável
- [ ] Evidências de falha configuradas
- [ ] Sem flaky tests conhecidos
- [ ] Teste executado localmente
- [ ] Teste executado no CI
- [ ] Teste alinhado à especificação SDD