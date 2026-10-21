"""
FastAPI application factory with routers, middleware, and lifecycle management.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi

from app.core.config import get_config
from app.core.errors import ErrorHandlingMiddleware
from app.routers import scan, repair, patch, verification, report


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    config = get_config()
    
    app = FastAPI(
        title="AccessLens API",
        description="AI-powered website accessibility detection and repair platform",
        version="1.0.0",
        debug=config.DEBUG,
    )
    
    # Add middleware stack (order matters)
    # ErrorHandling must be first to catch all exceptions
    app.add_middleware(ErrorHandlingMiddleware)
    
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-Request-ID"],
    )
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint for load balancers and orchestration."""
        return JSONResponse(
            status_code=200,
            content={
                "status": "healthy",
                "environment": config.ENVIRONMENT,
                "version": "1.0.0",
            }
        )
    
    # API Info endpoint
    @app.get("/api/info")
    async def api_info():
        """API information and metadata."""
        return JSONResponse(
            status_code=200,
            content={
                "name": "AccessLens API",
                "version": "1.0.0",
                "environment": config.ENVIRONMENT,
                "endpoints": [
                    "/health",
                    "/api/info",
                    "/api/scan",
                    "/api/repair/generate",
                    "/api/repair/approve",
                    "/api/patch/apply",
                    "/api/verification/{scan_id}",
                ]
            }
        )
    
    # Register routers
    app.include_router(
        scan.router,
        prefix="/api",
        tags=["scanning"],
    )
    app.include_router(
        repair.router,
        prefix="/api",
        tags=["repairs"],
    )
    app.include_router(
        patch.router,
        prefix="/api",
        tags=["patches"],
    )
    app.include_router(
        verification.router,
        prefix="/api",
        tags=["verification"],
    )
    app.include_router(
        report.router,
        prefix="/api",
        tags=["reports"],
    )
    
    # Custom OpenAPI schema (optional)
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        openapi_schema = get_openapi(
            title="AccessLens API",
            version="1.0.0",
            routes=app.routes,
        )
        openapi_schema["info"]["description"] = "AI-powered website accessibility detection and repair platform"
        app.openapi_schema = openapi_schema
        return app.openapi_schema
    
    app.openapi = custom_openapi
    
    return app
# Create FastAPI application instance for module import
app = create_app()

