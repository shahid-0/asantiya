from typing import Optional
import typer

from asantiya.accessories import app as accessories_app
from asantiya.app import app as asantiya_app
from asantiya.deploy import app as deploy_app
from asantiya.init import app as init_app

from asantiya import __app_name__, __version__

app = typer.Typer(no_args_is_help=True)
app.add_typer(accessories_app, name="accessory")
app.add_typer(asantiya_app, name="app")
app.add_typer(deploy_app)
app.add_typer(init_app)

def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"{__app_name__} v{__version__}")
        raise typer.Exit()

@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        help="Show the application's version and exit.",
        callback=_version_callback,
        is_eager=True,
    ),
) -> None:
    return