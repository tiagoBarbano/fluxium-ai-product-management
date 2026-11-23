import secrets

from redis.exceptions import RedisError

from app.infra.db import redis_client


SESSION_KEY_PREFIX = "admin:portal:active-session"
_RELEASE_SCRIPT = """
if redis.call('get', KEYS[1]) == ARGV[1] then
    return redis.call('del', KEYS[1])
end
return 0
"""


class PortalSessionAlreadyActive(Exception):
    pass


class PortalSessionUnavailable(Exception):
    pass


def session_key(tenant_id: str, username: str) -> str:
    return f"{SESSION_KEY_PREFIX}:{tenant_id.strip()}:{username.strip().lower()}"


async def reserve_session(tenant_id: str, username: str, ttl_seconds: int) -> str:
    session_id = secrets.token_urlsafe(32)
    try:
        reserved = await redis_client.set(
            session_key(tenant_id, username),
            session_id,
            nx=True,
            ex=ttl_seconds,
        )
    except RedisError as exc:
        raise PortalSessionUnavailable from exc

    if not reserved:
        raise PortalSessionAlreadyActive
    return session_id


async def validate_session(tenant_id: str, username: str, session_id: str) -> bool:
    try:
        current_session_id = await redis_client.get(session_key(tenant_id, username))
    except RedisError as exc:
        raise PortalSessionUnavailable from exc
    return current_session_id in {session_id, session_id.encode()}


async def release_session(tenant_id: str, username: str, session_id: str) -> None:
    try:
        await redis_client.eval(
            _RELEASE_SCRIPT,
            1,
            session_key(tenant_id, username),
            session_id,
        )
    except RedisError as exc:
        raise PortalSessionUnavailable from exc