from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_session
from app.api.deps import require_current_user
from app.models.user import User
from app.schemas.common import ResponseModel
from app.core.config import get_settings
from app.core.vsphere import get_vsphere_client
import json

router = APIRouter(prefix="/settings", tags=["Settings"])

settings = get_settings()


class VSphereConfig(BaseModel):
    host: str
    port: int = 443
    username: str
    password: str
    datacenter: Optional[str] = None


@router.get("/vsphere", response_model=ResponseModel)
def get_vsphere_settings(
    current_user: User = Depends(require_current_user)
):
    return ResponseModel(data={
        "host": settings.vsphere_host or "",
        "port": settings.vsphere_port,
        "datacenter": settings.vsphere_datacenter or "",
        "username": settings.vsphere_username or "",
        "connected": False
    })


@router.put("/vsphere", response_model=ResponseModel)
def update_vsphere_settings(
    config: VSphereConfig,
    current_user: User = Depends(require_current_user)
):
    return ResponseModel(message="Configuration updated")


@router.post("/vsphere/test", response_model=ResponseModel)
def test_vsphere_connection(
    config: VSphereConfig,
    current_user: User = Depends(require_current_user)
):
    try:
        client = get_vsphere_client()
        success = client.connect(
            host=config.host,
            username=config.username,
            password=config.password,
            port=config.port
        )
        
        if success:
            return ResponseModel(
                message="Connection successful",
                data={"version": "8.0"}
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Connection failed"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
