import typer
from typing import Annotated, List
from pathlib import Path
from asantiya.ssh_manager import SSHManager
from asantiya.docker_manager import DockerManager
from asantiya.tools.config import load_config, _is_local
from asantiya.logger import setup_logging

_logger = setup_logging()

app = typer.Typer()


@app.command(help="Stop Odoo containers")
def down(
        accessories: Annotated[List[str], typer.Option(help="Single or list of accessories name")] = None,
        volumes: Annotated[bool, typer.Option("--volumes", "-v", help='Remove named volumes declared in the "volumes" section of the Yaml file and anonymous volumes attached to containers', is_flag=True, show_default="False")] = False
    ) -> None:
    config = load_config(Path().cwd() / "deploy.yaml")

    sshmanager = SSHManager()
    docker_manager = DockerManager()

    is_local = _is_local(config)

    if not is_local:
        if not getattr(config.host, "key", None) and not getattr(config.host, "password", None):
            _logger.error("❌ You must provide either --key or --password unless using --local.")
            raise typer.Exit(code=1)

    try:
        if not is_local:
            _logger.info("🔒 Connecting remotely via SSH...")
            sshmanager.connect(config.server, config.host.user, config.host.key, config.host.password)

            _logger.info("🧪 Checking Docker setup remotely...")
            docker_manager.check_docker_version(sshmanager.ssh)
            docker_manager.connect(host=config.server, user=config.host.user)
        else:
            _logger.info("💻 Running locally...")
            docker_manager.check_docker_version()
            docker_manager.connect(local=True)

        if not accessories:
            accessories = docker_manager.list_accessory_services(config.accessories) 
        docker_manager.stop_accessories(accessories, volumes)

    except Exception as e:
        _logger.exception(f"❌ Unexpected error during stopping containers: {e}")
    finally:
        sshmanager.close()
