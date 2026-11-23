"""Legacy authentication module, intentionally not mounted by the Fluxium app.

The active internal provider lives in ``identity_router.py``, ``identity_service.py``
and ``oidc.py``. This module is retained only as historical source material and
must not be imported by new code.
"""

import base64
import hashlib
import hmac
import os
import re
import secrets
import smtplib
import unicodedata
import uuid
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from html import escape
from urllib.parse import parse_qs, urlencode

import jwt
from app.audit.models import AuditActor, AuditResource
from app.audit.service import AuditService
from app.gateway.core.security import get_current_user
from app.gateway.models.auth import (
    ChangePasswordRequest,
    ConsumerCredentialsGenerateRequest,
    ConsumerCredentialsGenerateResponse,
    ConsumerTokenGenerateRequest,
    ConsumerTokenGenerateResponse,
    CreatePortalUserRequest,
    PortalAuthResponse,
    PortalConfirmEmailRequest,
    PortalConfirmEmailResponse,
    PortalLoginRequest,
    PortalPendingVerificationResponse,
    PortalRegisterRequest,
    PortalResendConfirmationRequest,
    PortalResendConfirmationResponse,
    PortalUserResponse,
    UpdateRolesRequest,
    UpdateTenantRequest,
)
from app.gateway.models.consumer import DEFAULT_CONSUMER_SCOPE, consumer_audience
from app.infra.db import client as client_db
from app.infra.logging_fast import log_json
from app.infra.settings import get_settings
from app.auth import portal_session
from app.services.billing_asaas import asaas_billing_service
from app.services.tenant_saas import PLAN_LIMITS, tenant_saas_service
from fluxium_shared.dependencies.tenant_validation import (
    TenantValidationError,
    resolve_tenant_id,
)
from fastapi import APIRouter, Depends, HTTPException, Request

db = client_db.gateway
db_core = client_db.core

settings = get_settings()
SECRET = settings.internal_jwt_secret

router = APIRouter(prefix="/admin/auth", tags=["Auth"])
audit_service = AuditService()
oidc_router = APIRouter(
    prefix="/auth/realms/{realm}/protocol/openid-connect", tags=["Auth OIDC"]
)

ROLE_PLATFORM_ADMIN = "platform_admin"
TRIAL_ROLE_ALIASES = {"platform_trial", "plataform_trial"}


def _as_utc_datetime(value: datetime | None) -> datetime | None:
    if not isinstance(value, datetime):
        return None
    if value.tzinfo is None:
        # Mongo can return naive UTC datetimes depending on client tz settings.
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _email_confirmation_required() -> bool:
    return settings.email_confirmation_required


def _email_confirmation_ttl_minutes() -> int:
    return max(5, settings.email_token_ttl_minutes)


def _email_resend_limit() -> int:
    return max(1, settings.email_resend_rate_limit_count)


def _email_resend_window_minutes() -> int:
    return max(1, settings.email_resend_rate_limit_window_minutes)


def _email_verify_base_url() -> str:
    return settings.email_verify_base_url.rstrip("/")


def _email_sender_enabled() -> bool:
    return settings.email_sender_enabled


def _token_hash(raw_token: str) -> str:
    return hmac.new(
        SECRET.encode("utf-8"), raw_token.encode("utf-8"), hashlib.sha256
    ).hexdigest()


async def _save_verification_token(user_id, email: str, username: str) -> str:
    now = datetime.now(tz=timezone.utc)
    expires_at = now + timedelta(minutes=_email_confirmation_ttl_minutes())

    raw_token = secrets.token_urlsafe(48)
    token_hash = _token_hash(raw_token)

    tokens = db_core.portal_email_verification_tokens
    await tokens.update_many(
        {
            "user_id": user_id,
            "used_at": None,
            "invalidated_at": None,
        },
        {"$set": {"invalidated_at": now}},
    )

    await tokens.insert_one(
        {
            "user_id": user_id,
            "email": email,
            "username": username,
            "token_hash": token_hash,
            "created_at": now,
            "expires_at": expires_at,
            "used_at": None,
            "invalidated_at": None,
        }
    )

    return raw_token


def _send_confirmation_email(
    email: str, username: str, tenant_id: str, raw_token: str
) -> None:
    verify_link = (
        f"{_email_verify_base_url()}/confirm-email?{urlencode({'token': raw_token})}"
    )

    subject = "Confirme seu e-mail para acessar a Fluxium"
    body = (
        f"Ola, {username}.\n\n"
        "Seu acesso ao portal Fluxium esta quase pronto.\n"
        "Confirme seu e-mail para ativar sua conta e acessar a plataforma:\n\n"
        f"Tenant ID: {tenant_id}\n\n"
        f"{verify_link}\n\n"
        f"Este link expira em {_email_confirmation_ttl_minutes()} minutos e pode ser usado uma unica vez.\n\n"
        "Ao entrar no portal, informe este Tenant ID no campo Tenant ID da tela de login.\n\n"
        "Se voce nao criou uma conta na Fluxium, ignore esta mensagem.\n"
    )
    html_body = _confirmation_email_html(
        username=username,
        tenant_id=tenant_id,
        verify_link=verify_link,
        ttl_minutes=_email_confirmation_ttl_minutes(),
    )

    if not _email_sender_enabled():
        log_json(
            "INFO",
            "email_sender_disabled_confirmation_link_generated",
            email_hash=hashlib.sha256(email.encode()).hexdigest(),
            username=username,
            token_generated=True,
        )
        return

    smtp_host = settings.email_smtp_host
    smtp_port = settings.email_smtp_port
    smtp_user = settings.email_smtp_user
    smtp_password = settings.email_smtp_password
    smtp_tls = settings.email_smtp_tls
    from_email = settings.email_from or smtp_user or "no-reply@fluxium.local"

    if not smtp_host:
        raise RuntimeError("EMAIL_SMTP_HOST is required when EMAIL_SENDER_ENABLED=true")
    if not smtp_port:
        raise RuntimeError("EMAIL_SMTP_PORT is required when EMAIL_SENDER_ENABLED=true")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = email
    msg.set_content(body)
    msg.add_alternative(html_body, subtype="html")

    with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=10) as server:
        if smtp_tls:
            server.starttls()

        if smtp_user and smtp_password:
            server.login(smtp_user, base64.b64decode(smtp_password).decode("utf-8"))

        server.send_message(msg)


def _confirmation_email_html(
    username: str, tenant_id: str, verify_link: str, ttl_minutes: int
) -> str:
    safe_username = escape(username)
    safe_tenant_id = escape(tenant_id)
    safe_verify_link = escape(verify_link, quote=True)
    return f"""\
<!doctype html>
<html lang="pt-BR">
    <body style="margin:0;background:#f4f7fb;font-family:Arial,sans-serif;color:#102548;">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="padding:32px 16px;">
            <tr><td align="center">
                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:600px;background:#ffffff;border:1px solid #dce8fb;">
                    <tr><td style="padding:28px 36px;background:#103c8c;">
                        <img src="https://app.fluxiumplataform.com/logo-new.png" alt="Fluxium Platform" width="240" style="display:block;width:240px;max-width:100%;height:auto;border:0;" />
                    </td></tr>
                    <tr><td style="padding:36px;">
                        <p style="margin:0 0 12px;font-size:16px;line-height:24px;">Ola, {safe_username}.</p>
                        <p style="margin:0 0 28px;font-size:15px;line-height:22px;color:#163d86;"><strong>Tenant ID:</strong> {safe_tenant_id}</p>
                        <h1 style="margin:0 0 16px;font-size:28px;line-height:36px;color:#163d86;">Confirme seu e-mail</h1>
                        <p style="margin:0 0 28px;font-size:16px;line-height:24px;">Seu acesso ao portal Fluxium esta quase pronto. Confirme seu e-mail para ativar sua conta e operar a plataforma.</p>
                        <a href="{safe_verify_link}" style="display:inline-block;padding:14px 22px;background:#1e4da9;color:#ffffff;font-size:16px;font-weight:bold;line-height:20px;text-decoration:none;">Confirmar e-mail</a>
                        <p style="margin:28px 0 0;font-size:14px;line-height:21px;color:#5f7396;">Este link expira em {ttl_minutes} minutos e pode ser usado uma unica vez.</p>
                        <p style="margin:16px 0 0;font-size:14px;line-height:21px;color:#5f7396;">Se o botao nao abrir, copie este endereco no navegador:<br /><a href="{safe_verify_link}" style="color:#1e4da9;word-break:break-all;">{safe_verify_link}</a></p>
                        <p style="margin:16px 0 0;font-size:14px;line-height:21px;color:#5f7396;">Ao entrar no portal, informe este Tenant ID no campo Tenant ID da tela de login.</p>
                    </td></tr>
                    <tr><td style="padding:20px 36px;background:#f8fbff;border-top:1px solid #dce8fb;font-size:12px;line-height:18px;color:#5f7396;">Fluxium Platform<br />Se voce nao criou uma conta, ignore esta mensagem.</td></tr>
                </table>
            </td></tr>
        </table>
    </body>
</html>
"""


async def _issue_and_send_confirmation_email(
    user_id, email: str, username: str, tenant_id: str
) -> None:
    raw_token = await _save_verification_token(
        user_id=user_id, email=email, username=username
    )
    _send_confirmation_email(
        email=email,
        username=username,
        tenant_id=tenant_id,
        raw_token=raw_token,
    )


async def _resend_pending_confirmation(user: dict) -> None:
    now = datetime.now(tz=timezone.utc)
    tokens = db_core.portal_email_verification_tokens
    resend_window = now - timedelta(minutes=_email_resend_window_minutes())
    resend_count = await tokens.count_documents(
        {
            "user_id": user.get("_id"),
            "created_at": {"$gte": resend_window},
        }
    )
    if resend_count >= _email_resend_limit():
        raise HTTPException(
            status_code=429,
            detail={
                "code": "EMAIL_CONFIRMATION_RATE_LIMITED",
                "message": "Limite de reenvio atingido. Tente novamente mais tarde.",
            },
        )

    try:
        await _issue_and_send_confirmation_email(
            user_id=user.get("_id"),
            email=str(user.get("email") or ""),
            username=user.get("username") or "usuario",
            tenant_id=str(user.get("tenant_id") or ""),
        )
    except Exception as exc:
        log_json(
            "ERROR",
            "email_confirmation_send_failed",
            username=user.get("username"),
            tenant_id=user.get("tenant_id"),
            error=str(exc),
        )
        raise HTTPException(
            status_code=503,
            detail={
                "code": "EMAIL_CONFIRMATION_SEND_FAILED",
                "message": "Nao foi possivel enviar o e-mail de confirmacao. Tente novamente.",
            },
        ) from exc


def _dev_token_endpoint_enabled() -> bool:
    return os.getenv("ENABLE_DEV_TOKEN_ENDPOINT", "false").lower() == "true"


def _hash_password(password: str, salt_hex: str) -> str:
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt_hex),
        200000,
    )
    return digest.hex()


def _verify_password(password: str, salt_hex: str, password_hash: str) -> bool:
    computed = _hash_password(password, salt_hex)
    return hmac.compare_digest(computed, password_hash)


async def _find_login_user(users, username: str, tenant_id: str | None) -> dict | None:
    normalized_tenant_id = (tenant_id or "").strip()
    if normalized_tenant_id:
        return await users.find_one(
            {"username": username, "tenant_id": normalized_tenant_id}
        )

    matches = await users.find({"username": username}).to_list(length=2)
    if len(matches) > 1:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "TENANT_REQUIRED",
                "message": "Informe o tenant_id para entrar com este usuario.",
            },
        )
    return matches[0] if matches else None


def _generate_client_id() -> str:
    return f"cli_{secrets.token_hex(12)}"


def _generate_secret_id() -> str:
    return secrets.token_urlsafe(32)


def _hash_consumer_secret(secret_value: str, salt_hex: str) -> str:
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        secret_value.encode("utf-8"),
        bytes.fromhex(salt_hex),
        200000,
    )
    return digest.hex()


def _verify_consumer_secret(secret_value: str, salt_hex: str, secret_hash: str) -> bool:
    computed = _hash_consumer_secret(secret_value, salt_hex)
    return hmac.compare_digest(computed, secret_hash)


def _build_issuer(request: Request, realm: str) -> str:
    host = request.headers.get("host") or "localhost"
    forwarded_proto = request.headers.get("x-forwarded-proto")
    scheme = forwarded_proto or request.url.scheme or "http"
    return f"{scheme}://{host}/auth/realms/{realm}"


async def _build_portal_token(
    username: str,
    tenant_id: str,
    roles: list[str],
    expires_in_seconds: int | None = None,
) -> PortalAuthResponse:
    effective_ttl = expires_in_seconds or settings.portal_session_ttl_seconds
    try:
        session_id = await portal_session.reserve_session(
            tenant_id,
            username,
            effective_ttl,
        )
    except portal_session.PortalSessionAlreadyActive as exc:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "SESSION_ALREADY_ACTIVE",
                "message": "Este usuario ja possui uma sessao ativa.",
            },
        ) from exc
    except portal_session.PortalSessionUnavailable as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "SESSION_STORE_UNAVAILABLE",
                "message": "Nao foi possivel validar a sessao. Tente novamente.",
            },
        ) from exc

    expires_at = datetime.now(tz=timezone.utc) + timedelta(seconds=effective_ttl)
    claims = {
        "sub": username,
        "tenant_id": tenant_id,
        "roles": roles,
        "sid": session_id,
        "exp": expires_at,
        "aud": ["fluxium-plataform", "fluxium-gateway", "gateway-api"],
    }
    token = jwt.encode(claims, SECRET, algorithm="HS256")
    return PortalAuthResponse(
        access_token=token,
        expires_in_seconds=effective_ttl,
        user={"username": username, "tenant_id": tenant_id, "roles": roles},
    )


def _normalized_roles(raw_roles: list[str] | None) -> set[str]:
    return {
        str(role).strip().lower() for role in (raw_roles or []) if str(role).strip()
    }


def _is_platform_admin(raw_roles: list[str] | None) -> bool:
    return ROLE_PLATFORM_ADMIN in _normalized_roles(raw_roles)


def _is_product_owner(raw_roles: list[str] | None) -> bool:
    return bool(_normalized_roles(raw_roles).intersection({"product_owner", "product-owner", "owner"}))


def _is_trial_user(raw_roles: list[str] | None) -> bool:
    return bool(_normalized_roles(raw_roles).intersection(TRIAL_ROLE_ALIASES))


def _slug_text(value: str, fallback: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or fallback


def _build_tenant_id(empresa_name: str) -> str:
    empresa_slug = _slug_text(empresa_name, "empresa")
    return f"{empresa_slug}-{secrets.token_hex(3)}"


def _normalize_empresa_name(empresa_name: str) -> str:
    decomposed = unicodedata.normalize("NFKD", empresa_name)
    without_accents = "".join(
        char for char in decomposed if not unicodedata.combining(char)
    )
    return " ".join(without_accents.casefold().split())


def _build_checkout_url(plan: str, tenant_id: str, username: str) -> str:
    if plan == "enterprise":
        return ""
    return (
        f"/app/checkout?plan={plan}&tenant_id={tenant_id}&user={username}&provider=mock"
    )


def _build_trial_expired_checkout_url(tenant_id: str, username: str) -> str:
    return (
        f"/app/checkout?plan=basic&tenant_id={tenant_id}&user={username}"
        "&provider=mock&origin=trial_expired"
    )


def _build_trial_expired_detail(tenant_id: str, username: str) -> dict[str, str]:
    return {
        "code": "TRIAL_EXPIRED",
        "message": "Seu periodo trial de 14 dias acabou. Escolha um plano para continuar usando.",
        "checkout_url": _build_trial_expired_checkout_url(tenant_id, username),
    }


def _plan_price(plan: str) -> float:
    return float(getattr(settings, f"billing_plan_price_{plan}", 0.0))


async def _get_paid_plan_checkout_url(tenant_id: str) -> str | None:
    if settings.billing_provider != "asaas":
        return None

    empresa = await db_core.empresas.find_one({"tenant_id": tenant_id})
    if not empresa:
        log_json("WARNING", "asaas_checkout_tenant_not_found", tenant_id=tenant_id)
        return None

    billing = dict(empresa.get("billing") or {})
    if str(billing.get("status") or "").lower() in {"active", "paid"}:
        return None

    checkout_url = billing.get("checkout_url")
    if billing.get("checkout_status") == "pending" and isinstance(checkout_url, str):
        return checkout_url

    plan = str(empresa.get("plan") or "starter").lower()
    if _plan_price(plan) <= 0:
        return None

    try:
        checkout = await asaas_billing_service.upsert_subscription_for_plan(empresa, plan)
    except Exception as exc:
        # Billing provider outage/misconfiguration must never block login.
        log_json(
            "ERROR",
            "asaas_checkout_creation_failed",
            tenant_id=tenant_id,
            plan=plan,
            error=str(exc),
        )
        return None

    billing.update(checkout)
    billing["status"] = "trialing"
    await db_core.empresas.update_many(
        {"tenant_id": tenant_id},
        {"$set": {"billing": billing, "updated_at": datetime.now(tz=timezone.utc)}},
    )
    return str(checkout["checkout_url"])


def _is_free_trial_expired(empresa: dict, now: datetime) -> bool:
    plan = str(empresa.get("plan") or "").strip().lower()
    if plan not in {"free", "starter"}:
        return False
    billing = empresa.get("billing") or {}
    billing_status = str(billing.get("status") or "").strip().lower()
    if billing_status != "trialing":
        return False
    trial_ends_at = _as_utc_datetime(billing.get("trial_ends_at"))
    if not trial_ends_at:
        return False
    return trial_ends_at < now


async def _deactivate_expired_trial_access(
    username: str, tenant_id: str, empresa: dict
) -> None:
    now = datetime.now(tz=timezone.utc)
    billing = dict(empresa.get("billing") or {})
    billing["status"] = "trial_expired"
    billing["updated_at"] = now

    await db_core.empresas.update_many(
        {"tenant_id": tenant_id},
        {"$set": {"billing": billing, "updated_at": now}},
    )


async def _resolve_trial_expired_login_error(
    username: str, tenant_id: str
) -> dict[str, str] | None:
    empresa = await db_core.empresas.find_one({"tenant_id": tenant_id})
    if not empresa:
        return None

    now = datetime.now(tz=timezone.utc)
    if _is_free_trial_expired(empresa, now):
        await _deactivate_expired_trial_access(username, tenant_id, empresa)
        detail = _build_trial_expired_detail(tenant_id, username)
        checkout_url = await _get_paid_plan_checkout_url(tenant_id)
        if checkout_url:
            detail["checkout_url"] = checkout_url
        return detail

    billing = empresa.get("billing") or {}
    if str(billing.get("status") or "").strip().lower() == "trial_expired":
        detail = _build_trial_expired_detail(tenant_id, username)
        checkout_url = await _get_paid_plan_checkout_url(tenant_id)
        if checkout_url:
            detail["checkout_url"] = checkout_url
        return detail

    return None


def _ensure_tenant_operation_allowed(current: dict, tenant_id: str) -> None:
    try:
        resolve_tenant_id(
            current,
            requested_tenant_id=tenant_id,
            allow_admin_override=True,
        )
    except TenantValidationError as exc:
        raise HTTPException(status_code=403, detail="Not allowed") from exc


@router.post(
    "/register", response_model=PortalAuthResponse | PortalPendingVerificationResponse
)
async def portal_register(payload: PortalRegisterRequest):
    users = db_core.portal_users
    empresas = db_core.empresas
    username = payload.username.strip().lower()
    empresa_name = payload.empresa_name.strip()
    if not empresa_name:
        raise HTTPException(status_code=422, detail="empresa_name is required")

    plan = str(payload.plan or "starter").strip().lower()
    if plan not in PLAN_LIMITS:
        raise HTTPException(status_code=400, detail="Invalid plan")

    tenant_id = (payload.tenant_id or "").strip() or _build_tenant_id(empresa_name)
    empresa_name_normalized = _normalize_empresa_name(empresa_name)
    email = (payload.email or "").strip().lower()

    if email:
        pending_user = await users.find_one(
            {
                "username": username,
                "email": email,
                "status": "pending_email_verification",
            }
        )
        if pending_user:
            await _resend_pending_confirmation(pending_user)
            return PortalPendingVerificationResponse(
                status="pending_email_verification",
                message="Cadastro pendente. Um novo e-mail de confirmacao foi enviado.",
                tenant_id=str(pending_user.get("tenant_id") or tenant_id),
            )

    exists = await users.find_one({"username": username, "tenant_id": tenant_id})
    if exists:
        existing_email = str(exists.get("email") or "").strip().lower()
        if (
            exists.get("status") == "pending_email_verification"
            and email
            and existing_email == email
        ):
            await _resend_pending_confirmation(exists)
            return PortalPendingVerificationResponse(
                status="pending_email_verification",
                message="Cadastro pendente. Um novo e-mail de confirmacao foi enviado.",
                tenant_id=tenant_id,
            )
        raise HTTPException(status_code=409, detail="Username already exists")

    existing_empresa = await empresas.find_one({"tenant_id": tenant_id})
    if existing_empresa:
        raise HTTPException(status_code=409, detail="Tenant already exists")

    duplicate_empresa = await empresas.find_one(
        {"name_normalized": empresa_name_normalized}
    )
    if not duplicate_empresa:
        duplicate_empresa = await empresas.find_one(
            {
                "name": {
                    "$regex": f"^{re.escape(empresa_name)}$",
                    "$options": "i",
                }
            }
        )
    if duplicate_empresa:
        raise HTTPException(
            status_code=409,
            detail="Empresa ja cadastrada. Use o tenant_id recebido no e-mail para entrar.",
        )

    salt_hex = secrets.token_hex(16)
    password_hash = _hash_password(payload.password, salt_hex)
    roles = ["product_owner", "operator"]

    now = datetime.now(tz=timezone.utc)
    confirmation_required = _email_confirmation_required()
    user_status = "pending_email_verification" if confirmation_required else "active"

    user_doc = {
        "username": username,
        "tenant_id": tenant_id,
        "full_name": payload.full_name,
        "email": email,
        "password_salt": salt_hex,
        "password_hash": password_hash,
        "roles": roles,
        "status": user_status,
        "created_at": now,
        "updated_at": now,
        "email_verified_at": now if user_status == "active" else None,
    }

    if confirmation_required and not email:
        raise HTTPException(
            status_code=422,
            detail="email is required when email confirmation is enabled",
        )

    empresa_doc = {
        "tenant_id": tenant_id,
        "empresa_id": tenant_id,
        "name": empresa_name,
        "name_normalized": empresa_name_normalized,
        "domain": (payload.domain or "").strip() or None,
        "plan": plan,
        "limits": PLAN_LIMITS[plan],
        "settings": {
            "billing_contact_email": email,
            "billing_contact_cpf_cnpj": payload.cpf_cnpj,
        },
        "status": "ACTIVE",
        "created_at": now,
    }

    empresa_doc["billing"] = await tenant_saas_service.build_initial_billing(empresa_doc, plan)

    insert_result = await users.insert_one(user_doc)
    try:
        await empresas.insert_one(empresa_doc)
    except Exception:
        await users.delete_one({"username": username})
        raise

    await audit_service.record_event(
        event_type="user.registered_pending" if confirmation_required else "user.created",
        tenant_id=tenant_id,
        actor=AuditActor(type="anonymous", id=username),
        resource=AuditResource(type="user", id=username),
        action_result="success",
        source="admin.auth.register",
        metadata={"email_confirmation_required": confirmation_required},
    )

    if confirmation_required:
        try:
            await _issue_and_send_confirmation_email(
                user_id=insert_result.inserted_id,
                email=email,
                username=username,
                tenant_id=tenant_id,
            )
            log_json(
                "INFO",
                "email_confirmation_sent",
                username=username,
                tenant_id=tenant_id,
            )
        except Exception as exc:
            log_json(
                "ERROR",
                "email_confirmation_send_failed",
                username=username,
                tenant_id=tenant_id,
                error=str(exc),
            )
            raise HTTPException(
                status_code=503,
                detail={
                    "code": "EMAIL_CONFIRMATION_SEND_FAILED",
                    "message": "Cadastro criado, mas nao foi possivel enviar o e-mail de confirmacao. Tente novamente.",
                },
            ) from exc

        return PortalPendingVerificationResponse(
            status="pending_email_verification",
            message="Cadastro realizado. Verifique seu e-mail para ativar a conta.",
            tenant_id=tenant_id,
        )

    return await _build_portal_token(username, tenant_id, roles)


@router.post("/confirm-email", response_model=PortalConfirmEmailResponse)
async def confirm_portal_email(payload: PortalConfirmEmailRequest):
    now = datetime.now(tz=timezone.utc)
    tokens = db_core.portal_email_verification_tokens
    users = db_core.portal_users

    token_hash = _token_hash(payload.token)
    doc = await tokens.find_one({"token_hash": token_hash, "invalidated_at": None})

    if not doc:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "TOKEN_INVALID",
                "message": "Token de confirmacao invalido.",
            },
        )

    if doc.get("used_at"):
        raise HTTPException(
            status_code=400,
            detail={
                "code": "TOKEN_ALREADY_USED",
                "message": "Token de confirmacao ja utilizado.",
            },
        )

    expires_at = _as_utc_datetime(doc.get("expires_at"))
    if not expires_at or expires_at < now:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "TOKEN_EXPIRED",
                "message": "Token de confirmacao expirado.",
            },
        )

    user_id = doc.get("user_id")
    user = await users.find_one({"_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await users.update_one(
        {"_id": user_id},
        {
            "$set": {
                "status": "active",
                "email_verified_at": now,
                "updated_at": now,
            }
        },
    )
    await tokens.update_one(
        {"_id": doc.get("_id")},
        {"$set": {"used_at": now}},
    )

    await audit_service.record_event(
        event_type="email_confirmation.succeeded",
        tenant_id=str(user.get("tenant_id") or ""),
        actor=AuditActor(type="user", id=str(user.get("username") or "")),
        resource=AuditResource(type="user", id=str(user.get("username") or "")),
        action_result="success",
        source="admin.auth.confirm_email",
    )

    log_json(
        "INFO",
        "email_confirmation_succeeded",
        username=user.get("username"),
        tenant_id=user.get("tenant_id"),
    )

    return PortalConfirmEmailResponse(
        status="active",
        message="E-mail confirmado com sucesso. Acesso liberado.",
    )


@router.post("/resend-confirmation", response_model=PortalResendConfirmationResponse)
async def resend_portal_confirmation(payload: PortalResendConfirmationRequest):
    generic_response = PortalResendConfirmationResponse(
        message="Se o cadastro existir e estiver pendente, um novo e-mail foi enviado."
    )

    email = payload.email.strip().lower()
    if not email:
        return generic_response

    users = db_core.portal_users
    user = await users.find_one({"email": email})

    if not user or user.get("status") == "active":
        return generic_response

    try:
        await _resend_pending_confirmation(user)
        log_json(
            "INFO",
            "email_confirmation_resent",
            username=user.get("username"),
            tenant_id=user.get("tenant_id"),
            email=email,
        )
    except HTTPException:
        raise

    return generic_response


@router.get("/users/me", response_model=PortalUserResponse)
async def get_current_portal_user(user=Depends(get_current_user)):
    """Return current portal user info from token or DB."""
    username = user.get("sub") or user.get("username")
    if not username:
        raise HTTPException(status_code=401, detail="Invalid token: no subject")

    tenant_id = str(user.get("tenant_id") or "").strip()
    user_query = {"username": username}
    if tenant_id:
        user_query["tenant_id"] = tenant_id
    doc = await db_core.portal_users.find_one(user_query)
    if doc:
        return PortalUserResponse(
            username=doc.get("username"),
            tenant_id=doc.get("tenant_id") or "",
            full_name=doc.get("full_name"),
            email=doc.get("email"),
            roles=doc.get("roles") or [],
            status=doc.get("status"),
        )

    # fallback to token claims
    return PortalUserResponse(
        username=username,
        tenant_id=user.get("tenant_id") or "",
        full_name=user.get("name") or user.get("preferred_username"),
        email=user.get("email"),
        roles=user.get("roles") or [],
        status=None,
    )


@router.get("/users/{tenant_id}", response_model=list[PortalUserResponse])
async def list_portal_users(tenant_id: str, current=Depends(get_current_user)):
    roles = current.get("roles") or []
    caller_tenant_id = str(current.get("tenant_id") or "").strip()

    users = db_core.portal_users

    if _is_platform_admin(roles):
        docs = await users.find({"tenant_id": tenant_id}).to_list(length=1000)
        return [
            PortalUserResponse(
                username=doc.get("username"),
                tenant_id=doc.get("tenant_id") or "",
                full_name=doc.get("full_name"),
                email=doc.get("email"),
                roles=doc.get("roles") or [],
                status=doc.get("status"),
            )
            for doc in docs
        ]

    if _is_product_owner(roles):
        if not caller_tenant_id or caller_tenant_id != tenant_id:
            raise HTTPException(status_code=403, detail="Not allowed")
        docs = await users.find({"tenant_id": tenant_id}).to_list(length=1000)
        return [
            PortalUserResponse(
                username=doc.get("username"),
                tenant_id=doc.get("tenant_id") or "",
                full_name=doc.get("full_name"),
                email=doc.get("email"),
                roles=doc.get("roles") or [],
                status=doc.get("status"),
            )
            for doc in docs
        ]

    if _is_trial_user(roles):
        subject = str(current.get("sub") or current.get("username") or "").strip().lower()
        if not subject:
            raise HTTPException(status_code=401, detail="Invalid token: no subject")
        if caller_tenant_id and caller_tenant_id != tenant_id:
            raise HTTPException(status_code=403, detail="Not allowed")

        doc = await users.find_one({"username": subject, "tenant_id": tenant_id})
        if not doc:
            return []
        return [
            PortalUserResponse(
                username=doc.get("username"),
                tenant_id=doc.get("tenant_id") or "",
                full_name=doc.get("full_name"),
                email=doc.get("email"),
                roles=doc.get("roles") or [],
                status=doc.get("status"),
            )
        ]

    raise HTTPException(status_code=403, detail="Not allowed")


@router.put("/users/{username}/tenant")
async def update_portal_user_tenant(
    username: str, payload: UpdateTenantRequest, current=Depends(get_current_user)
):
    _ = (username, payload, current)
    raise HTTPException(
        status_code=410,
        detail="Tenant update is disabled. tenant_id is inherited from empresa/session context.",
    )


@router.post("/users", response_model=PortalUserResponse)
async def create_portal_user(
    payload: CreatePortalUserRequest, current=Depends(get_current_user)
):
    roles = current.get("roles") or []
    is_platform_admin = _is_platform_admin(roles)
    is_product_owner = _is_product_owner(roles)
    if not is_platform_admin and not is_product_owner:
        raise HTTPException(status_code=403, detail="Not allowed")

    username = payload.username.strip().lower()
    tenant_id = str(current.get("tenant_id") or "").strip()
    if not tenant_id:
        raise HTTPException(status_code=422, detail="Current session has no tenant_id")

    users = db_core.portal_users
    empresas = db_core.empresas

    exists = await users.find_one({"username": username, "tenant_id": tenant_id})
    if exists:
        raise HTTPException(status_code=409, detail="Username already exists")

    tenant_exists = await empresas.find_one({"tenant_id": tenant_id})
    if not tenant_exists:
        raise HTTPException(status_code=404, detail="Tenant not found")

    now = datetime.now(tz=timezone.utc)
    salt_hex = secrets.token_hex(16)
    password_hash = _hash_password(payload.password, salt_hex)
    normalized_roles = [
        r.strip().lower() for r in (payload.roles or []) if r and r.strip()
    ]
    if is_product_owner and set(normalized_roles) != {"operator"}:
        raise HTTPException(
            status_code=403,
            detail="Product owners can only create operator users",
        )

    user_doc = {
        "username": username,
        "tenant_id": tenant_id,
        "full_name": (payload.full_name or "").strip() or None,
        "email": (payload.email or "").strip().lower() or None,
        "password_salt": salt_hex,
        "password_hash": password_hash,
        "roles": normalized_roles or ["platform_trial"],
        "status": "active",
        "created_at": now,
        "updated_at": now,
        "email_verified_at": now,
    }

    await users.insert_one(user_doc)

    return PortalUserResponse(
        username=user_doc["username"],
        tenant_id=user_doc["tenant_id"],
        full_name=user_doc.get("full_name"),
        email=user_doc.get("email"),
        roles=user_doc.get("roles") or [],
        status=user_doc.get("status"),
    )


@router.post("/users/{username}/change-password")
async def change_portal_password(
    username: str, payload: ChangePasswordRequest, current=Depends(get_current_user)
):
    """Change password for a portal user. Allowed for self or platform_admin role."""
    # allow if current subject equals username or current has platform_admin role
    subject = current.get("sub") or current.get("username")
    username = username.strip().lower()
    roles = current.get("roles") or []
    if subject != username and not _is_platform_admin(roles):
        raise HTTPException(
            status_code=403, detail="Not allowed to change this password"
        )

    users = db_core.portal_users
    user = await _find_login_user(users, username, current.get("tenant_id"))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user_query = {
        "username": username,
        "tenant_id": str(user.get("tenant_id") or ""),
    }

    salt_hex = secrets.token_hex(16)
    password_hash = _hash_password(payload.password, salt_hex)

    await users.update_one(
        user_query,
        {"$set": {"password_salt": salt_hex, "password_hash": password_hash}},
    )
    return {"success": True}


@router.put("/users/{username}/roles")
async def update_portal_roles(
    username: str, payload: UpdateRolesRequest, current=Depends(get_current_user)
):
    """Update roles for a portal user. Requires platform_admin role."""
    roles = current.get("roles") or []
    if not _is_platform_admin(roles):
        raise HTTPException(status_code=403, detail="Not allowed")

    users = db_core.portal_users
    user = await users.find_one({"username": username})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await users.update_one({"username": username}, {"$set": {"roles": payload.roles}})
    return {"success": True}


@router.post("/login", response_model=PortalAuthResponse)
async def portal_login(payload: PortalLoginRequest):
    users = db_core.portal_users
    username = payload.username.strip().lower()
    user = await _find_login_user(users, username, payload.tenant_id)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    status = str(user.get("status") or "").strip().lower()
    if status != "active":
        if status == "pending_email_verification":
            await audit_service.record_event(
                event_type="login.blocked_unverified",
                tenant_id=str(user.get("tenant_id") or ""),
                actor=AuditActor(type="anonymous"),
                resource=AuditResource(type="user", id=username),
                action_result="denied",
                source="admin.auth.login",
            )
            raise HTTPException(
                status_code=403,
                detail={
                    "code": "EMAIL_NOT_CONFIRMED",
                    "message": "Confirme seu e-mail para acessar o sistema.",
                },
            )
        tenant_id_for_inactive = str(user.get("tenant_id") or "").strip()
        if tenant_id_for_inactive:
            trial_error = await _resolve_trial_expired_login_error(
                username=username,
                tenant_id=tenant_id_for_inactive,
            )
            if trial_error:
                raise HTTPException(status_code=402, detail=trial_error)
        raise HTTPException(status_code=403, detail="User is inactive")

    if not _verify_password(
        payload.password, user.get("password_salt", ""), user.get("password_hash", "")
    ):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    roles = user.get("roles") or ["platform_admin"]
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=422, detail="User has no tenant_id configured")

    trial_error = await _resolve_trial_expired_login_error(
        username=username,
        tenant_id=tenant_id,
    )
    if trial_error:
        raise HTTPException(status_code=402, detail=trial_error)

    return await _build_portal_token(username, tenant_id, roles)


@router.post("/logout")
async def portal_logout(current=Depends(get_current_user)):
    username = str(current.get("sub") or "").strip().lower()
    tenant_id = str(current.get("tenant_id") or "").strip()
    session_id = str(current.get("sid") or "").strip()
    if not username or not tenant_id or not session_id:
        return {"success": True}

    try:
        await portal_session.release_session(tenant_id, username, session_id)
    except portal_session.PortalSessionUnavailable as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "SESSION_STORE_UNAVAILABLE",
                "message": "Nao foi possivel encerrar a sessao. Tente novamente.",
            },
        ) from exc
    return {"success": True}


@router.post(
    "/consumers/{tenant_id}/{consumer_id}/credentials/generate",
    response_model=ConsumerCredentialsGenerateResponse,
)
async def generate_consumer_credentials(
    tenant_id: str,
    consumer_id: str,
    payload: ConsumerCredentialsGenerateRequest,
    user=Depends(get_current_user),
):
    _ensure_tenant_operation_allowed(user, tenant_id)

    consumer = await db.consumers.find_one({"_id": consumer_id, "tenant_id": tenant_id})
    if not consumer:
        raise HTTPException(status_code=404, detail="Consumer not found")

    current_client_id = consumer.get("client_id")
    should_regenerate_client_id = bool(
        payload.regenerate_client_id or not current_client_id
    )

    next_client_id = (
        _generate_client_id() if should_regenerate_client_id else current_client_id
    )
    current_secret_id = consumer.get("secret_id")
    next_secret_id = (
        _generate_secret_id() if payload.regenerate_secret else current_secret_id
    )

    if not next_secret_id:
        next_secret_id = _generate_secret_id()

    secret_salt = secrets.token_hex(16)
    secret_hash = _hash_consumer_secret(next_secret_id, secret_salt)

    generated_at = datetime.now(tz=timezone.utc)

    await db.consumers.update_one(
        {"_id": consumer_id, "tenant_id": tenant_id},
        {
            "$set": {
                "client_id": next_client_id,
                "secret_salt": secret_salt,
                "secret_hash": secret_hash,
                "credentials_updated_at": generated_at,
            },
            "$unset": {"secret_id": ""},
        },
    )

    return ConsumerCredentialsGenerateResponse(
        consumer_id=consumer_id,
        tenant_id=tenant_id,
        client_id=next_client_id,
        secret_id=next_secret_id,
        secret_generated_at=generated_at.isoformat(),
    )


@router.post(
    "/consumers/{tenant_id}/{consumer_id}/token/generate",
    response_model=ConsumerTokenGenerateResponse,
)
async def generate_consumer_token(
    tenant_id: str,
    consumer_id: str,
    payload: ConsumerTokenGenerateRequest,
    user=Depends(get_current_user),
):
    _ensure_tenant_operation_allowed(user, tenant_id)

    if payload.expires_in_seconds <= 0:
        raise HTTPException(
            status_code=400, detail="expires_in_seconds must be greater than 0"
        )

    consumer = await db.consumers.find_one({"_id": consumer_id, "tenant_id": tenant_id})
    if not consumer:
        raise HTTPException(status_code=404, detail="Consumer not found")

    environment = consumer.get("environment")
    has_active_credentials = bool(
        consumer.get("client_id")
        and (
            (consumer.get("secret_hash") and consumer.get("secret_salt"))
            or consumer.get("secret_id")
        )
    )
    if consumer.get("status") == "inactive":
        raise HTTPException(status_code=403, detail="consumer_inactive")
    if not has_active_credentials:
        raise HTTPException(status_code=403, detail="consumer_credentials_not_configured")
    if environment not in {"staging", "production"}:
        raise HTTPException(status_code=409, detail="consumer_environment_not_configured")

    expires_at = datetime.now(tz=timezone.utc) + timedelta(
        seconds=payload.expires_in_seconds
    )
    claims = {
        "sub": consumer_id,
        "consumer_id": consumer_id,
        "tenant_id": tenant_id,
        "client_id": consumer.get("client_id"),
        "consumer_name": consumer.get("name"),
        "actor_type": consumer.get("actor_type"),
        "status": consumer.get("status"),
        "tags": consumer.get("tags") or [],
        "plan_override": consumer.get("plan_override"),
        "environment": environment,
        "aud": [consumer_audience(environment)],
        "scope": DEFAULT_CONSUMER_SCOPE,
        "exp": expires_at,
    }

    if payload.include_permissions:
        permissions = []
        async for permission in db.consumer_permissions.find(
            {
                "tenant_id": tenant_id,
                "consumer_id": consumer_id,
                "status": {"$ne": "inactive"},
            }
        ):
            permissions.append(
                {
                    "api_id": permission.get("api_id"),
                    "route_id": permission.get("route_id"),
                    "methods": permission.get("methods") or ["*"],
                }
            )
        claims["permissions"] = permissions

    if payload.additional_claims:
        protected_claims = {
            "tenant_id",
            "consumer_id",
            "client_id",
            "environment",
            "aud",
            "scope",
            "exp",
        }
        claims.update(
            {
                key: value
                for key, value in payload.additional_claims.items()
                if key not in protected_claims
            }
        )

    token = jwt.encode(claims, SECRET, algorithm="HS256")
    return ConsumerTokenGenerateResponse(
        access_token=token,
        expires_in_seconds=payload.expires_in_seconds,
        claims=claims,
    )


@oidc_router.post("/token")
async def oidc_token_client_credentials(realm: str, request: Request):

    # Accept both application/x-www-form-urlencoded and multipart/form-data
    content_type = request.headers.get("content-type", "")
    if "application/x-www-form-urlencoded" in content_type:
        form = await request.form()
    else:
        raw_body = await request.body()
        form = parse_qs(raw_body.decode("utf-8"), keep_blank_values=True)

    grant_type = form.get("grant_type") or form.get("grant_type", [""])[0]
    if isinstance(grant_type, list):
        grant_type = grant_type[0]
    client_id = form.get("client_id") or form.get("client_id", [""])[0]
    if isinstance(client_id, list):
        client_id = client_id[0]
    client_secret = form.get("client_secret") or form.get("client_secret", [""])[0]
    if isinstance(client_secret, list):
        client_secret = client_secret[0]
    requested_scope = form.get("scope") or form.get("scope", ["openid"])[0]
    if isinstance(requested_scope, list):
        requested_scope = requested_scope[0]
    if not requested_scope:
        requested_scope = "openid"

    if grant_type != "client_credentials":
        raise HTTPException(status_code=400, detail="unsupported_grant_type")

    # allow HTTP Basic auth to supply client_id:client_secret
    if not client_id or not client_secret:
        auth_header = request.headers.get("authorization") or request.headers.get(
            "Authorization"
        )
        if auth_header and auth_header.lower().startswith("basic "):
            try:
                import base64

                b = auth_header.split(None, 1)[1]
                cred = base64.b64decode(b).decode("utf-8")
                parts = cred.split(":", 1)
                if len(parts) == 2:
                    client_id = client_id or parts[0]
                    client_secret = client_secret or parts[1]
            except Exception:
                # ignore and fall back to form values
                pass

    if not client_id or not client_secret:
        raise HTTPException(status_code=401, detail="invalid_client")

    # ensure we always scope lookup by tenant (realm)
    consumer = await db.consumers.find_one(
        {
            "tenant_id": realm,
            "client_id": client_id,
            "status": {"$ne": "inactive"},
        }
    )

    if not consumer:
        raise HTTPException(status_code=401, detail="invalid_client")

    environment = consumer.get("environment")
    if environment not in {"staging", "production"}:
        raise HTTPException(status_code=403, detail="consumer_environment_not_configured")

    stored_secret_hash = consumer.get("secret_hash")
    stored_secret_salt = consumer.get("secret_salt")
    if stored_secret_hash and stored_secret_salt:
        is_valid_secret = _verify_consumer_secret(
            client_secret, stored_secret_salt, stored_secret_hash
        )
    else:
        # Backward compatibility for legacy records that still have secret_id in clear text.
        is_valid_secret = hmac.compare_digest(
            str(consumer.get("secret_id") or ""), client_secret
        )

    if not is_valid_secret:
        raise HTTPException(status_code=401, detail="invalid_client")

    tenant_id = consumer.get("tenant_id")
    consumer_id = consumer.get("_id")
    if not tenant_id or not consumer_id:
        raise HTTPException(status_code=422, detail="consumer_missing_tenant_or_id")

    permissions = []
    async for permission in db.consumer_permissions.find(
        {
            "tenant_id": tenant_id,
            "consumer_id": consumer_id,
            "status": {"$ne": "inactive"},
        }
    ):
        permissions.append(
            {
                "api_id": permission.get("api_id"),
                "route_id": permission.get("route_id"),
                "methods": permission.get("methods") or ["*"],
            }
        )

    issuer = _build_issuer(request, realm)
    now = int(datetime.now(tz=timezone.utc).timestamp())
    expires_in = 7200
    exp = now + expires_in
    jti = str(uuid.uuid4())
    tags = consumer.get("tags") or []
    actor_type = consumer.get("actor_type") or "application"

    scope_parts = [item for item in requested_scope.split(" ") if item]
    scope_parts.append(DEFAULT_CONSUMER_SCOPE)
    if "openid" not in scope_parts:
        scope_parts.insert(0, "openid")
    if tags:
        scope_parts.append("tags")
    scope = " ".join(dict.fromkeys(scope_parts))

    base_claims = {
        "exp": exp,
        "iat": now,
        "jti": jti,
        "iss": issuer,
        "aud": [
            consumer_audience(environment),
            client_id,
            "fluxium-plataform",
            "fluxium-gateway",
            "gateway-api",
        ],
        "sub": consumer_id,
        "typ": "Bearer",
        "azp": client_id,
        "scope": scope,
        "tenant_id": tenant_id,
        "consumer_id": consumer_id,
        "consumer_name": consumer.get("name"),
        "actor_type": actor_type,
        "tags": tags,
        "plan_override": consumer.get("plan_override"),
        "permissions": permissions,
        "preferred_username": f"service-account-{client_id}",
        "clientId": client_id,
        "roles": [actor_type],
        "groups": tags,
        "environment": environment,
    }

    access_token = jwt.encode(base_claims, SECRET, algorithm="HS256")

    id_token_claims = {
        **base_claims,
        "typ": "ID",
        "aud": [client_id, "fluxium-gateway"],
    }
    id_token = jwt.encode(id_token_claims, SECRET, algorithm="HS256")

    return {
        "access_token": access_token,
        "expires_in": expires_in,
        "refresh_expires_in": 0,
        "token_type": "Bearer",
        "id_token": id_token,
        "not-before-policy": 0,
        "scope": scope,
    }
