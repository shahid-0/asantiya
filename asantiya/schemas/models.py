from pydantic import BaseModel, field_validator
from typing import Dict, List, Union
from pathlib import Path

class ContainerOptions(BaseModel):
    restart: str = "always"
    
class HostConfig(BaseModel):
    user: str = "root"
    key: Path = None
    password: str = None

class AccessoryConfig(BaseModel):
    image: str
    service: str
    network: str
    ports: str
    env: Dict[str, str] = {}
    options: ContainerOptions = ContainerOptions()
    volumes: List[str] = []
    depends_on: List[str] = []

    @field_validator('ports')
    def validate_ports(cls, v):
        if ':' not in v:
            raise ValueError("Ports must be in HOST:CONTAINER format")
        return v

class AppConfig(BaseModel):
    service: str
    server: str
    host: Union[HostConfig, bool]
    accessories: Dict[str, AccessoryConfig]