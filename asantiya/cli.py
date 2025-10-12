from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from asantiya import __app_name__, __version__
from asantiya.accessories import app as accessories_app
from asantiya.app import app as asantiya_app
from asantiya.utils.config import DocumentedConfigGenerator
from asantiya.schemas.models import ConfigurationError
from asantiya.docker_manager import DockerManager
from asantiya.logger import DeploymentLogger, setup_logging
from pathlib import Path
from typing import Optional
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, Prompt
from rich.table import Table

# Create console for rich output
console = Console()

app = typer.Typer(
    no_args_is_help=True,
    rich_markup_mode="rich",
    help=f"[bold blue]{__app_name__}[/bold blue] - Docker deployment CLI tool for local and remote environments",
)

# Add commands directly
@app.command("init")
def init_cmd(
    output: Optional[str] = typer.Option(
        "deploy.yaml",
        "--output",
        "-o",
        help="Output file path for configuration.",
    ),
    interactive: bool = typer.Option(
        True,
        "--interactive/--no-interactive",
        help="Run in interactive mode to customize configuration.",
    ),
    template: Optional[str] = typer.Option(
        None,
        "--template",
        "-t",
        help="Configuration template to use (basic, full, minimal).",
    ),
) -> None:
    """🎯 Initialize Asantiya configuration files"""
    try:
        output_path = Path(output)
        
        # Check if file already exists
        if output_path.exists():
            if not Confirm.ask(f"Configuration file '{output}' already exists. Overwrite?"):
                console.print("[yellow]Configuration creation cancelled.[/yellow]")
                return
        
        # Show banner
        _show_banner()
        
        # Initialize configuration
        console.print(Panel(
            "[bold blue]🎯 Initializing Asantiya Configuration[/bold blue]\n"
            "Setting up your deployment configuration...",
            border_style="blue"
        ))
        
        # Get template configuration
        if template:
            config_data = _get_template_config(template)
        else:
            config_data = _get_template_config("basic")
        
        # Interactive customization if requested
        if interactive:
            config_data = _interactive_config_setup(config_data)
        
        # Generate configuration
        generator = DocumentedConfigGenerator()
        yaml_content = generator.generate_documented_yaml(output_path, **config_data)
        
        # Show success message
        console.print(Panel(
            f"[bold green]✅ Configuration Created Successfully![/bold green]\n"
            f"Configuration file:\n{output_path.absolute()}\n\n"
            f"[bold]Next Steps:[/bold]\n"
            f"1. Review and customize the configuration file\n"
            f"2. Set up environment variables if needed\n"
            f"3. Run asantiya deploy to deploy your application",
            border_style="green"
        ))
        
        # Show configuration summary
        _show_config_summary(config_data)
        
        console.print(f"[green]Configuration initialized successfully: {output}[/green]")
        
    except Exception as e:
        console.print(f"[red]Error initializing configuration: {e}[/red]")
        raise typer.Exit(1)

@app.command("deploy")
def deploy_cmd(
    config: Optional[str] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to configuration file (default: deploy.yaml).",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Force deployment without confirmation.",
    ),
    skip_build: bool = typer.Option(
        False,
        "--skip-build",
        help="Skip building the Docker image.",
    ),
    skip_accessories: bool = typer.Option(
        False,
        "--skip-accessories",
        help="Skip starting accessory containers.",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-V",
        help="Enable verbose output.",
    ),
) -> None:
    """🚀 Build and deploy your application"""
    try:
        # Use global config if not provided
        config_file = config or app.ctx.get("config") or "deploy.yaml"
        config_path = Path(config_file)
        
        # Check if config file exists
        if not config_path.exists():
            console.print(f"[red]Configuration file not found: {config_file}[/red]")
            console.print("[yellow]Run 'asantiya init' to create a configuration file.[/yellow]")
            raise typer.Exit(1)
        
        # Show banner
        _show_banner()
        
        # Show configuration summary
        _show_deploy_config_summary(config_path)
        
        # Confirm deployment
        if not force:
            if not Confirm.ask("Proceed with deployment?"):
                console.print("[yellow]Deployment cancelled.[/yellow]")
                return
        
        # Start deployment
        with DeploymentLogger("Deployment") as logger:
            logger.start()
            
            try:
                # Initialize Docker manager
                docker_manager = DockerManager(str(config_path))
                
                # Connect to Docker
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console,
                ) as progress:
                    task = progress.add_task("Connecting to Docker...", total=None)
                    docker_manager.connect()
                    progress.update(task, description="✅ Connected to Docker")
                
                # Build image if not skipped
                if not skip_build:
                    with Progress(
                        SpinnerColumn(),
                        TextColumn("[progress.description]{task.description}"),
                        console=console,
                    ) as progress:
                        task = progress.add_task("Building Docker image...", total=None)
                        docker_manager.build_image_from_dockerfile()
                        progress.update(task, description="✅ Docker image built")
                
                # Start accessories if not skipped
                if not skip_accessories:
                    with Progress(
                        SpinnerColumn(),
                        TextColumn("[progress.description]{task.description}"),
                        console=console,
                    ) as progress:
                        task = progress.add_task("Starting accessory containers...", total=None)
                        docker_manager.start_accessories()
                        progress.update(task, description="✅ Accessory containers started")
                
                # Start main application
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console,
                ) as progress:
                    task = progress.add_task("Starting main application...", total=None)
                    docker_manager.start_app()
                    progress.update(task, description="✅ Main application started")
                
                logger.complete()
                console.print(Panel(
                    "[bold green]🎉 Deployment completed successfully![/bold green]\n"
                    "Your application is now running.",
                    border_style="green"
                ))
                
            except Exception as e:
                logger.fail(str(e))
                console.print(f"[red]Deployment failed: {e}[/red]")
                raise typer.Exit(1)
                
    except Exception as e:
        console.print(f"[red]Error during deployment: {e}[/red]")
        raise typer.Exit(1)

# Add subcommands for more complex functionality
app.add_typer(
    accessories_app,
    name="accessory",
    help="Manage accessory containers (databases, caches, etc.)",
)
app.add_typer(asantiya_app, name="app", help="Manage main application container")


def _version_callback(value: bool) -> None:
    """Show version information."""
    if value:
        version_text = Text(f"{__app_name__} v{__version__}", style="bold green")
        console.print(Panel(version_text, title="Version", border_style="green"))
        raise typer.Exit()


def _show_banner() -> None:
    """Show application banner."""
    banner_text = Text.assemble(
        ("Asantiya", "bold blue"),
        " - ",
        ("اسانتیا", "bold cyan"),
        "\n",
        ("Docker deployment made easy", "italic dim"),
    )
    console.print(Panel(banner_text, border_style="blue"))


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
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-V",
        help="Enable verbose output.",
    ),
    config: Optional[str] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to configuration file (default: deploy.yaml).",
    ),
) -> None:
    """
    🚀 Asantiya - Docker deployment CLI tool

    Deploy applications to servers using a single configuration file.
    Automates deployment steps such as building, packaging, uploading, and starting services.

    [bold]Quick Start:[/bold]

    1. [cyan]asantiya init[/cyan] - Create configuration file
    2. [cyan]asantiya deploy[/cyan] - Deploy your application
    3. [cyan]asantiya app start[/cyan] - Start your application
    4. [cyan]asantiya accessory up[/cyan] - Start accessory services

    [bold]Examples:[/bold]

    • [dim]asantiya init --help[/dim] - See init options
    • [dim]asantiya deploy --env production[/dim] - Deploy to production
    • [dim]asantiya accessory logs db[/dim] - View database logs
    • [dim]asantiya app restart[/dim] - Restart main application

    For more information, visit: [link]https://github.com/shahid-0/asantiya[/link]
    """
    if not version:
        _show_banner()

    # Store global options for use by subcommands
    app.ctx = {"verbose": verbose, "config": config}


def _get_template_config(template: str) -> dict:
    """Get configuration template based on type."""
    templates = {
        "basic": {
            "service": "my-app",
            "image": "my-app:latest",
            "app_ports": "8080:80",
            "builder": {
                "arch": "amd64",
                "local": True,
            },
            "accessories": {
                "db": {
                    "service": "my-app-db",
                    "image": "postgres:13",
                    "ports": "5432:5432",
                    "env": {"POSTGRES_PASSWORD": "change-me"},
                    "volumes": ["db_data:/var/lib/postgresql/data"],
                    "network": "my-app-network",
                }
            }
        },
        "full": {
            "service": "asantiya",
            "image": "${HOST_USER}/asantiya",
            "app_ports": "8020:8020",
            "builder": {
                "arch": "arm64",
                "remote": "ssh://${HOST_USER}@${SERVER}",
                "local": False,
            },
            "accessories": {
                "db": {
                    "service": "asantiya-db",
                    "image": "postgres:13",
                    "ports": "8069:8069",
                    "env": {"POSTGRES_PASSWORD": "some-strong-password-for-postgressql"},
                    "volumes": ["myvolume:/var/lib/postgresql/data"],
                    "network": "asantiya-network",
                    "options": {"restart": "always"},
                }
            }
        },
        "minimal": {
            "service": "simple-app",
            "image": "simple-app:latest",
            "app_ports": "3000:3000",
            "builder": {
                "arch": "amd64",
                "local": True,
            }
        }
    }
    return templates.get(template, templates["basic"])


def _interactive_config_setup(config_data: dict) -> dict:
    """Interactive configuration setup."""
    console.print("\n[bold blue]🔧 Interactive Configuration Setup[/bold blue]")
    
    # Service name
    service = Prompt.ask("Service name", default=config_data.get("service", "my-app"))
    config_data["service"] = service
    
    # Image name
    image = Prompt.ask("Docker image name", default=config_data.get("image", f"{service}:latest"))
    config_data["image"] = image
    
    # Ports
    ports = Prompt.ask("Port mapping (host:container)", default=config_data.get("app_ports", "8080:80"))
    config_data["app_ports"] = ports
    
    # Architecture
    arch = Prompt.ask("Target architecture", choices=["amd64", "arm64", "armv7"], default=config_data.get("builder", {}).get("arch", "amd64"))
    config_data.setdefault("builder", {})["arch"] = arch
    
    # Build mode
    local_build = Confirm.ask("Build locally?", default=config_data.get("builder", {}).get("local", True))
    config_data.setdefault("builder", {})["local"] = local_build
    
    if not local_build:
        remote_url = Prompt.ask("Remote build server (SSH URL)", default=config_data.get("builder", {}).get("remote", "ssh://user@server.com"))
        config_data.setdefault("builder", {})["remote"] = remote_url
    
    return config_data


def _show_config_summary(config_data: dict):
    """Show configuration summary table."""
    table = Table(title="Configuration Summary")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Service", config_data.get("service", "N/A"))
    table.add_row("Image", config_data.get("image", "N/A"))
    table.add_row("Ports", config_data.get("app_ports", "N/A"))
    table.add_row("Architecture", config_data.get("builder", {}).get("arch", "N/A"))
    table.add_row("Build Mode", "Local" if config_data.get("builder", {}).get("local", True) else "Remote")
    table.add_row("Accessories", str(len(config_data.get("accessories", {}))))
    
    console.print(table)


def _show_deploy_config_summary(config_path: Path):
    """Show deployment configuration summary."""
    try:
        from asantiya.utils.config import load_config
        config = load_config(str(config_path))
        
        table = Table(title="Deployment Configuration")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Service", config.service)
        table.add_row("Image", config.image)
        table.add_row("Ports", config.app_ports)
        table.add_row("Architecture", config.builder.arch)
        table.add_row("Build Mode", "Local" if config.builder.local else "Remote")
        table.add_row("Accessories", str(len(config.accessories or {})))
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[yellow]Could not load configuration: {e}[/yellow]")
