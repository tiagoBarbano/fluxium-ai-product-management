# 10 - Confluence - Documentação do Produto

Este documento define as regras para agentes de IA responsáveis pela criação e manutenção da documentação do **produto** no Confluence.
A documentação deve representar o comportamento, funcionalidades, regras, fluxos, integrações e decisões relevantes do produto de forma clara, consistente e atualizada.
O Confluence deve ser tratado como uma **base de conhecimento do produto**, e não como documentação do processo de desenvolvimento.

---

# 1. Objetivo

A documentação deve permitir que uma pessoa compreenda:

- o que o produto faz;
- quais capacidades possui;
- como suas funcionalidades funcionam;
- quais regras de negócio existem;
- quais fluxos são suportados;
- como as funcionalidades se relacionam;
- quais integrações existem;
- quais limitações existem;
- como o produto deve se comportar.

A documentação deve ser útil para:

- Product Managers;
- Product Owners;
- desenvolvedores;
- arquitetos;
- QA;
- suporte;
- operações;
- stakeholders.

---

# 2. Princípios

A documentação deve priorizar:

- clareza;
- precisão;
- simplicidade;
- consistência;
- rastreabilidade;
- atualização;
- ausência de duplicidade.

O agente deve documentar o **produto real**, não aquilo que supõe que o produto deveria fazer.

Não inventar:

- funcionalidades;
- regras de negócio;
- comportamentos;
- APIs;
- integrações;
- telas;
- fluxos;
- decisões.

Quando uma informação não estiver confirmada, indicar explicitamente a necessidade de validação.

---

# 3. Antes de Criar uma Página

Antes de criar uma página, o agente deve pesquisar o Confluence.

Pesquisar por:

- nome da funcionalidade;
- nome da feature;
- nome do produto;
- termos relacionados;
- regras de negócio;
- APIs;
- integrações;
- componentes relacionados.

Verificar se:

1. já existe uma página sobre o assunto;
2. existe uma página que possa ser atualizada;
3. existe conteúdo semelhante;
4. existe uma página pai adequada.

**Preferir atualizar uma página existente em vez de criar conteúdo duplicado.**

---

# 4. Estrutura do Produto

A documentação deve representar a estrutura funcional do produto.

Uma estrutura possível:

```text
Produto
│
├── Visão Geral
│
├── Capacidades
│   ├── Cadastro
│   ├── Produtos
│   ├── Regras
│   └── Workflow
│
├── Features
│   ├── Feature A
│   ├── Feature B
│   └── Feature C
│
├── Fluxos
│   ├── Fluxo A
│   └── Fluxo B
│
├── Regras de Negócio
│
├── Integrações
│
├── APIs
│
└── Operação
```

A estrutura real deve respeitar a organização existente do Space.

Não criar uma nova hierarquia quando já existir uma estrutura consolidada.

---

# 5. Página de Feature

Quando uma feature possuir documentação própria, utilizar uma estrutura semelhante a:

```markdown
# Feature: Nome
## Objetivo
## Contexto
## Descrição
## Comportamento
## Regras de Negócio
## Fluxo
## Entradas
## Saídas
## Integrações
## Dependências
## Limitações
## Critérios Importantes
## Referências
```

Utilizar somente as seções necessárias.

---

# 6. Capacidades do Produto

Capacidades representam aquilo que o produto é capaz de fazer.

Exemplo:

```text
Produto
 └── Gestão de Produtos
      ├── Criar produto
      ├── Editar produto
      ├── Versionar produto
      └── Publicar produto
```

Cada capacidade deve possuir uma descrição clara de:

- objetivo;
- comportamento;
- regras;
- entradas;
- resultados;
- dependências.

---

# 7. Regras de Negócio

Regras de negócio devem ser documentadas de forma objetiva.

Exemplo:

```text
Regra: Produto publicado não pode ser alterado.

Quando:
- produto possui status PUBLISHED;

Então:
- alterações devem gerar uma nova versão.
```

Sempre que possível, identificar:

- condição;
- comportamento esperado;
- exceções;
- resultado.

Não transformar detalhes de implementação em regra de negócio.

---

# 8. Fluxos

Fluxos importantes devem ser documentados de forma visual ou textual.

Exemplo:

```text
Usuário
   ↓
Criar Produto
   ↓
Validar Dados
   ↓
Salvar como DRAFT
   ↓
Enviar para Aprovação
   ↓
Aprovar
   ↓
PUBLICADO
```

O fluxo deve representar o comportamento real conhecido.

Quando existirem exceções, documentá-las.

---

# 9. APIs

Quando uma API fizer parte do comportamento do produto, documentar:

- objetivo;
- endpoint;
- método;
- autenticação;
- entradas;
- parâmetros;
- resposta;
- erros;
- regras relevantes;
- exemplos.

Exemplo:

```text
POST /products
```

Request:

```json
{
  "name": "Produto"
}
```

Response:

```json
{
  "id": "prd_001",
  "status": "DRAFT"
}
```

A documentação não deve afirmar que uma API existe sem confirmação.

---

# 10. Telas e Interfaces

Quando a documentação tratar de uma funcionalidade visual, descrever:

- objetivo da tela;
- informações apresentadas;
- ações disponíveis;
- regras;
- estados;
- mensagens;
- permissões;
- comportamento esperado.

Quando uma imagem ou screenshot for relevante, associá-la à documentação quando disponível.

---

# 11. Integrações

Para cada integração relevante, documentar:

- sistema integrado;
- objetivo;
- direção da comunicação;
- dados envolvidos;
- autenticação;
- eventos ou endpoints;
- comportamento em caso de erro;
- dependências.

Exemplo:

```text
Produto
   |
   v
API
   |
   v
Sistema Externo
```

Não documentar detalhes que não estejam confirmados.

---

# 12. Comportamento e Estado

Quando uma funcionalidade possuir estados, documentá-los explicitamente.

Exemplo:

```text
DRAFT
  ↓
IN_REVIEW
  ↓
APPROVED
  ↓
PUBLISHED
```

Documentar:

- estados possíveis;
- transições;
- condições;
- ações permitidas;
- ações proibidas.

---

# 13. Permissões

Quando o comportamento depender de perfil ou permissão, documentar.

Exemplo:

| Ação | Administrador | Operador |
|---|---|---|
| Criar | Sim | Sim |
| Editar | Sim | Sim |
| Publicar | Sim | Não |
| Excluir | Sim | Não |

As permissões devem representar o comportamento real do produto.

---

# 14. Atualização da Documentação

Quando uma funcionalidade for alterada, o agente deve avaliar as páginas relacionadas.

Verificar:

- feature;
- capacidade;
- fluxo;
- regras de negócio;
- API;
- integração;
- telas;
- exemplos;
- referências.

Evitar atualizar apenas uma página quando a alteração impactar outras partes da documentação.

---

# 15. Alterações de Comportamento

Quando uma alteração modificar o comportamento do produto, atualizar a documentação correspondente.

Exemplo:

```text
Antes:
Produto publicado pode ser editado.

Depois:
Produto publicado não pode ser editado.
Alterações criam nova versão.
```

A documentação deve representar o comportamento atual.

Informações históricas devem permanecer somente quando possuírem valor documental.

---

# 16. Documentação vs Implementação

Não confundir:

```text
Produto
↓
O que o sistema faz
```

com:

```text
Implementação
↓
Como o código faz
```

A documentação de produto deve priorizar:

- comportamento;
- regras;
- fluxos;
- capacidades;
- experiência;
- integrações.

Detalhes internos de código devem ser documentados somente quando forem relevantes para compreender o produto ou sua operação.

---

# 17. Exemplos

Exemplos devem ser:

- simples;
- representativos;
- atuais;
- consistentes com o produto.

Não utilizar:

- credenciais reais;
- dados pessoais reais;
- tokens;
- secrets;
- informações sensíveis.

Utilizar dados fictícios:

```text
customer_001
product_001
tenant_001
user@example.com
```

---

# 18. Terminologia

Utilizar sempre a terminologia oficial do produto.

Exemplo:

```text
Feature
Produto
Cliente
Workspace
Regra
Fluxo
Publicação
Versão
```

Não utilizar nomes diferentes para representar o mesmo conceito.

Quando um termo for alterado, avaliar a atualização das páginas relacionadas.

---

# 19. Consistência entre Páginas

Uma informação deve possuir uma fonte principal sempre que possível.

Evitar repetir a mesma regra em várias páginas.

Quando uma informação for necessária em diferentes contextos:

- manter a definição principal em uma página;
- referenciar a página quando possível;
- evitar cópias independentes.

Isso reduz inconsistências.

---

# 20. Conteúdo Obsoleto

Quando encontrar conteúdo potencialmente obsoleto:

1. verificar a informação atual;
2. identificar páginas relacionadas;
3. atualizar quando houver evidência;
4. remover somente quando claramente inválido;
5. preservar histórico quando relevante.

Quando necessário:

```text
Status: Obsoleto
Substituído por: Nome da página
```

---

# 21. Status da Documentação

Quando útil, utilizar:

```text
Rascunho
Em revisão
Ativo
Obsoleto
Arquivado
```

O status deve refletir o estado real conhecido.

Não utilizar o título para indicar versão:

```text
Produto V1
Produto V2
Produto FINAL
Produto FINAL 2
```

Utilizar o histórico do Confluence para versionamento.

---

# 22. Decisões de Produto

Decisões relevantes para o comportamento do produto podem ser documentadas.

Registrar, quando aplicável:

```text
Contexto
Problema
Decisão
Comportamento resultante
Impactos
```

Não transformar uma sugestão do agente em decisão oficial.

---

# 23. Busca por Impacto

Antes de alterar uma funcionalidade documentada, pesquisar termos relacionados para identificar possíveis impactos.

Exemplo:

```text
Alteração:
Publicação de Produto

Pesquisar:
├── Produto
├── Versionamento
├── Aprovação
├── Regras
├── Workflow
├── API
└── Integrações
```

O objetivo é evitar documentação inconsistente.

---

# 24. Segurança da Documentação

Nunca publicar no Confluence:

- senhas;
- tokens;
- API keys;
- secrets;
- credenciais;
- chaves privadas;
- dados pessoais desnecessários;
- informações confidenciais sem autorização.

Utilizar placeholders quando necessário:

```text
${API_KEY}
${DATABASE_PASSWORD}
${TOKEN}
```

---

# 25. Regra de Conservadorismo

O agente deve ser conservador ao modificar documentação existente.

Quando houver dúvida sobre:

- regra de negócio;
- comportamento;
- decisão de produto;
- integração;
- permissão;
- fluxo;
- informação histórica;

não assumir.

Manter a informação existente e sinalizar a necessidade de confirmação.

---

# 26. Regras para o Agente

Ao criar ou manter documentação do produto:

- Pesquise antes de criar.
- Prefira atualizar páginas existentes.
- Evite duplicação.
- Respeite a hierarquia existente.
- Documente o comportamento real do produto.
- Utilize a terminologia oficial.
- Mantenha regras de negócio objetivas.
- Documente fluxos importantes.
- Documente APIs e integrações quando fizerem parte do produto.
- Avalie impacto em páginas relacionadas.
- Mantenha informações consistentes entre páginas.
- Não invente funcionalidades ou comportamentos.
- Não transforme hipóteses em fatos.
- Não confunda produto com implementação.
- Preserve informações válidas.
- Atualize informações obsoletas quando houver evidência.
- Não remova conteúdo relevante sem justificativa.
- Não publique informações sensíveis.
- Utilize o histórico do Confluence para versionamento.
- Priorize qualidade e utilidade da documentação.

---

# 27. Checklist

Antes de concluir uma alteração:

- [ ] A documentação existente foi pesquisada.
- [ ] Não existe duplicação desnecessária.
- [ ] A página está no local correto.
- [ ] O título representa corretamente o conteúdo.
- [ ] O comportamento documentado corresponde ao produto atual.
- [ ] As regras de negócio estão claras.
- [ ] Fluxos relevantes estão documentados.
- [ ] APIs e integrações relevantes foram consideradas.
- [ ] Terminologia está consistente.
- [ ] Páginas relacionadas foram avaliadas.
- [ ] Não existem informações inventadas.
- [ ] Não existem secrets ou credenciais.
- [ ] Conteúdo obsoleto foi tratado quando identificado.
- [ ] Links e referências estão corretos.
- [ ] A documentação está objetiva e navegável.