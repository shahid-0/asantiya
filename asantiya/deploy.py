import typer
from typing import Annotated, List
from pathlib import Path
from asantiya.docker_manager import DockerManager
from asantiya.utils.config import load_config
from asantiya.logger import setup_logging
from asantiya.utils.docker import setup_connection

_logger = setup_logging()

app = typer.Typer()


@app.command(help="Build and deploy your app")
def deploy() -> None:
    docker_manager = DockerManager()
    
    try:
        setup_connection(docker_manager)

        docker_manager.build_image_from_dockerfile(docker_manager.config.builder.dockerfile, docker_manager.config.image)

    except Exception as e:
        _logger.exception(f"❌ Unexpected error during deploying app: {e}")
