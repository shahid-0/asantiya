from pydantic import BaseModel, Field, field_validator
from typing import Dict, List, Literal, Union, Optional
from pathlib import Path

class ContainerOptions(BaseModel):
    restart: str = "always"
    
    
class Builder(BaseModel):
    arch: Literal['amd64', 'arm64', 'armv7'] = 'amd64'
    remote: str = ""
    local: bool = False
    dockerfile: Path = Path.cwd()
    
    @property
    def platform(self) -> str:
        return f'linux/{self.arch}'
    
    @field_validator('dockerfile')
    def validate_dockerfile(cls, v: Path) -> Path:
        if not (v / 'Dockerfile').exists():
            raise ValueError(f"Dockerfile not found in {v}")
        return v

class AccessoryConfig(BaseModel):
    image: str
    service: Optional[str] = None
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
    service: str = "asantiya"
    image: str = "asantiya-service"
    server: str = "${SERVER}"
    app_ports: str = "HOST_PORT:CONTAINER_PORT"
    builder: Builder = Builder()
    accessories: Dict[str, AccessoryConfig] = Field(default_factory=dict)