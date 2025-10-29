import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from asantiya.schemas.models import AppConfig, ConfigurationError
from asantiya.utils.load_env import get_env


class DocumentedConfigGenerator:
    @staticmethod
    def generate_documented_yaml(output_path: Optional[Path] = None, **kwargs) -> str:
        """
        Generate YAML configuration with inline documentation

        Args:
            output_path: Optional file path to save the config
            **kwargs: Configuration overrides

        Returns:
            YAML string with documentation comments
        """
        config = {
            "# Main application configuration": None,
            "service": "asantiya",
            "image": "${HOST_USER}/asantiya",
            "# Port mappings (host:container)": None,
            "app_ports": "8020:8020",
            "# Host machine configuration (set to false if not needed)": None,
            "host": False,
            "# Build configuration": None,
            "builder": {
                "# Target architecture (amd64/arm64/armv7)": None,
                "arch": "arm64",
                "# Remote build server (SSH connection string)": None,
                "remote": "ssh://${HOST_USER}@${SERVER}",
                "# Local build flag": None,
                "local": False,
            },
            "# Container services definitions": None,
            "accessories": {
                "db": {
                    "# PostgreSQL database service": None,
                    "service": "asantiya-db",
                    "image": "postgres:13",
                    "# Port mapping (host:container)": None,
                    "ports": "8069:8069",
                    "# Container behavior options": None,
                    "options": {
                        "# Restart policy (always/unless-stopped/on-failure)": None,
                        "restart": "always",
                    },
                    "# Environment variables": None,
                    "env": {
                        "POSTGRES_PASSWORD": "some-strong-password-for-postgressql"
                    },
                    "# Volume mounts (host_path:container_path[:ro])": None,
                    "volumes": ["myvolume:/var/lib/postgresql/data"],
                    "# Network connection": None,
                    "network": "asantiya-network",
                }
            },
        }

        # Apply any customizations
        config.update(kwargs)

        # Convert to YAML with preserved comments
        yaml_str = yaml.dump(
            config, sort_keys=False, default_flow_style=False, width=120, indent=2
        )

        # Post-processing to handle comment markers
        yaml_str = yaml_str.replace("'# ", "# ").replace("': null", "")

        if output_path:
            output_path.write_text(yaml_str)
        return yaml_str


def load_config(
    yaml_file_path: str,
    output_file_path: Optional[str] = None,
    required_vars: Optional[List[str]] = None,
) -> AppConfig:
    """
    Load and validate configuration from a YAML file with environment variable substitution.

    Args:
        yaml_file_path: Path to the input YAML file with placeholders
        output_file_path: Path to save the processed YAML (if None, returns config without saving)
        required_vars: List of environment variables that must be set

    Returns:
        Validated AppConfig instance

    Raises:
        ConfigurationError: If configuration validation fails
        FileNotFoundError: If YAML file doesn't exist
        yaml.YAMLError: If YAML parsing fails
    """
    yaml_path = Path(yaml_file_path)

    # Validate input file exists
    if not yaml_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {yaml_file_path}")

    if not yaml_path.is_file():
        raise ConfigurationError(f"Path is not a file: {yaml_file_path}")

    # Pattern to match ${ENV_VAR} style placeholders
    env_var_pattern = re.compile(r"\$\{([^}]+)\}")

    def replace_env_vars(value: Any) -> Any:
        """Replace all environment variable placeholders in a value."""
        if isinstance(value, str):

            def replace_match(match):
                var_name = match.group(1)
                # Check if this is a required variable
                is_required = required_vars and var_name in required_vars
                try:
                    return get_env(var_name, required=is_required)
                except EnvironmentError as e:
                    raise ConfigurationError(f"Environment variable error: {e}")

            return env_var_pattern.sub(replace_match, value)
        return value

    try:
        # Read and parse YAML file
        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if data is None:
            raise ConfigurationError("YAML file is empty or contains no valid data")

        # Process the entire data structure recursively
        def process(item: Any) -> Any:
            if isinstance(item, dict):
                return {k: process(v) for k, v in item.items()}
            elif isinstance(item, list):
                return [process(v) for v in item]
            elif isinstance(item, str):
                return replace_env_vars(item)
            return item

        processed_data = process(data)

        # Save to output file if specified
        if output_file_path:
            output_path = Path(output_file_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                yaml.dump(processed_data, f, default_flow_style=False, indent=2)

        # Validate and return configuration
        try:
            return AppConfig(**processed_data)
        except Exception as e:
            raise ConfigurationError(f"Configuration validation failed: {e}")

    except yaml.YAMLError as e:
        raise ConfigurationError(f"YAML parsing error: {e}")
    except Exception as e:
        if isinstance(e, ConfigurationError):
            raise
        raise ConfigurationError(f"Unexpected error loading configuration: {e}")


def validate_config_file(config_path: str) -> Dict[str, Any]:
    """
    Validate a configuration file without loading it as AppConfig.

    Args:
        config_path: Path to the YAML configuration file

    Returns:
        Dictionary containing validation results

    Raises:
        ConfigurationError: If validation fails
    """
    yaml_path = Path(config_path)

    if not yaml_path.exists():
        raise ConfigurationError(f"Configuration file not found: {config_path}")

    try:
        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if data is None:
            raise ConfigurationError("YAML file is empty")

        # Basic structure validation
        required_keys = ["service", "image", "app_ports"]
        missing_keys = [key for key in required_keys if key not in data]

        if missing_keys:
            raise ConfigurationError(
                f"Missing required configuration keys: {', '.join(missing_keys)}"
            )

        # Validate port format
        if "app_ports" in data:
            ports = data["app_ports"]
            if not isinstance(ports, str) or ":" not in ports:
                raise ConfigurationError("app_ports must be in 'HOST:CONTAINER' format")

        return {
            "valid": True,
            "service": data.get("service"),
            "image": data.get("image"),
            "accessories_count": len(data.get("accessories", {})),
            "has_builder": "builder" in data,
        }

    except yaml.YAMLError as e:
        raise ConfigurationError(f"YAML parsing error: {e}")
    except Exception as e:
        if isinstance(e, ConfigurationError):
            raise
        raise ConfigurationError(f"Validation error: {e}")
