from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field
import json


class Cluster(SQLModel, table=True):
    __tablename__ = "clusters"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    vc_guid: str = Field(unique=True, index=True)
    datacenter_id: int = Field(foreign_key="datacenters.id", index=True)
    name: str
    host_count: int = 0
    total_cpu_cores: int = 0
    total_memory_gb: float = 0
    ha_enabled: bool = False
    drs_enabled: bool = False
    raw_data: Optional[str] = None
    last_sync: datetime = Field(default_factory=datetime.utcnow)
    
    @property
    def raw_data_dict(self) -> dict:
        if self.raw_data:
            return json.loads(self.raw_data)
        return {}
