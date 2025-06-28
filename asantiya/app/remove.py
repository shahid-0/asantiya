import typer
from asantiya.docker_manager import DockerManager
from asantiya.logger import setup_logging
from asantiya.utils.docker import setup_connection

_logger = setup_logging()

app = typer.Typer()


@app.command(help="Remove app containers and images")
def remove() -> None:
    docker_manager = DockerManager()

    try:
        setup_connection(docker_manager)
        docker_manager.remove_app()

    except Exception as e:
        _logger.exception(f"❌ Unexpected error during deleting the app: {e}")