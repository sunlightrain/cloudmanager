from typing import Optional
from pydantic import BaseModel


class VMBase(BaseModel):
    name: str
    cpu: int = 2
    memory_mb: int = 4096
    disk_gb: int = 50


class VMCreate(VMBase):
    network_name: str = "VM Network"
    datastore: str = "datastore1"
    guest_id: str = "ubuntu64Guest"
    annotation: Optional[str] = None


class VMUpdate(BaseModel):
    cpu: Optional[int] = None
    memory_mb: Optional[int] = None


class VMPowerAction(BaseModel):
    action: str


class VMResponse(VMBase):
    vm_id: str
    status: str
    ip_address: Optional[str] = None
    host: Optional[str] = None
    datastore: Optional[str] = None
    guest_full_name: Optional[str] = None
    annotation: Optional[str] = None
    
    class Config:
        from_attributes = True


class VMListResponse(BaseModel):
    items: list[VMResponse]
    total: int
    page: int = 1
    page_size: int = 20
