# Fluxo de Desenvolvimento

Toda nova funcionalidade deve seguir esta sequência:

1. specification.md (cliente)
2. analysis.md
3. implementation-plan.md
4. implementação
5. checklist.md
6. traceability.md
7. code review
8. pull request
9. database noSql
10. confluence

A especificação é a única fonte de verdade.

## Fluxo Operacional (PoC atual)

1. Acesse o menu lateral e abra `Services`.
2. Crie um Service do tipo `API` ou `PIPELINE`.
3. No detalhe do Service, crie uma versão, valide e publique.
4. Para `PIPELINE`, associe um pipeline publicado na criação da versão.
5. Acesse `Deployments` para criar o deployment por ambiente (`STAGING` ou `PRODUCTION`).
6. Ative o deployment para permitir execução em runtime.
7. Acesse `Executions` para acompanhar status, latência e erros por execução.

## Navegação da Console

- Topbar e menu lateral permanecem fixos.
- O conteúdo de cada item (`Overview`, `Services`, `APIs`, `Pipelines`, `Deployments`, `Executions`) abre no painel central.

## Diagnóstico Rápido

- `ACTIVE_DEPLOYMENT_NOT_FOUND`: não existe deployment ativo para o Service no ambiente informado.
- `PATH_PARAMETER_MISSING`: o payload de execução não possui os campos exigidos pelo path template da API.
- `API_TIMEOUT`: a chamada externa excedeu o tempo configurado do step/deployment.

## APIs por Ambiente (Fase 1)

- O cadastro de API agora aceita configuração separada para `STAGING` e `PRODUCTION`.
- Cada ambiente possui `base_url`, `path`, `headers` e `authentication_ref` próprios.
- `STAGING` é opcional; `PRODUCTION` permanece obrigatório.
- O teste de API no detalhe permite selecionar o ambiente antes de executar.
- Compatibilidade: APIs legadas sem configuração por ambiente continuam funcionando com fallback para `PRODUCTION` usando `base_url/path/headers` do registro existente.
- Quando `authentication_ref` é informado, o runtime injeta o header `Authorization` usando o mapa configurado em `API_AUTHENTICATION_REFS` no backend (JSON `{ "ref": "Bearer token" }`).
- Também é possível configurar OAuth Client Credentials por ambiente com `token_url`, `client_id_ref`, `client_secret_ref` e `scope` opcional.
- O runtime busca o token OAuth no `token_url` e envia `Authorization: Bearer <token>` na chamada da API.
- Refs OAuth são resolvidas via `API_OAUTH_CLIENT_ID_REFS` e `API_OAUTH_CLIENT_SECRET_REFS` no backend (JSON).
- Prioridade de autenticação no runtime por ambiente: `oauth_client_credentials` > `authentication_ref` > sem header `Authorization`.

## Erros de autenticação (APIs)

- `AUTHENTICATION_REFERENCE_NOT_FOUND`: `authentication_ref` não foi encontrado no mapa configurado.
- `OAUTH_CLIENT_ID_REFERENCE_NOT_FOUND`: `client_id_ref` OAuth não foi encontrado no mapa configurado.
- `OAUTH_CLIENT_SECRET_REFERENCE_NOT_FOUND`: `client_secret_ref` OAuth não foi encontrado no mapa configurado.
- `OAUTH_TOKEN_REQUEST_FAILED`: falha HTTP/rede ao obter token OAuth.
- `OAUTH_TOKEN_TIMEOUT`: timeout na chamada do token endpoint OAuth.
- `OAUTH_TOKEN_INVALID_RESPONSE`: resposta do token endpoint inválida.
- `OAUTH_TOKEN_MISSING`: `access_token` ausente na resposta OAuth.