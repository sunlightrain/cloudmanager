from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field
import json


class Network(SQLModel, table=True):
    __tablename__ = "networks"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    vc_guid: str = Field(unique=True, index=True)
    datacenter_id: int = Field(foreign_key="datacenters.id", index=True)
    name: str
    type: str = "Standard"
    vlan_id: Optional[int] = None
    raw_data: Optional[str] = None
    last_sync: datetime = Field(default_factory=datetime.utcnow)
    
    @property
    def raw_data_dict(self) -> dict:
        if self.raw_data:
            return json.loads(self.raw_data)
        return {}


class PortGroup(SQLModel, table=True):
    __tablename__ = "port_groups"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    vc_guid: str = Field(unique=True, index=True)
    network_id: int = Field(foreign_key="networks.id", index=True)
    name: str
    vlan_id: Optional[int] = None
    raw_data: Optional[str] = None
    last_sync: datetime = Field(default_factory=datetime.utcnow)
