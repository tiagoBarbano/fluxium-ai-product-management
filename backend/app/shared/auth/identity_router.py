import base64
from urllib.parse import parse_qs

from fastapi import APIRouter, Depends, HTTPException, Path, Request, status

from .auth_model import IdentityClaims, UserRole
from .authorization import require_roles
from .identity_repository import MongoIdentityRepository
from .identity_port import IdentityProvisioningPort
from .identity_schemas import (
    ConsumerCredentialsResponse,
    ConsumerTokenRequest,
    CreateConsumerRequest,
    CreateUserRequest,
    OidcDiscoveryResponse,
    OidcTokenResponse,
    RefreshTokenRequest,
    TokenResponse,
    UserTokenRequest,
    UserResponse,
)
from .identity_service import IdentityConflictError, IdentityService
from .oidc import OidcTokenIssuer
from .security import get_current_principal
from ...config.settings import get_settings
from ...database.mongo import get_database


router = APIRouter(prefix="/identity", tags=["identity"])
oidc_router = APIRouter(
    prefix="/auth/realms/{realm}/protocol/openid-connect",
    tags=["auth-oidc"],
)
oidc_discovery_router = APIRouter(
    prefix="/auth/realms/{realm}",
    tags=["auth-oidc"],
)


def get_identity_service() -> IdentityProvisioningPort:
    database = get_database()
    repository = MongoIdentityRepository(
        users=database["identity_users"],
        consumers=database["identity_consumers"],
        refresh_tokens=database["identity_refresh_tokens"],
    )
    return IdentityService(repository, get_settings())


admin_dependency = require_roles(UserRole.ADMIN)


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    request: CreateUserRequest,
    principal: IdentityClaims = Depends(admin_dependency),
    service: IdentityProvisioningPort = Depends(get_identity_service),
) -> UserResponse:
    try:
        return await service.create_user(request, principal)
    except IdentityConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.post("/consumers", response_model=ConsumerCredentialsResponse, status_code=status.HTTP_201_CREATED)
async def create_consumer(
    request: CreateConsumerRequest,
    principal: IdentityClaims = Depends(admin_dependency),
    service: IdentityProvisioningPort = Depends(get_identity_service),
) -> ConsumerCredentialsResponse:
    try:
        return await service.create_consumer(request, principal)
    except IdentityConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.post("/consumers/{client_id}/credentials", response_model=ConsumerCredentialsResponse)
async def rotate_consumer_credentials(
    client_id: str = Path(min_length=8, max_length=128),
    principal: IdentityClaims = Depends(admin_dependency),
    service: IdentityProvisioningPort = Depends(get_identity_service),
) -> ConsumerCredentialsResponse:
    try:
        return await service.rotate_consumer_credentials(client_id, principal)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/token", response_model=TokenResponse)
async def issue_consumer_token(
    request: ConsumerTokenRequest,
    service: IdentityProvisioningPort = Depends(get_identity_service),
) -> TokenResponse:
    try:
        return await service.issue_consumer_token(
            request.client_id,
            request.client_secret,
            request.expires_in_seconds,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/users/token", response_model=TokenResponse)
async def issue_user_token(
    request: UserTokenRequest,
    service: IdentityProvisioningPort = Depends(get_identity_service),
) -> TokenResponse:
    try:
        return await service.issue_user_token(
            request.username,
            request.password,
            request.tenant_id,
            request.expires_in_seconds,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/users/token/refresh", response_model=TokenResponse)
async def refresh_user_token(
    request: RefreshTokenRequest,
    service: IdentityProvisioningPort = Depends(get_identity_service),
) -> TokenResponse:
    try:
        return await service.refresh_user_token(
            request.refresh_token,
            request.expires_in_seconds,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@oidc_router.post("/token", response_model=OidcTokenResponse)
async def oidc_token_client_credentials(
    realm: str,
    request: Request,
    service: IdentityProvisioningPort = Depends(get_identity_service),
) -> OidcTokenResponse:
    content_type = request.headers.get("content-type", "")
    if "multipart/form-data" in content_type:
        raise HTTPException(status_code=415, detail="multipart_form_not_supported")
    form = parse_qs((await request.body()).decode("utf-8"), keep_blank_values=True)
    grant_type = form.get("grant_type", [""])[0]
    client_id = form.get("client_id", [""])[0]
    client_secret = form.get("client_secret", [""])[0]
    refresh_token = form.get("refresh_token", [""])[0]
    requested_scope = form.get("scope", ["openid"])[0] or "openid"

    if grant_type == "refresh_token":
        if not refresh_token:
            raise HTTPException(status_code=400, detail="invalid_request")
        try:
            scope = " ".join(dict.fromkeys(f"openid {requested_scope}".split()))
            expires = get_settings().identity_access_token_ttl_seconds
            issued = await service.refresh_user_oidc_token(
                refresh_token,
                expires,
                tenant_id=realm,
                scope=scope,
            )
        except PermissionError as exc:
            raise HTTPException(status_code=401, detail="invalid_grant") from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        return OidcTokenResponse(
            access_token=issued.access_token,
            expires_in=expires,
            id_token=issued.id_token,
            scope=scope,
            refresh_token=issued.refresh_token,
            refresh_expires_in=issued.refresh_expires_in,
        )

    if not client_id or not client_secret:
        authorization = request.headers.get("Authorization", "")
        if authorization.lower().startswith("basic "):
            try:
                decoded = base64.b64decode(authorization.split(" ", 1)[1]).decode("utf-8")
                client_id, client_secret = decoded.split(":", 1)
            except (ValueError, UnicodeDecodeError):
                pass
    if grant_type != "client_credentials":
        raise HTTPException(status_code=400, detail="unsupported_grant_type")
    if not client_id or not client_secret:
        raise HTTPException(status_code=401, detail="invalid_client")

    try:
        scope = " ".join(dict.fromkeys(f"openid {requested_scope}".split()))
        expires = get_settings().identity_access_token_ttl_seconds
        issued = await service.issue_consumer_oidc_token(
            client_id,
            client_secret,
            expires,
            tenant_id=realm,
            scope=scope,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=401, detail="invalid_client") from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return OidcTokenResponse(
        access_token=issued.access_token,
        expires_in=expires,
        id_token=issued.id_token,
        scope=scope,
    )


@oidc_discovery_router.get(
    "/.well-known/openid-configuration",
    response_model=OidcDiscoveryResponse,
)
async def oidc_discovery(realm: str, request: Request) -> OidcDiscoveryResponse:
    settings = get_settings()
    issuer = settings.identity_jwt_issuer or "fluxium-internal"
    token_endpoint = str(request.url_for("oidc_token_client_credentials", realm=realm))
    return OidcDiscoveryResponse(
        issuer=issuer,
        token_endpoint=token_endpoint,
        grant_types_supported=["client_credentials", "refresh_token"],
        response_types_supported=["token"],
        subject_types_supported=["public"],
        id_token_signing_alg_values_supported=[settings.identity_jwt_algorithm.upper()],
        scopes_supported=["openid"],
        jwks_uri=str(request.url_for("oidc_jwks", realm=realm)),
    )


@oidc_discovery_router.get("/.well-known/jwks.json", name="oidc_jwks")
async def oidc_jwks() -> dict[str, list[dict[str, object]]]:
    jwk = OidcTokenIssuer(get_settings()).public_jwk()
    return {"keys": [jwk] if jwk else []}