from app.api.routes import auth, vms, tasks, hosts, logs, settings
from app.api.routes import snapshots, clone, batch, infrastructure, users, inventory
from app.api.routes import tenants, approvals

__all__ = [
    "auth",
    "vms",
    "tasks",
    "hosts",
    "logs",
    "settings",
    "snapshots",
    "clone",
    "batch",
    "infrastructure",
    "users",
    "inventory",
    "tenants",
    "approvals",
]
