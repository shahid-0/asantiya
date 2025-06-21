import re
import yaml
from typing import Any, Dict
from asantiya.schemas.models import AppConfig, HostConfig
from asantiya.utils.load_env import get_env

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
    
def _is_local(config: HostConfig) -> bool:
    """
    Returns True if running locally (i.e., no key/password set), or host is explicitly boolean.
    """
    host = config.host
    
    # If host is explicitly False or not a dict-like object, treat as local
    if isinstance(host, bool):
        return host is False

    # If host is None or missing key/password, assume local
    return not (getattr(host, "key", None) or getattr(host, "password", None))
