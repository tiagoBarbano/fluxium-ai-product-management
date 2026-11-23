# Specification Driven Development (SDD)

## Objetivo

Toda funcionalidade deve ser desenvolvida seguindo um processo orientado por especificação.

A especificação funcional é a única fonte de verdade para os requisitos de negócio.

Nunca implemente uma funcionalidade diretamente a partir de um pedido do usuário sem antes analisar sua especificação.

---

# Documentos de Entrada

Antes de iniciar qualquer implementação, leia obrigatoriamente:

- `docs/ai/00-instructions.md`
- `docs/standards/*`
- `docs/specifications/features/*`
- `docs/specifications/*`

Caso exista conflito entre documentação e código existente, informe antes de prosseguir.

---

# Fluxo de Desenvolvimento

## Etapa 1 — Análise

Objetivo:

Compreender completamente a especificação.

Gerar:

```

docs/plan/analysis.md

```

O documento deve conter:

- objetivo;
- requisitos funcionais;
- requisitos não funcionais;
- regras de negócio;
- fluxos principais;
- fluxos alternativos;
- pré-condições;
- pós-condições;
- validações;
- restrições;
- dependências;
- integrações;
- riscos;
- ambiguidades;
- dúvidas para o cliente.

Não implemente código nesta etapa.

---

## Etapa 2 — Planejamento

Objetivo:

Transformar a análise em um plano técnico.

Gerar:

```

docs/plan/implementation-plan.md

```

O plano deve conter:

- arquitetura proposta;
- componentes envolvidos;
- classes novas;
- classes alteradas;
- endpoints;
- DTOs;
- entidades;
- serviços;
- repositórios;
- integrações;
- eventos;
- alterações de banco;
- estratégia de testes.

Justifique decisões arquiteturais relevantes.

---

## Etapa 3 — Validação

Compare o plano com a especificação.

Confirme que:

- todos os requisitos estão cobertos;
- nenhuma funcionalidade extra será implementada;
- nenhuma regra de negócio foi omitida.

Caso exista qualquer inconsistência, interrompa a implementação.

---

## Etapa 4 — Implementação

Implemente apenas o que está previsto em:

- specification.md
- analysis.md
- implementation-plan.md

Sempre seguir os padrões definidos em `docs/standards/`.

Reutilize componentes existentes sempre que possível.

Evite alterações fora do escopo.

---

## Etapa 5 — Testes

Implemente os testes necessários para validar a funcionalidade.

Sempre considerar:

- testes unitários;
- testes de integração;
- cenários de erro;
- edge cases.

Todo requisito funcional deve possuir pelo menos um teste correspondente.

---

## Etapa 6 — Rastreabilidade

Atualize:

```

traceability.md

```

Relacionando:

- requisito;
- implementação;
- testes.

Exemplo:

| Requisito | Código | Testes |
|-----------|--------|---------|
| REQ-001 | CustomerService | CustomerServiceTest |

---

## Etapa 7 — Revisão

Execute uma revisão utilizando:

- Definition of Done
- Code Review

Verifique:

- arquitetura;
- performance;
- segurança;
- observabilidade;
- testes;
- aderência aos padrões.

---

## Critérios para Finalização

Uma funcionalidade somente pode ser considerada concluída quando:

- todos os requisitos foram implementados;
- nenhum requisito extra foi adicionado;
- todos os testes passaram;
- a arquitetura foi respeitada;
- o Definition of Done foi atendido;
- a revisão foi concluída.

Caso qualquer um desses critérios não seja atendido, informe explicitamente antes de finalizar.