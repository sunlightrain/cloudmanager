from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field
import json


class Datacenter(SQLModel, table=True):
    __tablename__ = "datacenters"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    vc_guid: str = Field(unique=True, index=True)
    name: str
    raw_data: Optional[str] = Field(default=None)
    last_sync: datetime = Field(default_factory=datetime.utcnow)
    
    @property
    def raw_data_dict(self) -> dict:
        if self.raw_data:
            return json.loads(self.raw_data)
        return {}
