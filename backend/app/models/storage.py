from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field
import json


class Datastore(SQLModel, table=True):
    __tablename__ = "datastores"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    vc_guid: str = Field(unique=True, index=True)
    datacenter_id: int = Field(foreign_key="datacenters.id", index=True)
    name: str
    type: str = "unknown"
    capacity_gb: int = 0
    free_gb: int = 0
    used_percent: float = 0
    raw_data: Optional[str] = None
    last_sync: datetime = Field(default_factory=datetime.utcnow)
    
    @property
    def used_gb(self) -> int:
        return self.capacity_gb - self.free_gb
    
    @property
    def raw_data_dict(self) -> dict:
        if self.raw_data:
            return json.loads(self.raw_data)
        return {}
