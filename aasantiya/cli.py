"""This module provides the aasantiya CLI."""
# rptodo/cli.py

from typing import Optional
import typer

from pathlib import Path

from aasantiya import __app_name__, __version__

app = typer.Typer(no_args_is_help=True)

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
    )
) -> None:
    return



@app.command(help="Initialize aasantiya")
def init():
    """
    Initialize the task manager by creating a configuration directory and file.
    
    Creates:
    - 'aasantiya' directory in current path
    - 'config.yaml' inside the directory
    """
    base_dir =  Path("aasantiya")
    config_file = base_dir / "config.yaml"
    
    try:
        base_dir.mkdir(exist_ok=True)
        config_file.touch(exist_ok=True)
        
        typer.echo(f"✓ Created directory: '{base_dir}/'")
        typer.echo(f"✓ Created config file: '{config_file}'")
        typer.echo("\nTask manager initialized successfully!")
    except Exception as e:
        typer.echo(f"Error: {str(e)}", err=True)
        raise typer.Exit(code=1)