# Autorização Fluxium

Este módulo implementa o provider interno de identidade do Fluxium e adapta seus
claims ao domínio da plataforma. O fluxo atual cobre emissão local de JWT para
usuários e consumers, além do grant OIDC `client_credentials`.

O backend valida tokens e expõe uma superfície administrativa mínima para o ciclo 
local de segurança:

- `POST /api/v1/identity/users`: cria usuários dentro do tenant do administrador; 
- `POST /api/v1/identity/users/token`: emite token para usuário local; 
- `POST /api/v1/identity/users/token/refresh`: rotaciona refresh token de usuário;
- `POST /api/v1/identity/consumers`: cria consumer e retorna o segredo uma única vez; 
- `POST /api/v1/identity/consumers/{client_id}/credentials`: rotaciona o segredo; 
- `POST /api/v1/identity/token`: emite token usando credenciais do consumer. 
- `POST /api/v1/auth/realms/{realm}/protocol/openid-connect/token`: endpoint OIDC
	interno para `client_credentials`;
- `GET /api/v1/auth/realms/{realm}/.well-known/openid-configuration`: discovery OIDC.

O discovery anuncia os grants `client_credentials` e `refresh_token`. O refresh
é rotacionado e deve ser enviado somente ao endpoint OIDC por HTTPS.

As rotas administrativas exigem `ADMIN`. A senha e os segredos são armazenados 
somente como hashes; o segredo bruto não deve ser persistido ou registrado em logs. 
O router depende de `IdentityProvisioningPort`, e a emissão é centralizada em
`OidcTokenIssuer`. HS256 permanece como default local; para ambientes com
múltiplos serviços, configure `FLUXIUM_IDENTITY_JWT_ALGORITHM=RS256` com as
chaves PEM e publique a chave em `/.well-known/jwks.json`.

Refresh tokens são opacos, armazenados somente como hash, expiram conforme
`FLUXIUM_IDENTITY_REFRESH_TOKEN_TTL_SECONDS` e são consumidos uma única vez.

## Claims aceitas

O adapter valida a assinatura HS256, `sub` e `exp`. `issuer` e `audience` são
opcionais na configuração local e obrigatórios quando configurados. Os claims
normalizados são:

- `sub`: identificador do usuário ou processo;
- `tenant_id` ou `tenantId`: tenant autenticado;
- `workspace_id`/`workspaceId` ou `workspace_ids`/`workspaceIds`: workspaces autorizados;
- `roles`: papéis `ADMIN`, `PRODUCT_MANAGER`, `CONTRIBUTOR` e `VIEWER`.

Também é aceita a origem `realm_access.roles` para compatibilidade de tokens,
mas o contrato oficial do provedor de identidade deve ser congelado antes da produção.

O tenant e os workspaces são sempre derivados do token. O backend não aceita
esses valores como fonte de autenticação no corpo ou em headers confiados pelo
cliente.