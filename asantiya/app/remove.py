import typer
from asantiya.docker_manager import DockerManager
from asantiya.logger import setup_logging


_logger = setup_logging()

app = typer.Typer()


@app.command(help="Remove app containers and images")
def remove() -> None:
    docker_manager = DockerManager()

    try:
        docker_manager.connect()
        docker_manager.remove_app()

    except Exception as e:
        _logger.exception(f"❌ Unexpected error during deleting the app: {e}")