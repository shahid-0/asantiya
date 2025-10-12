"""Tests for schema models and validation."""

import pytest
from pydantic import ValidationError

from asantiya.schemas.models import (
    AccessoryConfig,
    AppConfig,
    Builder,
    ConfigurationError,
    ContainerOptions,
    DockerError,
    SSHConnectionError,
)


class TestContainerOptions:
    """Test ContainerOptions model."""

    def test_valid_restart_policies(self):
        """Test valid restart policies."""
        valid_policies = ["always", "unless-stopped", "on-failure", "no"]
        for policy in valid_policies:
            options = ContainerOptions(restart=policy)
            assert options.restart == policy

    def test_invalid_restart_policy(self):
        """Test invalid restart policy raises error."""
        with pytest.raises(ValidationError) as exc_info:
            ContainerOptions(restart="invalid")

        # Pydantic v2 uses different error message format
        error_msg = str(exc_info.value)
        assert (
            "Input should be 'always', 'unless-stopped', 'on-failure' or 'no'"
            in error_msg
        )


class TestBuilder:
    """Test Builder model."""

    def test_valid_architectures(self):
        """Test valid architectures."""
        valid_archs = ["amd64", "arm64", "armv7"]
        for arch in valid_archs:
            builder = Builder(arch=arch)
            assert builder.arch == arch
            assert builder.platform == f"linux/{arch}"

    def test_invalid_architecture(self):
        """Test invalid architecture raises error."""
        with pytest.raises(ValidationError):
            Builder(arch="invalid")

    def test_dockerfile_validation(self, temp_dir):
        """Test Dockerfile validation."""
        # Test with non-existent path
        with pytest.raises(ValidationError) as exc_info:
            Builder(dockerfile=temp_dir / "nonexistent")

        assert "Dockerfile path does not exist" in str(exc_info.value)

        # Test with path without Dockerfile
        with pytest.raises(ValidationError) as exc_info:
            Builder(dockerfile=temp_dir)

        assert "Dockerfile not found" in str(exc_info.value)

    def test_valid_dockerfile(self, sample_dockerfile):
        """Test valid Dockerfile path."""
        builder = Builder(dockerfile=sample_dockerfile.parent)
        assert builder.dockerfile == sample_dockerfile.parent

    def test_remote_url_validation(self):
        """Test remote URL validation."""
        # Valid URLs
        valid_urls = ["ssh://user@host", "tcp://host:2375"]
        for url in valid_urls:
            builder = Builder(remote=url)
            assert builder.remote == url

        # Invalid URL
        with pytest.raises(ValidationError) as exc_info:
            Builder(remote="invalid-url")

        assert "Remote URL must start with" in str(exc_info.value)


class TestAccessoryConfig:
    """Test AccessoryConfig model."""

    def test_valid_config(self):
        """Test valid accessory configuration."""
        config = AccessoryConfig(
            image="postgres:13",
            service="test-db",
            network="test-network",
            ports="5432:5432",
            env={"POSTGRES_PASSWORD": "test"},
            volumes=["data:/var/lib/postgresql/data"],
        )

        assert config.image == "postgres:13"
        assert config.service == "test-db"
        assert config.network == "test-network"
        assert config.ports == "5432:5432"

    def test_port_validation(self):
        """Test port format validation."""
        # Valid ports
        valid_ports = ["8080:80", "5432:5432", "3000:3000"]
        for ports in valid_ports:
            config = AccessoryConfig(image="test", network="test", ports=ports)
            assert config.ports == ports

        # Invalid ports
        invalid_ports = ["8080", "8080:abc", "abc:8080", ""]
        for ports in invalid_ports:
            with pytest.raises(ValidationError):
                AccessoryConfig(image="test", network="test", ports=ports)

    def test_volume_validation(self):
        """Test volume format validation."""
        # Valid volumes
        valid_volumes = [
            ["host:container"],
            ["host:container:ro"],
            ["host:container:rw"],
        ]
        for volumes in valid_volumes:
            config = AccessoryConfig(
                image="test", network="test", ports="8080:80", volumes=volumes
            )
            assert config.volumes == volumes

        # Invalid volumes
        invalid_volumes = [
            ["host"],  # Missing container
            ["host:container:invalid"],  # Invalid mode
            ["host:container:extra:invalid"],  # Too many parts
        ]
        for volumes in invalid_volumes:
            with pytest.raises(ValidationError):
                AccessoryConfig(
                    image="test", network="test", ports="8080:80", volumes=volumes
                )

    def test_image_validation(self):
        """Test image name validation."""
        # Valid images
        valid_images = ["nginx", "postgres:13", "registry.com/image:tag"]
        for image in valid_images:
            config = AccessoryConfig(image=image, network="test", ports="8080:80")
            assert config.image == image

        # Invalid images
        invalid_images = [
            "",
            "   ",
            "registry/namespace/sub/image:tag",
        ]  # Too many slashes
        for image in invalid_images:
            with pytest.raises(ValidationError):
                AccessoryConfig(image=image, network="test", ports="8080:80")


class TestAppConfig:
    """Test AppConfig model."""

    def test_valid_config(self, sample_config_data):
        """Test valid app configuration."""
        config = AppConfig(**sample_config_data)
        assert config.service == "test-app"
        assert config.image == "test-app:latest"
        assert config.app_ports == "8080:80"
        assert len(config.accessories) == 1
        assert "db" in config.accessories

    def test_app_ports_validation(self):
        """Test app ports validation."""
        # Valid ports
        valid_ports = ["8080:80", "3000:3000", "80:8080"]
        for ports in valid_ports:
            config = AppConfig(app_ports=ports)
            assert config.app_ports == ports

        # Invalid ports
        invalid_ports = ["8080", "abc:80", "80:abc", ""]
        for ports in invalid_ports:
            with pytest.raises(ValidationError):
                AppConfig(app_ports=ports)

    def test_service_name_validation(self):
        """Test service name validation."""
        # Valid names
        valid_names = ["my-app", "my_app", "my.app", "my-app-1", "app123"]
        for name in valid_names:
            config = AppConfig(service=name, image="test", app_ports="8080:80")
            assert config.service == name

        # Invalid names
        invalid_names = [
            "",
            "   ",
            "-app",
            "app@invalid",
            "app space",
            "app/with/slash",
        ]
        for name in invalid_names:
            with pytest.raises(ValidationError):
                AppConfig(service=name, image="test", app_ports="8080:80")

    def test_dependency_validation(self):
        """Test accessory dependency validation."""
        # Valid dependencies
        config_data = {
            "service": "test",
            "image": "test",
            "app_ports": "8080:80",
            "accessories": {
                "db": {
                    "image": "postgres",
                    "network": "test",
                    "ports": "5432:5432",
                    "depends_on": [],
                },
                "app": {
                    "image": "nginx",
                    "network": "test",
                    "ports": "80:80",
                    "depends_on": ["db"],
                },
            },
        }
        config = AppConfig(**config_data)
        assert config.accessories["app"].depends_on == ["db"]

        # Invalid dependencies
        config_data["accessories"]["app"]["depends_on"] = ["nonexistent"]
        with pytest.raises(ValidationError) as exc_info:
            AppConfig(**config_data)

        assert "depends on 'nonexistent' which is not defined" in str(exc_info.value)


class TestCustomExceptions:
    """Test custom exception classes."""

    def test_asantiya_error(self):
        """Test AsantiyaError base exception."""
        error = ConfigurationError("Test error")
        assert isinstance(error, Exception)
        assert str(error) == "Test error"

    def test_configuration_error(self):
        """Test ConfigurationError."""
        error = ConfigurationError("Config error")
        assert isinstance(error, ConfigurationError)
        assert str(error) == "Config error"

    def test_docker_error(self):
        """Test DockerError."""
        error = DockerError("Docker error")
        assert isinstance(error, DockerError)
        assert str(error) == "Docker error"

    def test_ssh_connection_error(self):
        """Test SSHConnectionError."""
        error = SSHConnectionError("SSH error")
        assert isinstance(error, SSHConnectionError)
        assert str(error) == "SSH error"
