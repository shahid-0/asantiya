import typer
from asantiya.docker_manager import DockerManager
from asantiya.logger import setup_logging
from asantiya.utils.docker import setup_connection

_logger = setup_logging()

app = typer.Typer()


@app.command(help="Stop app container")
def stop() -> None:
    docker_manager = DockerManager()

    try:
        setup_connection(docker_manager)
        docker_manager.stop_app_container()
        name = docker_manager.list_accessory_services() 
        docker_manager.stop_accessories(name)

    except Exception as e:
        _logger.exception(f"❌ Unexpected error during stopping containers: {e}")
