import typer
from typing import Annotated, List
from pathlib import Path
from asantiya.docker_manager import DockerManager
from asantiya.utils.config import load_config
from asantiya.logger import setup_logging
from asantiya.utils.docker import setup_connection

_logger = setup_logging()

app = typer.Typer()


@app.command(help="Stop accessories/containers")
def down(
        accessories: Annotated[List[str], typer.Option(help="Single or list of accessories name")] = None,
        volumes: Annotated[bool, typer.Option("--volumes", "-v", help='Remove named volumes declared in the "volumes" section of the Yaml file and anonymous volumes attached to containers', is_flag=True, show_default="False")] = False
    ) -> None:
    config = load_config(Path().cwd() / "deploy.yaml")
    docker_manager = DockerManager()

    try:
        setup_connection(config, docker_manager)

        if not accessories:
            accessories = docker_manager.list_accessory_services(config.accessories) 
        docker_manager.stop_accessories(accessories, volumes)

    except Exception as e:
        _logger.exception(f"❌ Unexpected error during stopping containers: {e}")
