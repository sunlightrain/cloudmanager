from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field
import json


class Host(SQLModel, table=True):
    __tablename__ = "hosts"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    vc_guid: str = Field(unique=True, index=True)
    cluster_id: int = Field(foreign_key="clusters.id", index=True, nullable=True)
    datacenter_id: int = Field(foreign_key="datacenters.id", index=True)
    name: str
    status: str = "unknown"
    connection_state: str = "disconnected"
    maintenance_mode: bool = False
    cpu_cores: int = 0
    cpu_mhz: int = 0
    cpu_usage_percent: float = 0
    memory_bytes: int = 0
    memory_usage_percent: float = 0
    raw_data: Optional[str] = None
    last_sync: datetime = Field(default_factory=datetime.utcnow)
    
    @property
    def raw_data_dict(self) -> dict:
        if self.raw_data:
            return json.loads(self.raw_data)
        return {}
    
    @property
    def memory_gb(self) -> float:
        return self.memory_bytes / (1024 ** 3)
