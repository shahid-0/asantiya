import typer
from pathlib import Path
from asantiya.logger import setup_logging
from asantiya.utils.config import DocumentedConfigGenerator

_logger = setup_logging()

app = typer.Typer()


@app.command(help="Creates the files needed to deploy your application with asantiya")
def init() -> None:
    try:
        DocumentedConfigGenerator.generate_documented_yaml(
            output_path=Path("deploy.yaml"),
            builder={
                "# Build machine specifications": None,
                "arch": "amd64",
                "remote": "ssh://build@ci.example.com",
                "local": False
            },
            accessories={
                "db": {
                    "# postgres service": None,
                    "service": "asantiya-db",
                    "image": "postgres:13",
                    "ports": "8069:8069",
                    "options": { "restart": "always" },
                    "env": { "POSTGRES_PASSWORD": "some-strong-password-for-postgressql"},
                    "volumes": [ "myvolume:/var/lib/postgresql/data" ],
                    "network": "asantiya"
                }
            }
        )
        _logger.info("Asantiya initialize successfully")

    except Exception as e:
        _logger.exception(f"❌ Unexpected error during stopping containers: {e}")
