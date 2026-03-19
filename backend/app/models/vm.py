from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field
import json


class VM(SQLModel, table=True):
    __tablename__ = "vms"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    vc_guid: str = Field(unique=True, index=True)
    name: str
    status: str = "unknown"
    host_id: Optional[int] = Field(foreign_key="hosts.id", index=True, nullable=True)
    datacenter_id: int = Field(foreign_key="datacenters.id", index=True)
    cluster_id: Optional[int] = Field(foreign_key="clusters.id", index=True, nullable=True)
    cpu: int = 0
    memory_mb: int = 0
    disk_gb: Optional[str] = None
    ip_addresses: Optional[str] = None
    mac_addresses: Optional[str] = None
    tools_status: str = "unknown"
    guest_state: str = "unknown"
    guest_full_name: Optional[str] = None
    guest_id: Optional[str] = None
    annotation: Optional[str] = None
    datastore_ids: Optional[str] = None
    created: Optional[datetime] = None
    last_sync: datetime = Field(default_factory=datetime.utcnow)
    
    @property
    def disk_gb_list(self) -> List[int]:
        if self.disk_gb:
            return json.loads(self.disk_gb)
        return []
    
    @property
    def ip_addresses_list(self) -> List[str]:
        if self.ip_addresses:
            return json.loads(self.ip_addresses)
        return []
    
    @property
    def mac_addresses_list(self) -> List[str]:
        if self.mac_addresses:
            return json.loads(self.mac_addresses)
        return []
    
    @property
    def datastore_ids_list(self) -> List[str]:
        if self.datastore_ids:
            return json.loads(self.datastore_ids)
        return []
    
    def to_summary(self) -> dict:
        return {
            "id": self.id,
            "vc_guid": self.vc_guid,
            "name": self.name,
            "status": self.status,
            "cpu": self.cpu,
            "memory_mb": self.memory_mb,
            "ip_addresses": self.ip_addresses_list,
            "host_id": self.host_id,
            "tools_status": self.tools_status,
        }
