import typer
from pathlib import Path
from asantiya.ssh_manager import SSHManager
from asantiya.docker_manager import DockerManager
from asantiya.tools.config import load_config, _is_local
from asantiya.logger import setup_logging

_logger = setup_logging()

app = typer.Typer()

@app.command(help="Deploy odoo container")
def up() -> None:
    config = load_config(Path().cwd() / "deploy.yaml")
    is_local = _is_local(config)
    
    if not is_local:
        if not getattr(config.host, "key", None) and not getattr(config.host, "password", None):
            _logger.error("❌ You must provide either --key or --password unless using host: False.")
            raise typer.Exit(code=1)
    
    sshmanager = SSHManager()
    docker_manager = DockerManager()
    
    try:
        if not is_local:
            _logger.info("🔒 Connecting remotely via SSHasantiya..")
            sshmanager.connect(config.server, config.host.user, config.host.key, config.host.password)

            _logger.info("🧪 Checking Docker setup remotely...")
            docker_manager.check_docker_version(sshmanager.ssh)
            docker_manager.connect(host=config.server, user=config.host.user)
        else:
            _logger.info("💻 Running locally...")
            docker_manager.check_docker_version()
            docker_manager.connect(local=True)
            
        results = docker_manager.create_all_accessories(config.accessories)
        _logger.info(f"Successfully deployed in order: {', '.join(results.keys())}")
            
    except Exception as e:
        _logger.exception(f"Unexpected error during deploying the app: {e}")
    finally:
        sshmanager.close()