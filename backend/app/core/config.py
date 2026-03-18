from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "VMware Cloud Manager"
    debug: bool = True
    
    database_url: str = "sqlite:///./cloud_manager.db"
    
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24
    
    vsphere_host: Optional[str] = None
    vsphere_port: int = 443
    vsphere_username: Optional[str] = None
    vsphere_password: Optional[str] = None
    vsphere_datacenter: Optional[str] = None
    
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()
