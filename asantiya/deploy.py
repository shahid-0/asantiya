import typer
from asantiya.docker_manager import DockerManager
from asantiya.logger import setup_logging


_logger = setup_logging()

app = typer.Typer()


@app.command(help="Build and deploy your app")
def deploy() -> None:
    docker_manager = DockerManager()
    
    try:
        docker_manager.connect()
        docker_manager.deploy_app()

    except Exception as e:
        _logger.exception(f"❌ Unexpected error during deploying app: {e}")
