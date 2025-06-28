import typer
from typing import Annotated
from asantiya.docker_manager import DockerManager

from asantiya.logger import setup_logging

_logger = setup_logging()

app = typer.Typer()

@app.command(help="Show accessory logs")
def logs(
        name: Annotated[str, typer.Argument(help="Name of the container (must exist in config)")],
        follow: Annotated[bool, typer.Option("--follow", "-f", help="Keep streaming new log output (like tail -f)", is_flag=True, show_default="False")] = False,
        tail: Annotated[int, typer.Option("--tail", "-t", help="Number of lines to show from the end of logs")] = 100
    ) -> None:
    docker_manager = DockerManager()
    
    try:
        docker_manager.connect()
            
        docker_manager.show_accessory_logs(name, follow, tail)
            
    except Exception as e:
        _logger.exception(f"Unexpected error during showing accessory logs: {e}")