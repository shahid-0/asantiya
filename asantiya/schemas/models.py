import re
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class AsantiyaError(Exception):
    """Base exception for Asantiya-specific errors."""

    pass


class ConfigurationError(AsantiyaError):
    """Raised when there's a configuration validation error."""

    pass


class DockerError(AsantiyaError):
    """Raised when there's a Docker-related error."""

    pass


class SSHConnectionError(AsantiyaError):
    """Raised when there's an SSH connection error."""

    pass


class ContainerOptions(BaseModel):
    """Container runtime options configuration."""

    restart: Literal["always", "unless-stopped", "on-failure", "no"] = "always"

    @field_validator("restart")
    @classmethod
    def validate_restart_policy(cls, v: str) -> str:
        valid_policies = ["always", "unless-stopped", "on-failure", "no"]
        if v not in valid_policies:
            raise ValueError(
                f"Invalid restart policy '{v}'. Must be one of: {', '.join(valid_policies)}"
            )
        return v


class Builder(BaseModel):
    """Build configuration for Docker images."""

    arch: Literal["amd64", "arm64", "armv7"] = "amd64"
    remote: str = ""
    local: bool = False
    dockerfile: Path = Field(default_factory=Path.cwd)
    build_args: Dict[str, str] = Field(default_factory=dict)

    @property
    def platform(self) -> str:
        """Get the Docker platform string."""
        return f"linux/{self.arch}"

    @field_validator("dockerfile")
    @classmethod
    def validate_dockerfile(cls, v: Path) -> Path:
        """Validate that Dockerfile exists in the specified path."""
        if not v.exists():
            raise ValueError(f"Dockerfile path does not exist: {v}")
        if not (v / "Dockerfile").exists():
            raise ValueError(f"Dockerfile not found in {v}")
        return v

    @field_validator("remote")
    @classmethod
    def validate_remote_url(cls, v: str) -> str:
        """Validate remote SSH URL format."""
        if v and not v.startswith(("ssh://", "tcp://")):
            raise ValueError("Remote URL must start with 'ssh://' or 'tcp://'")
        return v


class AccessoryConfig(BaseModel):
    """Configuration for accessory containers (databases, caches, etc.)."""

    image: str
    service: Optional[str] = None
    network: str
    ports: str
    env: Dict[str, str] = Field(default_factory=dict)
    options: ContainerOptions = Field(default_factory=ContainerOptions)
    volumes: List[str] = Field(default_factory=list)
    depends_on: List[str] = Field(default_factory=list)
    healthcheck: Optional[Dict[str, Any]] = None

    @field_validator("ports")
    @classmethod
    def validate_ports(cls, v: str) -> str:
        """Validate port mapping format."""
        if not v or ":" not in v:
            raise ValueError("Ports must be in HOST:CONTAINER format (e.g., '8080:80')")

        parts = v.split(":")
        if len(parts) != 2:
            raise ValueError("Ports must be in HOST:CONTAINER format")

        try:
            int(parts[0])  # Host port
            int(parts[1])  # Container port
        except ValueError:
            raise ValueError("Port numbers must be integers")

        return v

    @field_validator("volumes")
    @classmethod
    def validate_volumes(cls, v: List[str]) -> List[str]:
        """Validate volume mount format."""
        for volume in v:
            parts = volume.split(":")
            if len(parts) < 2 or len(parts) > 3:
                raise ValueError(
                    f"Invalid volume format '{volume}'. Use 'host:container[:mode]'"
                )
            if len(parts) == 3 and parts[2] not in ["ro", "rw"]:
                raise ValueError(f"Invalid volume mode '{parts[2]}'. Use 'ro' or 'rw'")
        return v

    @field_validator("image")
    @classmethod
    def validate_image_name(cls, v: str) -> str:
        """Validate Docker image name format."""
        if not v or not v.strip():
            raise ValueError("Image name cannot be empty")

        # Basic validation for Docker image name format
        if "/" in v:
            parts = v.split("/")
            if len(parts) > 2:
                raise ValueError(
                    "Invalid image name format. Use 'registry/namespace/image:tag' or 'image:tag'"
                )

        return v.strip()


class AppConfig(BaseModel):
    """Main application configuration."""

    service: str = "asantiya"
    image: str = "asantiya-service"
    server: str = "${SERVER}"
    app_ports: str = "8020:8020"
    builder: Builder = Field(default_factory=Builder)
    accessories: Dict[str, AccessoryConfig] = Field(default_factory=dict)
    environment: Dict[str, str] = Field(default_factory=dict)
    volumes: List[str] = Field(default_factory=list)
    network: str = "asantiya-network"

    @field_validator("app_ports")
    @classmethod
    def validate_app_ports(cls, v: str) -> str:
        """Validate application port mapping."""
        if not v or ":" not in v:
            raise ValueError("App ports must be in HOST:CONTAINER format")

        parts = v.split(":")
        if len(parts) != 2:
            raise ValueError("App ports must be in HOST:CONTAINER format")

        try:
            int(parts[0])  # Host port
            int(parts[1])  # Container port
        except ValueError:
            raise ValueError("Port numbers must be integers")

        return v

    @field_validator("service")
    @classmethod
    def validate_service_name(cls, v: str) -> str:
        """Validate service name format."""
        if not v or not v.strip():
            raise ValueError("Service name cannot be empty")

        # Docker container name validation
        if not re.match(r"^[a-zA-Z0-9][a-zA-Z0-9_.-]*$", v):
            raise ValueError(
                "Service name must start with alphanumeric and contain only alphanumeric, underscore, dot, or dash"
            )

        return v.strip()

    @model_validator(mode="after")
    def validate_dependencies(self) -> "AppConfig":
        """Validate that accessory dependencies exist."""
        accessory_names = set(self.accessories.keys())

        for name, accessory in self.accessories.items():
            for dep in accessory.depends_on:
                if dep not in accessory_names:
                    raise ValueError(
                        f"Accessory '{name}' depends on '{dep}' which is not defined"
                    )

        return self
