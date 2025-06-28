import typer
from typing import Annotated
from asantiya.docker_manager import DockerManager
from asantiya.logger import setup_logging


_logger = setup_logging()

app = typer.Typer()


@app.command(help="Stop accessories/containers")
def down(
        name: Annotated[str, typer.Argument(help="Single or list of accessories name")] = "all",
        volumes: Annotated[bool, typer.Option("--volumes", "-v", help='Remove named volumes declared in the "volumes" section of the Yaml file and anonymous volumes attached to containers', is_flag=True, show_default="False")] = False
    ) -> None:
    docker_manager = DockerManager()

    try:
        docker_manager.connect()

        if name == "all":
            name = docker_manager.list_accessory_services() 
        docker_manager.stop_accessories(name, volumes)

    except Exception as e:
        _logger.exception(f"❌ Unexpected error during stopping containers: {e}")
