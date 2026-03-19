from app.api.routes import auth, vms, tasks, hosts, logs, settings
from app.api.routes import snapshots, clone, batch, infrastructure, users, inventory
from app.api.routes import tenants, approvals, automation, monitoring, backups

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
    "automation",
    "monitoring",
    "backups",
]
