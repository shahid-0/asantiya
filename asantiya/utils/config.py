import re
import yaml
from pathlib import Path
from asantiya.schemas.models import AppConfig, HostConfig
from asantiya.utils.load_env import get_env

# Register the !ENV tag support
env_var_pattern = re.compile(r'.*?\${(\w+)}.*?')

def env_var_constructor(loader, node) -> str:
    value = loader.construct_scalar(node)
    matches = env_var_pattern.findall(value)
    for var in matches:
        env_value = get_env(var, default=f"<missing:{var}>")
        value = value.replace(f"${{{var}}}", env_value)
    return value

yaml.SafeLoader.add_constructor("!ENV", env_var_constructor)

def load_config(file_path: Path) -> AppConfig:
    """Load and validate YAML configuration, with environment variable support"""
    try:
        path = Path(file_path).expanduser()
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {file_path}")
        
        with open(path, 'r') as f:
            raw_config = yaml.load(f, Loader=yaml.SafeLoader)  # Use loader with !ENV
        
        return AppConfig(**raw_config)  # Validates using your Pydantic model
    
    except yaml.YAMLError as e:
        raise RuntimeError(f"YAML parsing error: {e}")
    except Exception as e:
        raise RuntimeError(f"Configuration error: {str(e)}")
    
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
