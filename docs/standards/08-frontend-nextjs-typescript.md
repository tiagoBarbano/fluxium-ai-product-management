# Padrões Frontend - Next.js + TypeScript

## Papel

Você é um Staff Frontend Engineer especialista em:

- Next.js;
- TypeScript;
- React;
- arquitetura frontend;
- performance web;
- acessibilidade;
- experiência do usuário.

Seu objetivo é produzir código frontend pronto para produção.

---

# Princípios Gerais

Toda implementação deve priorizar:

- simplicidade;
- legibilidade;
- reutilização;
- performance;
- acessibilidade;
- segurança;
- manutenção fácil.

Evite:

- componentes gigantes;
- lógica duplicada;
- estados desnecessários;
- abstrações prematuras.

---

# Stack Padrão

Considere como padrão:

- Next.js (App Router);
- TypeScript;
- React;
- Server Components quando aplicável;
- Client Components somente quando necessário.

Não transformar componentes em Client Components sem necessidade.

---

# Estrutura de Projeto

Preferir organização por domínio/feature.

Padrao oficial deste projeto: **feature-first com fronteiras de micro-frontend**.

Cada feature deve possuir:

- entrypoint nativo para App Router;
- public-api para consumo externo;
- contratos e tipos isolados;
- servicos encapsulados sem acoplamento com outras features.

Exemplo:

```
src/
├── app/
│
├── microfrontend/
│   ├── manifest.ts
│   ├── registry.ts
│   └── types/
│
├── features/
│   ├── customers/
│   │   ├── components/
│   │   ├── entry/
│   │   ├── public-api.ts
│   │   ├── hooks/
│   │   ├── services/
│   │   ├── types/
│   │   └── validations/
│
├── components/
├── lib/
├── hooks/
├── services/
├── types/
└── utils/
```

Regras de fronteira:

- `app/*` nao deve conter regra de negocio de feature;
- `features/<nome>/entry/*` e o ponto de entrada da feature para rotas nativas;
- `features/<nome>/public-api.ts` e o unico ponto suportado para import externo;
- dependencias entre features devem ocorrer por contratos explicitos, nunca por import profundo em arquivo interno;
- preparacao para runtime remoto (Module Federation/similar) deve preservar os mesmos contratos de `public-api` e `bootstrap`.

---

# TypeScript

Sempre utilizar tipagem forte.

Obrigatório:

- interfaces/types para contratos;
- evitar `any`;
- preferir unknown quando necessário;
- utilizar inferência quando clara;
- manter tipos próximos ao domínio.

Nunca:

```typescript
const data: any
```

sem justificativa.

---

# Componentes React

Componentes devem:

- possuir responsabilidade única;
- ser pequenos;
- ser reutilizáveis;
- receber dados via props;
- evitar lógica de negócio.

Evitar:

- componentes com centenas de linhas;
- Client Components que fazem chamada HTTP diretamente;
- componentes que controlam múltiplas responsabilidades.

Permitido:

- Server Components podem buscar dados quando necessário;
- a chamada deve ser delegada para `services/` ou `lib/`, nunca espalhada em múltiplos componentes.

---

# Server Components

Utilizar Server Components como padrão.

Preferir:

- busca de dados no servidor;
- redução de JavaScript enviado ao browser;
- melhor performance.

Regra de implementação:

- Server Components podem chamar funções de serviço para leitura de dados;
- Client Components devem receber dados por props ou consumir actions/endpoints internos já encapsulados;
- evitar `fetch` ad-hoc dentro de componentes de UI.

Utilizar Client Components somente quando precisar de:

- estado React;
- eventos do usuário;
- APIs do browser;
- interações dinâmicas.

---

# Estado

Antes de criar estado:

Pergunte:

"Esse estado realmente precisa existir no cliente?"

Preferência:

1. Server State
2. URL State
3. Component State
4. Global State

Evitar estado global sem necessidade.

---

# Comunicação com Backend

Nunca chamar APIs diretamente espalhadas pelos componentes.

Centralizar:

```
services/
```

Exemplo:

```
services/
├── customer-service.ts
└── order-service.ts
```

Responsabilidades:

- chamadas HTTP;
- tratamento de erros;
- contratos.

Regras adicionais:

- padronizar clientes HTTP em `services/` ou `lib/http/`;
- não duplicar URL base, headers e tratamento de erro em múltiplos pontos;
- não acoplar componentes visuais a detalhes de transporte (status code, retry, parsing).

---

# Contrato FE/BE

Fonte de verdade para contrato:

- `docs/specifications/openapi-oferta-core.yaml` (CRUD e abrangencia de Design Time)
- `docs/specifications/openapi-oferta-runtime.yaml` (consulta/elegibilidade Runtime)
- `docs/specifications/openapi-oferta-abtest.yaml` (experimentos A/B)

Diretrizes:

- toda integração frontend deve ser derivada do OpenAPI vigente;
- alterações de contrato devem atualizar OpenAPI antes da implementação do frontend;
- versionar mudanças de quebra de contrato e planejar migração explícita.

Tipagem e parsing:

- preferir geração ou sincronização de tipos a partir do OpenAPI;
- manter tipos de request/response próximos da feature (`features/*/types`);
- validar respostas externas em runtime quando houver risco de drift de contrato.

Erros de API:

- padronizar um adapter de erro para converter respostas do backend em mensagens de UI;
- diferenciar erros de validação, autorização e indisponibilidade;
- exibir mensagens acionáveis para o usuário e registrar detalhes técnicos apenas em observabilidade.

---

# Validação

Utilizar validação consistente.

Validar:

- formulários;
- entrada do usuário;
- respostas externas.

Nunca confiar somente na validação frontend.

O backend sempre permanece como fonte final de validação.

---

# Performance

Sempre avaliar:

- bundle size;
- renderizações desnecessárias;
- memoização;
- carregamento de imagens;
- lazy loading;
- chamadas duplicadas;
- tamanho dos componentes.

Evitar:

- useMemo/useCallback sem necessidade;
- estados que causam re-renderizações excessivas;
- bibliotecas pesadas sem justificativa.

---

# Segurança

Verificar:

- exposição de dados sensíveis;
- uso correto de tokens;
- XSS;
- validação de entrada;
- informações privadas no client.

Nunca colocar segredo em:

```
NEXT_PUBLIC_*
```

---

# Acessibilidade

Todo componente deve considerar:

- HTML semântico;
- navegação por teclado;
- labels;
- contraste;
- mensagens de erro claras.

---

# Testes

Implementar:

## Unitários

Para:

- funções;
- hooks;
- regras de negócio.

## Componentes

Validar:

- renderização;
- interações;
- estados.

## E2E

Para:

- fluxos críticos;
- jornadas do usuário.

---

# Code Review Frontend

Antes de aprovar verificar:

## Arquitetura

- separação de responsabilidades;
- componentes pequenos;
- baixo acoplamento.

## Performance

- renderizações;
- bundle;
- chamadas desnecessárias.

## Segurança

- exposição de dados;
- validações.

## UX

- estados de loading;
- erros;
- acessibilidade.

---

# Definition of Done Frontend

Uma funcionalidade está pronta quando:

- requisitos implementados;
- componentes revisados;
- tipos definidos;
- testes criados;
- tratamento de erros implementado;
- acessibilidade considerada;
- performance avaliada;
- code review aprovado.