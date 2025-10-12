"""Tests for Docker manager functionality."""

from unittest.mock import Mock, patch

import pytest

from asantiya.docker_manager import DockerManager
from asantiya.schemas.models import DockerError


class TestDockerManager:
    """Test DockerManager class."""

    def test_init_with_default_config(self, mock_docker_client):
        """Test DockerManager initialization with default config."""
        with patch("asantiya.docker_manager.load_config") as mock_load:
            mock_load.return_value = Mock()
            manager = DockerManager()
            assert manager.docker_client is None
            mock_load.assert_called_once()

    def test_init_with_custom_config_path(self, mock_docker_client):
        """Test DockerManager initialization with custom config path."""
        config_path = "/custom/path/deploy.yaml"
        with patch("asantiya.docker_manager.load_config") as mock_load:
            mock_load.return_value = Mock()
            DockerManager(config_path)
            mock_load.assert_called_once_with(config_path)

    def test_connect_local_success(self, app_config, mock_docker_client):
        """Test successful local Docker connection."""
        app_config.builder.local = True

        with patch("asantiya.docker_manager.load_config", return_value=app_config):
            with patch("docker.from_env", return_value=mock_docker_client):
                manager = DockerManager()
                result = manager.connect()

                assert result == mock_docker_client
                assert manager.docker_client == mock_docker_client

    def test_connect_remote_success(self, app_config, mock_docker_client):
        """Test successful remote Docker connection."""
        app_config.builder.local = False
        app_config.builder.remote = "ssh://user@host"

        with patch("asantiya.docker_manager.load_config", return_value=app_config):
            with patch("docker.DockerClient", return_value=mock_docker_client):
                manager = DockerManager()
                result = manager.connect()

                assert result == mock_docker_client
                assert manager.docker_client == mock_docker_client

    def test_connect_no_remote_url(self, app_config):
        """Test connection failure when remote URL is not configured."""
        app_config.builder.local = False
        app_config.builder.remote = ""

        with patch("asantiya.docker_manager.load_config", return_value=app_config):
            manager = DockerManager()

            with pytest.raises(DockerError) as exc_info:
                manager.connect()

            assert "Remote Docker URL not configured" in str(exc_info.value)

    def test_connect_docker_exception(self, app_config):
        """Test connection failure with Docker exception."""
        app_config.builder.local = True

        with patch("asantiya.docker_manager.load_config", return_value=app_config):
            with patch("docker.from_env", side_effect=Exception("Connection failed")):
                manager = DockerManager()

                with pytest.raises(DockerError) as exc_info:
                    manager.connect()

                assert "Unexpected error connecting to Docker" in str(exc_info.value)

    def test_check_docker_version_success(self, app_config, mock_docker_client):
        """Test successful Docker version check."""
        with patch("asantiya.docker_manager.load_config", return_value=app_config):
            manager = DockerManager()
            manager.docker_client = mock_docker_client

            version = manager.check_docker_version()
            assert version == "20.10.0"
            mock_docker_client.version.assert_called_once()

    def test_check_docker_version_no_client(self, app_config):
        """Test Docker version check without connected client."""
        with patch("asantiya.docker_manager.load_config", return_value=app_config):
            manager = DockerManager()

            with pytest.raises(DockerError) as exc_info:
                manager.check_docker_version()

            assert "Docker client is not connected" in str(exc_info.value)

    def test_check_docker_version_exception(self, app_config, mock_docker_client):
        """Test Docker version check with exception."""
        mock_docker_client.version.side_effect = Exception("Version check failed")

        with patch("asantiya.docker_manager.load_config", return_value=app_config):
            manager = DockerManager()
            manager.docker_client = mock_docker_client

            with pytest.raises(DockerError) as exc_info:
                manager.check_docker_version()

            assert "Unexpected error while checking Docker version" in str(
                exc_info.value
            )

    def test_delete_image_success(self, app_config, mock_docker_client):
        """Test successful image deletion."""
        with patch("asantiya.docker_manager.load_config", return_value=app_config):
            manager = DockerManager()
            manager.docker_client = mock_docker_client

            result = manager.delete_image("test-image:latest")
            assert result is True
            mock_docker_client.images.get.assert_called_once_with("test-image:latest")
            mock_docker_client.images.remove.assert_called_once()

    def test_delete_image_not_found(self, app_config, mock_docker_client):
        """Test image deletion when image not found."""
        from docker.errors import ImageNotFound

        mock_docker_client.images.get.side_effect = ImageNotFound("Image not found")

        with patch("asantiya.docker_manager.load_config", return_value=app_config):
            manager = DockerManager()
            manager.docker_client = mock_docker_client

            result = manager.delete_image("nonexistent-image")
            assert result is False

    def test_delete_image_no_client(self, app_config):
        """Test image deletion without connected client."""
        with patch("asantiya.docker_manager.load_config", return_value=app_config):
            manager = DockerManager()

            with pytest.raises(DockerError) as exc_info:
                manager.delete_image("test-image")

            assert "Docker client not connected" in str(exc_info.value)

    def test_delete_image_empty_name(self, app_config, mock_docker_client):
        """Test image deletion with empty image name."""
        with patch("asantiya.docker_manager.load_config", return_value=app_config):
            manager = DockerManager()
            manager.docker_client = mock_docker_client

            with pytest.raises(DockerError) as exc_info:
                manager.delete_image("")

            assert "Image name cannot be empty" in str(exc_info.value)

    def test_delete_images_success(self, app_config, mock_docker_client):
        """Test successful deletion of multiple images."""
        with patch("asantiya.docker_manager.load_config", return_value=app_config):
            manager = DockerManager()
            manager.docker_client = mock_docker_client

            results = manager.delete_images(["image1", "image2"])

            assert results["image1"] is True
            assert results["image2"] is True
            assert mock_docker_client.images.get.call_count == 2

    def test_delete_images_with_errors(self, app_config, mock_docker_client):
        """Test deletion of multiple images with some errors."""
        from docker.errors import ImageNotFound

        def side_effect(image_name):
            if image_name == "image1":
                # Return a proper mock image object
                mock_image = Mock()
                mock_image.id = "test-image-id"
                mock_image.tags = ["image1:latest"]
                return mock_image
            else:
                raise ImageNotFound("Not found")

        mock_docker_client.images.get.side_effect = side_effect

        with patch("asantiya.docker_manager.load_config", return_value=app_config):
            manager = DockerManager()
            manager.docker_client = mock_docker_client

            results = manager.delete_images(["image1", "image2"])

            assert results["image1"] is True
            assert results["image2"] is False

    def test_get_service_name_with_service(self, app_config):
        """Test getting service name when service is specified."""
        from asantiya.schemas.models import AccessoryConfig

        accessory = AccessoryConfig(
            image="test", network="test", ports="8080:80", service="custom-service"
        )

        with patch("asantiya.docker_manager.load_config", return_value=app_config):
            manager = DockerManager()

            service_name = manager._get_service_name(accessory, "test")
            assert service_name == "custom-service"

    def test_get_service_name_without_service(self, app_config):
        """Test getting service name when service is not specified."""
        from asantiya.schemas.models import AccessoryConfig

        accessory = AccessoryConfig(image="test", network="test", ports="8080:80")

        with patch("asantiya.docker_manager.load_config", return_value=app_config):
            manager = DockerManager()

            service_name = manager._get_service_name(accessory, "test")
            assert service_name == "asantiya-test"

    def test_find_accessory_by_name_found(self, app_config):
        """Test finding accessory by name when it exists."""
        app_config.accessories = {
            "db": Mock(service="asantiya-db"),
            "redis": Mock(service="asantiya-redis"),
        }

        with patch("asantiya.docker_manager.load_config", return_value=app_config):
            manager = DockerManager()

            result = manager._find_accessory_by_name("asantiya-db")
            assert result == "asantiya-db"

    def test_find_accessory_by_name_not_found(self, app_config):
        """Test finding accessory by name when it doesn't exist."""
        app_config.accessories = {"db": Mock(service="asantiya-db")}

        with patch("asantiya.docker_manager.load_config", return_value=app_config):
            manager = DockerManager()

            result = manager._find_accessory_by_name("nonexistent")
            assert result is None
