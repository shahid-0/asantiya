import typer
from asantiya.docker_manager import DockerManager

from asantiya.logger import setup_logging

_logger = setup_logging()

app = typer.Typer()

@app.command(help="Start accessories/container")
def up() -> None:
    docker_manager = DockerManager()
    
    try:
        docker_manager.connect()
            
        results = docker_manager.create_all_accessories()
        _logger.info(f"Successfully deployed in order: {', '.join(results.keys())}")
            
    except Exception as e:
        _logger.exception(f"Unexpected error during deploying the app: {e}")