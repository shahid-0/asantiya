import os
from dotenv import load_dotenv

# Load the .env file once (you can optionally pass a path)
load_dotenv()  # or load_dotenv(dotenv_path=".env")

def get_env(key: str, default: str = None, required: bool = False) -> str:
    """
    Get an environment variable value, optionally with default or raise error if required.

    Args:
        key (str): The environment variable key.
        default (str, optional): Default value if the key is not found. Defaults to None.
        required (bool, optional): If True, raise error when variable is missing.

    Returns:
        str: The environment variable value or default.

    Raises:
        EnvironmentError: If `required=True` and the key is missing.
    """
    value = os.getenv(key, default)
    if required and value is None:
        raise EnvironmentError(f"Missing required environment variable: {key}")
    return value
