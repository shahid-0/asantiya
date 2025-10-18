from pathlib import Path

import typer

from asantiya.docker_manager import DockerManager
from asantiya.logger import setup_logging

_logger = setup_logging()

app = typer.Typer()


@app.command(help="Start accessories/container")
def up(
    config: str = typer.Option(
        "deploy.yaml",
        "--config",
        "-c",
        help="Path to configuration file",
    ),
) -> None:
    config_path = Path(config)
    docker_manager = DockerManager(config_path)

    try:
        docker_manager.connect()

        results = docker_manager.create_all_accessories()
        _logger.info(f"Successfully deployed in order: {', '.join(results.keys())}")

    except Exception as e:
        _logger.exception(f"Unexpected error during deploying the app: {e}")
