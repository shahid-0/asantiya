"""Tests for configuration loading and validation."""

from unittest.mock import patch

import pytest
import yaml

from asantiya.schemas.models import ConfigurationError
from asantiya.utils.config import (
    DocumentedConfigGenerator,
    load_config,
    validate_config_file,
)


class TestLoadConfig:
    """Test configuration loading functionality."""

    def test_load_config_success(self, sample_config_file):
        """Test successful configuration loading."""
        config = load_config(str(sample_config_file))
        assert config.service == "test-app"
        assert config.image == "test-app:latest"
        assert config.app_ports == "8080:80"

    def test_load_config_file_not_found(self, temp_dir):
        """Test loading non-existent config file."""
        with pytest.raises(FileNotFoundError):
            load_config(str(temp_dir / "nonexistent.yaml"))

    def test_load_config_invalid_yaml(self, temp_dir):
        """Test loading invalid YAML file."""
        invalid_yaml = temp_dir / "invalid.yaml"
        invalid_yaml.write_text("invalid: yaml: content: [")

        with pytest.raises(ConfigurationError) as exc_info:
            load_config(str(invalid_yaml))

        assert "YAML parsing error" in str(exc_info.value)

    def test_load_config_empty_file(self, temp_dir):
        """Test loading empty YAML file."""
        empty_file = temp_dir / "empty.yaml"
        empty_file.write_text("")

        with pytest.raises(ConfigurationError) as exc_info:
            load_config(str(empty_file))

        assert "YAML file is empty" in str(exc_info.value)

    def test_load_config_with_env_vars(self, temp_dir):
        """Test loading config with environment variable substitution."""
        config_data = {
            "service": "test-app",
            "image": "${IMAGE_NAME}",
            "app_ports": "8080:80",
            "server": "${SERVER_HOST}",
        }

        config_file = temp_dir / "env_config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        with patch.dict(
            "os.environ",
            {"IMAGE_NAME": "my-app:latest", "SERVER_HOST": "prod.example.com"},
        ):
            config = load_config(str(config_file))
            assert config.image == "my-app:latest"
            assert config.server == "prod.example.com"

    def test_load_config_missing_required_env_var(self, temp_dir):
        """Test loading config with missing required environment variable."""
        config_data = {
            "service": "test-app",
            "image": "${REQUIRED_VAR}",
            "app_ports": "8080:80",
        }

        config_file = temp_dir / "missing_env.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        with pytest.raises(ConfigurationError) as exc_info:
            load_config(str(config_file), required_vars=["REQUIRED_VAR"])

        assert "Environment variable error" in str(exc_info.value)

    def test_load_config_validation_error(self, temp_dir):
        """Test loading config with validation errors."""
        invalid_config = {
            "service": "",  # Invalid empty service name
            "image": "test-app",
            "app_ports": "invalid-ports",  # Invalid port format
        }

        config_file = temp_dir / "invalid_config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(invalid_config, f)

        with pytest.raises(ConfigurationError) as exc_info:
            load_config(str(config_file))

        assert "Configuration validation failed" in str(exc_info.value)

    def test_load_config_save_output(self, sample_config_file, temp_dir):
        """Test loading config and saving processed output."""
        output_file = temp_dir / "processed.yaml"

        config = load_config(str(sample_config_file), str(output_file))

        assert output_file.exists()
        assert config.service == "test-app"

        # Verify output file contains processed config
        with open(output_file, "r") as f:
            saved_data = yaml.safe_load(f)
        assert saved_data["service"] == "test-app"


class TestValidateConfigFile:
    """Test configuration file validation."""

    def test_validate_config_success(self, sample_config_file):
        """Test successful config validation."""
        result = validate_config_file(str(sample_config_file))

        assert result["valid"] is True
        assert result["service"] == "test-app"
        assert result["image"] == "test-app:latest"
        assert result["accessories_count"] == 1
        assert result["has_builder"] is True

    def test_validate_config_file_not_found(self, temp_dir):
        """Test validating non-existent config file."""
        with pytest.raises(ConfigurationError) as exc_info:
            validate_config_file(str(temp_dir / "nonexistent.yaml"))

        assert "Configuration file not found" in str(exc_info.value)

    def test_validate_config_missing_required_keys(self, temp_dir):
        """Test validating config with missing required keys."""
        incomplete_config = {
            "service": "test-app"
            # Missing 'image' and 'app_ports'
        }

        config_file = temp_dir / "incomplete.yaml"
        with open(config_file, "w") as f:
            yaml.dump(incomplete_config, f)

        with pytest.raises(ConfigurationError) as exc_info:
            validate_config_file(str(config_file))

        assert "Missing required configuration keys" in str(exc_info.value)

    def test_validate_config_invalid_ports(self, temp_dir):
        """Test validating config with invalid port format."""
        invalid_config = {
            "service": "test-app",
            "image": "test-app:latest",
            "app_ports": "invalid-ports",
        }

        config_file = temp_dir / "invalid_ports.yaml"
        with open(config_file, "w") as f:
            yaml.dump(invalid_config, f)

        with pytest.raises(ConfigurationError) as exc_info:
            validate_config_file(str(config_file))

        assert "app_ports must be in 'HOST:CONTAINER' format" in str(exc_info.value)


class TestDocumentedConfigGenerator:
    """Test documented configuration generator."""

    def test_generate_documented_yaml_default(self):
        """Test generating documented YAML with default values."""
        yaml_content = DocumentedConfigGenerator.generate_documented_yaml()

        assert "service: asantiya" in yaml_content
        assert "image: ${HOST_USER}/asantiya" in yaml_content
        assert "app_ports: 8020:8020" in yaml_content
        assert "# Main application configuration" in yaml_content

    def test_generate_documented_yaml_with_customizations(self):
        """Test generating documented YAML with custom values."""
        yaml_content = DocumentedConfigGenerator.generate_documented_yaml(
            service="my-app", image="my-app:latest", app_ports="3000:3000"
        )

        assert "service: my-app" in yaml_content
        assert "image: my-app:latest" in yaml_content
        assert "app_ports: 3000:3000" in yaml_content

    def test_generate_documented_yaml_save_to_file(self, temp_dir):
        """Test generating and saving documented YAML to file."""
        output_path = temp_dir / "generated.yaml"

        yaml_content = DocumentedConfigGenerator.generate_documented_yaml(
            output_path=output_path, service="test-app"
        )

        assert output_path.exists()
        assert "service: test-app" in yaml_content

        # Verify file content
        with open(output_path, "r") as f:
            file_content = f.read()
        assert "service: test-app" in file_content

    def test_generate_documented_yaml_with_accessories(self):
        """Test generating YAML with custom accessories."""
        custom_accessories = {
            "redis": {
                "service": "my-redis",
                "image": "redis:alpine",
                "ports": "6379:6379",
                "network": "my-network",
            }
        }

        yaml_content = DocumentedConfigGenerator.generate_documented_yaml(
            accessories=custom_accessories
        )

        assert "redis:" in yaml_content
        assert "service: my-redis" in yaml_content
        assert "image: redis:alpine" in yaml_content
