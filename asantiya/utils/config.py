import re
import yaml
from typing import Optional
from asantiya.schemas.models import AppConfig
from asantiya.utils.load_env import get_env
from pathlib import Path

class DocumentedConfigGenerator:
    @staticmethod
    def generate_documented_yaml(
        output_path: Optional[Path] = None,
        **kwargs
    ) -> str:
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
            
            "# Server connection details (use environment variables)": None,
            "server": "${SERVER}",
            
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
                "local": False
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
                        "restart": "always"
                    },
                    
                    "# Environment variables": None,
                    "env": {
                        "POSTGRES_PASSWORD": "some-strong-password-for-postgressql"
                    },
                    
                    "# Volume mounts (host_path:container_path[:ro])": None,
                    "volumes": [
                        "myvolume:/var/lib/postgresql/data"
                    ],
                    
                    "# Network connection": None,
                    "network": "asantiya-network"
                }
            }
        }
        
        # Apply any customizations
        config.update(kwargs)
        
        # Convert to YAML with preserved comments
        yaml_str = yaml.dump(
            config,
            sort_keys=False,
            default_flow_style=False,
            width=120,
            indent=2
        )
        
        # Post-processing to handle comment markers
        yaml_str = yaml_str.replace("'# ", "# ").replace("': null", "")
        
        if output_path:
            output_path.write_text(yaml_str)
        return yaml_str

def load_config(yaml_file_path: str, output_file_path: str = None, 
                      required_vars: list = None) -> AppConfig:
    """
    Load environment variables into a YAML file, replacing ${VAR} placeholders with actual values.
    
    Args:
        yaml_file_path: Path to the input YAML file with placeholders
        output_file_path: Path to save the processed YAML (if None, returns dict without saving)
        required_vars: List of environment variables that must be set
    
    Returns:
        Dictionary with environment variables substituted
    
    Raises:
        EnvironmentError: If any required variable is missing
    """
    # Pattern to match ${ENV_VAR} style placeholders
    env_var_pattern = re.compile(r'\$\{([^}]+)\}')
    
    def replace_env_vars(value):
        """Replace all environment variable placeholders in a string."""
        if isinstance(value, str):
            def replace_match(match):
                var_name = match.group(1)
                # Check if this is a required variable
                is_required = required_vars and var_name in required_vars
                return get_env(var_name, required=is_required)
            return env_var_pattern.sub(replace_match, value)
        return value
    
    # Read the YAML file
    with open(yaml_file_path, 'r') as f:
        data = yaml.safe_load(f)
    
    # Process the entire data structure recursively
    def process(item):
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
        with open(output_file_path, 'w') as f:
            yaml.dump(processed_data, f)
    
    return AppConfig(**processed_data)
    
