from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config.settings import get_settings
from .shared.errors import register_exception_handlers
from .shared.observability.request_context import request_context_middleware
from .shared.auth.identity_router import (
    oidc_discovery_router,
    oidc_router,
    router as identity_router,
)
from .features.products.router import router as products_router
from .features.opportunities.router import router as opportunities_router
from .features.okrs.router import router as okrs_router
from .features.discovery.router import router as discovery_router
from .features.business_problems.router import router as business_problems_router
from .features.evidence.router import router as evidence_router
from .features.hypotheses.router import router as hypotheses_router
from .features.initiatives.router import router as initiatives_router
from .features.business_plans.router import router as business_plans_router
from .features.readiness.router import router as readiness_router
from .features.proposals.router import router as proposals_router
from .features.workspaces.router import router as workspaces_router
from .shared.audit.router import router as audit_router


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(title=settings.app_name, version="0.1.0")
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[
            origin.strip()
            for origin in settings.cors_allowed_origins.split(",")
            if origin.strip()
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.middleware("http")(request_context_middleware)
    register_exception_handlers(application)
    application.include_router(identity_router, prefix=settings.api_prefix)
    application.include_router(oidc_router, prefix=settings.api_prefix)
    application.include_router(oidc_discovery_router, prefix=settings.api_prefix)
    application.include_router(products_router, prefix=settings.api_prefix)
    application.include_router(opportunities_router, prefix=settings.api_prefix)
    application.include_router(okrs_router, prefix=settings.api_prefix)
    application.include_router(discovery_router, prefix=settings.api_prefix)
    application.include_router(business_problems_router, prefix=settings.api_prefix)
    application.include_router(evidence_router, prefix=settings.api_prefix)
    application.include_router(hypotheses_router, prefix=settings.api_prefix)
    application.include_router(initiatives_router, prefix=settings.api_prefix)
    application.include_router(business_plans_router, prefix=settings.api_prefix)
    application.include_router(readiness_router, prefix=settings.api_prefix)
    application.include_router(proposals_router, prefix=settings.api_prefix)
    application.include_router(workspaces_router, prefix=settings.api_prefix)
    application.include_router(audit_router, prefix=settings.api_prefix)

    @application.get(f"{settings.api_prefix}/health", tags=["health"])
    async def health() -> dict[str, str]:
        return {"status": "ok", "environment": settings.environment}

    return application


app = create_app()
