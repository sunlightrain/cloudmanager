from fastapi import FastAPI
from app.core.database import init_db
from app.api.routes import auth, vms, tasks, hosts, logs, settings
from app.api.routes import snapshots, clone, batch, infrastructure, users, inventory

app = FastAPI(
    title="VMware Cloud Manager",
    description="Cloud Management Platform for VMware vSphere",
    version="0.4.0"
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
app.include_router(inventory.router, prefix="/api")


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/")
def root():
    return {"message": "VMware Cloud Manager API", "version": "0.2.0"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
