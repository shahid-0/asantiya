import typer
from pathlib import Path
from asantiya.docker_manager import DockerManager
from asantiya.utils.config import load_config
from asantiya.utils.docker import setup_connection
from asantiya.logger import setup_logging

_logger = setup_logging()

app = typer.Typer()

@app.command(help="Start accessories/container")
def up() -> None:
    config = load_config(Path().cwd() / "deploy.yaml")
    docker_manager = DockerManager()
    
    try:
        setup_connection(config, docker_manager)
            
        results = docker_manager.create_all_accessories(config.accessories)
        _logger.info(f"Successfully deployed in order: {', '.join(results.keys())}")
            
    except Exception as e:
        _logger.exception(f"Unexpected error during deploying the app: {e}")