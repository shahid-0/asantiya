"""Pytest configuration and fixtures for Asantiya tests."""

import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest
import yaml

from asantiya.schemas.models import AppConfig


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_config_data(temp_dir):
    """Sample configuration data for testing."""
    # Create a dummy Dockerfile for testing
    dockerfile = temp_dir / "Dockerfile"
    dockerfile.write_text("FROM python:3.9\n")

    return {
        "service": "test-app",
        "image": "test-app:latest",
        "app_ports": "8080:80",
        "builder": {
            "arch": "amd64",
            "remote": "ssh://user@test-server.com",
            "local": False,
            "dockerfile": str(temp_dir),
        },
        "accessories": {
            "db": {
                "service": "test-db",
                "image": "postgres:13",
                "network": "test-network",
                "ports": "5432:5432",
                "env": {"POSTGRES_PASSWORD": "testpass"},
                "volumes": ["db_data:/var/lib/postgresql/data"],
                "options": {"restart": "always"},
            }
        },
    }


@pytest.fixture
def sample_config_file(temp_dir, sample_config_data):
    """Create a sample configuration file."""
    config_file = temp_dir / "deploy.yaml"
    with open(config_file, "w") as f:
        yaml.dump(sample_config_data, f)
    return config_file


@pytest.fixture
def app_config(sample_config_data):
    """Create an AppConfig instance from sample data."""
    return AppConfig(**sample_config_data)


@pytest.fixture
def mock_docker_client():
    """Mock Docker client for testing."""
    client = Mock()

    # Mock version info
    client.version.return_value = {"Version": "20.10.0"}
    client.ping.return_value = True

    # Mock containers
    mock_container = Mock()
    mock_container.id = "test-container-id"
    mock_container.name = "test-container"
    mock_container.status = "running"
    mock_container.image.tags = ["test-image:latest"]
    mock_container.attrs = {
        "State": {"StartedAt": "2023-01-01T00:00:00Z", "Status": "running"},
        "NetworkSettings": {"Ports": {"80/tcp": [{"HostPort": "8080"}]}},
    }

    client.containers.get.return_value = mock_container
    client.containers.list.return_value = [mock_container]
    client.containers.run.return_value = mock_container

    # Mock images
    mock_image = Mock()
    mock_image.id = "test-image-id"
    mock_image.tags = ["test-image:latest"]

    client.images.get.return_value = mock_image
    client.images.remove.return_value = True

    # Mock networks
    mock_network = Mock()
    mock_network.name = "test-network"
    client.networks.list.return_value = [mock_network]
    client.networks.create.return_value = mock_network

    return client


@pytest.fixture
def mock_ssh_client():
    """Mock SSH client for testing."""
    client = Mock()
    client.connect.return_value = None
    client.exec_command.return_value = (Mock(), Mock(), Mock())
    client.close.return_value = None
    return client


@pytest.fixture
def mock_logger():
    """Mock logger for testing."""
    logger = Mock()
    logger.info = Mock()
    logger.error = Mock()
    logger.warning = Mock()
    logger.debug = Mock()
    logger.exception = Mock()
    return logger


@pytest.fixture
def sample_dockerfile(temp_dir):
    """Create a sample Dockerfile for testing."""
    dockerfile = temp_dir / "Dockerfile"
    dockerfile.write_text(
        """
FROM python:3.9-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "app.py"]
"""
    )
    return dockerfile
