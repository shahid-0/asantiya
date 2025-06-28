import typer
from asantiya.docker_manager import DockerManager

from asantiya.logger import setup_logging

_logger = setup_logging()

app = typer.Typer()

@app.command(help="List containers")
def ls() -> None:
    docker_manager = DockerManager()
    
    try:
        docker_manager.connect()
            
        docker_manager.list_configured_containers()
            
    except Exception as e:
        _logger.exception(f"Unexpected error during listing the containers: {e}")