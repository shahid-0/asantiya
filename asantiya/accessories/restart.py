import typer
from pathlib import Path
from typing import Annotated, List
from asantiya.docker_manager import DockerManager
from asantiya.utils.config import load_config
from asantiya.logger import setup_logging
from asantiya.utils.docker import setup_connection

_logger = setup_logging()

app = typer.Typer()

@app.command(help="Restart single or list of accessories")
def restart(
        names: Annotated[List[str], typer.Option(help="Single or list of accessories name")] = None,
        force: Annotated[bool, typer.Option("--force", "-f", help="If True, forces restart even if container isn't running", is_flag=True, show_default="False")] = False
    ) -> None:
    docker_manager = DockerManager()

    try:
        setup_connection(docker_manager)

        if not names:
            names = docker_manager.list_accessory_services(docker_manager.config.accessories) 
        docker_manager.restart_accessories(names=names, force_restart=force)

    except Exception as e:
        _logger.exception(f"❌ Unexpected error during restarting containers: {e}")