import typer
from asantiya.docker_manager import DockerManager
from asantiya.logger import setup_logging


_logger = setup_logging()

app = typer.Typer()


@app.command(help="Stop app container")
def stop() -> None:
    docker_manager = DockerManager()

    try:
        docker_manager.connect()
        docker_manager.stop_app_container()
        name = docker_manager.list_accessory_services() 
        docker_manager.stop_accessories(name)

    except Exception as e:
        _logger.exception(f"❌ Unexpected error during stopping containers: {e}")
