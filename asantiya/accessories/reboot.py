import typer
from typing import Annotated
from asantiya.docker_manager import DockerManager
from asantiya.logger import setup_logging


_logger = setup_logging()

app = typer.Typer()


@app.command(help="Reboot existing accessory on host (stop container, remove container, start new container; use NAME=all to boot all accessories)")
def reboot(
        name: Annotated[str, typer.Argument(help="Accessory name (use all to boot all accessories)")],
        force: Annotated[bool, typer.Option("--force", "-f", help="Continue after errors", is_flag=True, show_default="False")] = False,
    ) -> None:
    docker_manager = DockerManager()

    try:
        docker_manager.connect()
        if name and name != "all":
            result = docker_manager.reboot_single_accessory(name)
            if result is not True:
                typer.echo(f"Error: {result}", err=True)
                raise typer.Exit(1)
        else:
            docker_manager.reboot_all_accessories(force=force)

    except Exception as e:
        _logger.exception(f"❌ Unexpected error during rebooting containers: {e}")
