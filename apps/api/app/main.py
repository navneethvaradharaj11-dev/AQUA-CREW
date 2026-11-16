"""
AQUA CREW — Backend API Entry Point
"""
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from contextlib import asynccontextmanager

from app.config import settings
from app.core.logging import logger
from app.core.exceptions import (
    AquaCrewException,
    aqua_crew_exception_handler,
    validation_exception_handler,
    http_exception_handler,
    unhandled_exception_handler,
)
from app.middleware import (
    RequestIDMiddleware,
    SecurityHeadersMiddleware,
    RequestSizeLimitMiddleware,
    RateLimiterMiddleware,
)
from app.api.v1.router import api_v1_router
from app.database.session import init_db
from app.services.simulation_service import simulation_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup lifecycle
    settings.validate_production_security()
    logger.info(f"Starting {settings.API_TITLE} v{settings.API_VERSION} [{settings.API_ENV}]")
    logger.info(f"Allowed CORS Origins: {settings.CORS_ORIGINS}")
    
    # Initialize database tables
    init_db()
    
    # Start background simulation engine
    if settings.SIMULATION_AUTO_START:
        simulation_service.start()

    yield

    # Shutdown lifecycle
    logger.info("Shutting down AQUA CREW API service cleanly.")
    simulation_service.pause()


app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
    openapi_url=f"{settings.API_PREFIX}/openapi.json",
    docs_url=f"{settings.API_PREFIX}/docs",
    redoc_url=f"{settings.API_PREFIX}/redoc",
    lifespan=lifespan,
)

# Production Security and Operational Middlewares
# Execution order: RequestID -> CORS -> RateLimiter -> RequestSizeLimit -> SecurityHeaders -> Endpoint
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestSizeLimitMiddleware)
app.add_middleware(RateLimiterMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestIDMiddleware)

# Centralized Exception Handlers
app.add_exception_handler(AquaCrewException, aqua_crew_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

# Mount API V1 routes
app.include_router(api_v1_router, prefix=settings.API_PREFIX)

from app.api.v1.endpoints.ws import websocket_telemetry_endpoint
from app.api.v1.endpoints.metrics import get_prometheus_metrics
from app.database.session import get_db
from fastapi import Depends

@app.websocket("/ws")
@app.websocket("/ws/telemetry")
async def ws_root(websocket: WebSocket):
    await websocket_telemetry_endpoint(websocket)


@app.get("/metrics", tags=["Observability"])
def root_metrics(db=Depends(get_db)):
    return get_prometheus_metrics(db=db)


@app.get("/", tags=["Root"])
async def root():
    return {
        "name": settings.API_TITLE,
        "version": settings.API_VERSION,
        "status": "online",
        "docs": f"{settings.API_PREFIX}/docs",
        "health": f"{settings.API_PREFIX}/health",
    }

