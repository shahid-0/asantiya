import typer
from asantiya.docker_manager import DockerManager
from asantiya.logger import setup_logging
from asantiya.utils.docker import setup_connection

_logger = setup_logging()

app = typer.Typer()


@app.command(help="Build and deploy your app")
def deploy() -> None:
    docker_manager = DockerManager()
    
    try:
        setup_connection(docker_manager)
        results = docker_manager.create_all_accessories()
        _logger.info(f"Successfully deployed in order: {', '.join(results.keys())}")
        docker_manager.deploy_app()

    except Exception as e:
        _logger.exception(f"❌ Unexpected error during deploying app: {e}")
