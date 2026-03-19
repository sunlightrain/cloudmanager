import logging
from fastapi import FastAPI, Request, status, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.core.database import init_db
from app.api.routes import auth, vms, tasks, hosts, logs, settings
from app.api.routes import snapshots, clone, batch, infrastructure, users
from app.api.routes import clusters, datacenters, storage, networks, migration

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="VMware Cloud Manager",
    description="Cloud Management Platform for VMware vSphere",
    version="0.3.0"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


app.include_router(auth.router, prefix="/api")
app.include_router(vms.router, prefix="/api")
app.include_router(tasks.router, prefix="/api")
app.include_router(hosts.router, prefix="/api")
app.include_router(logs.router, prefix="/api")
app.include_router(settings.router, prefix="/api")
app.include_router(snapshots.router, prefix="/api")
app.include_router(clone.router, prefix="/api")
app.include_router(batch.router, prefix="/api")
app.include_router(infrastructure.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(clusters.router, prefix="/api")
app.include_router(datacenters.router, prefix="/api")
app.include_router(storage.router, prefix="/api")
app.include_router(networks.router, prefix="/api")
app.include_router(migration.router, prefix="/api")


@app.on_event("startup")
def on_startup():
    logger.info("Starting VMware Cloud Manager...")
    init_db()
    logger.info("Database initialized")


@app.on_event("shutdown")
def on_shutdown():
    logger.info("Shutting down VMware Cloud Manager...")


@app.get("/")
def root():
    return {"message": "VMware Cloud Manager API", "version": "0.3.0"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
