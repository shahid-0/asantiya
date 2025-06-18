import docker
import subprocess
from typing import Annotated, List, Optional, Dict, Union
import docker.errors
from rich.progress import (
    Progress,  
    TextColumn,
    BarColumn,
    TransferSpeedColumn,
)
import paramiko
from asantiya.ssh_manager import SSHManager
from asantiya.schemas.models import AccessoryConfig
from asantiya.utils.docker import ensure_network, sort_by_dependencies
from asantiya.logger import setup_logging
from asantiya.schemas.models import HostConfig

_logger = setup_logging()

class DockerManager:
    
    def __init__(self):
        self.docker = docker
        self.docker_client = None
        
            
    def connect(self, host: str = None, user: str = None, local: bool = False) -> docker.DockerClient:
        try:
            if not local and host and user:
                self.docker_client = self.docker.DockerClient(base_url=f"ssh://{user}@{host}")
            else:
                self.docker_client = self.docker.from_env()
            # Test the connection
            self.docker_client.ping()
            _logger.info("Successfully connected to Docker daemon.")
            return self.docker_client
        except docker.errors.DockerException as e:
            raise ConnectionError(f"Failed to connect to Docker: {str(e)}")
        
            
    def check_docker_version(self) -> str:
        if not self.docker_client:
            _logger.error("❌ Docker client is not connected. Please call connect() first.")
            raise RuntimeError("Docker client not connected. Call connect() before checking the version.")

        try:
            version_info = self.docker_client.version()
            version = version_info.get("Version", "Unknown")
            _logger.info(f"🐳 Docker version: {version}")
            return version

        except docker.errors.DockerException as e:
            _logger.error(f"❌ Failed to retrieve Docker version: {str(e)}")
            raise ConnectionError("Could not connect to Docker daemon.")
        except Exception:
            _logger.exception("❌ Unexpected error while checking Docker version.")
            raise

        
    def pull_images(self, images: Annotated[List[str], "List of docker images"]):
        if not images or not isinstance(images, list) or not all(isinstance(img, str) and img.strip() for img in images):
            raise ValueError("You must provide a non-empty list of valid Docker image names.")
        
        with Progress(
            TextColumn("[bold]{task.description}"),
            BarColumn(),
            TransferSpeedColumn(),
        ) as progress:
            
            # Task 1: Pulling Images
            pull_task = progress.console.print("[cyan]Checking images...")
            
            for img in images:
                progress.console.print(f"  → Checking {img}")
                
                try:
                    # Check if image exists locally
                    self.docker_client.images.get(img)
                    progress.console.print(
                        f"    ✓ {img} already exists", 
                        style="green dim"
                    )
                    # progress.advance(pull_task)
                    continue
                except docker.errors.ImageNotFound:
                    for line in self.docker_client.api.pull(img, stream=True, decode=True):
                        if 'progressDetail' in line and line['progressDetail'].get('total'):
                            current = line['progressDetail']['current']
                            total = line['progressDetail']['total']
                            progress.update(
                                pull_task,
                                completed=int((current / total) * 100),
                                description=f"[green]Pulling {img}"
                            )
                        
                        # Optional: Show layer completion messages
                        if line.get('status') == 'Download complete':
                            progress.console.print(
                                f"    [dim]{line.get('id', '')[:12]}... {line['status']}",
                                style="dim"
                            )
                    
                    progress.console.print(
                        f"    ✓ {img} pulled successfully", 
                        style="green dim"
                    )
                    
    def create_accessory(self, config: AccessoryConfig) -> docker.models.containers.Container:
        """Create a single accessory container"""
        try:
            # Check if container already exists
            try:
                existing_container = self.docker_client.containers.get(config.service)
                
                if existing_container.status == "running":
                    _logger.info(f"Container {config.service} is already running")
                    return existing_container
                    
                _logger.info(f"Found stopped container {config.service} - starting it")
                existing_container.start()
                return existing_container
                
            except docker.errors.NotFound:
                pass 
            
            # Ensure network exists
            ensure_network(self.docker_client, config.network)
            
            # Pull image if needed
            self.pull_images([config.image])
            
            # Prepare container config
            host_port, container_port = config.ports.split(':')
            
            container = self.docker_client.containers.run(
                image=config.image,
                name=config.service,
                environment=config.env,
                ports={f"{container_port}/tcp": int(host_port)},
                volumes=self._parse_volumes(config.volumes),
                network=config.network,
                detach=True,
                restart_policy={"Name": config.options.restart},
                labels={"managed_by": "odooops"}
            )
            
            return container
            
        except docker.errors.APIError as e:
            raise RuntimeError(f"Failed to create {config.service}: {e.explanation}")
        
    def list_accessory_services(self, config: Dict[str, AccessoryConfig]) -> List[str]:
        """
        List all service names from the accessories configuration.
        
        Args:
            config: The loaded AppConfig containing accessories configuration
        
        Returns:
            A list of service names
            Example:
                ["redis-service", "database-service"]
        """
        if not config:
            return []
        
        return [accessory.service for accessory in config.values()]
        
    def stop_accessory(
        self, 
        name: str, 
        force: bool = False, 
        raise_errors: bool = False
    ) -> None:
        """
        Remove an accessory container with proper cleanup
        
        Args:
            name: Name of the container to remove
            force: If True, removes running containers (with SIGKILL)
            raise_errors: If True, raises exceptions on failures
        
        Raises:
            RuntimeError: If removal fails and raise_errors=True
            ValueError: If container doesn't exist and raise_errors=True
        """
        try:
            # Input validation
            if not name or not isinstance(name, str):
                msg = f"Invalid container name: {name}"
                _logger.error(msg)
                if raise_errors:
                    raise ValueError(msg)
                return

            try:
                container = self.docker_client.containers.get(name)
                
                if container.status == "running":
                    container.stop(timeout=5)  # More graceful than kill()
                    _logger.info(f"Successfully stopped container: {name}")
                    
                if force:
                    container.remove(v=force)  # v=True removes associated volumes
                    _logger.info(f"Successfully removed container: {name}")
                
            except docker.errors.NotFound:
                msg = f"Container {name} not found"
                _logger.error(msg)
                if raise_errors:
                    raise ValueError(msg)
            except docker.errors.APIError as e:
                msg = f"Failed to remove {name}: {e.explanation}"
                _logger.error(msg)
                if raise_errors:
                    raise RuntimeError(msg)

        except Exception as e:
            msg = f"Unexpected error removing container {name}: {str(e)}"
            _logger.error(msg)
            if raise_errors:
                raise RuntimeError(msg)
            
    def stop_accessories(
        self,
        names: Union[str, List[str]],
        force: bool = False,
        raise_errors: bool = False
    ) -> Dict[str, Union[bool, str]]:
        """Remove multiple containers with status reporting"""
        names = [name] if isinstance(names, str) else names
        
        results = {}
        for name in names:
            try:
                self.stop_accessory(name, force, raise_errors)
                results[name] = True
            except Exception as e:
                results[name] = str(e)
        return results
                    
    def _parse_volumes(self, volumes: List[str]) -> Dict[str, Dict]:
        """Convert volume strings to Docker format"""
        result = {}
        for vol in volumes:
            parts = vol.split(':')
            if len(parts) == 2:
                host, container = parts
                mode = 'rw'
            elif len(parts) == 3:
                host, container, mode = parts
            else:
                raise ValueError(f"Invalid volume format: {vol}")
            
            result[host] = {'bind': container, 'mode': mode}
        return result
    
    def create_all_accessories(self, configs: Dict[str, AccessoryConfig]) -> Dict[str, str]:
        """Create containers in dependency order"""
        results = {}
        ordered_services = sort_by_dependencies(configs)

        for service_name in ordered_services:
            config = configs[service_name]
            try:
                container = self.create_accessory(config)
                results[service_name] = container.id
                print(f"Started {service_name} ({container.id[:12]})")
            except Exception as e:
                raise RuntimeError(
                    f"Failed to start {service_name}. Aborting. Error: {str(e)}"
                )
        
        return results
    
    def restart_accessories(
        self,
        names: Union[str, List[str]],
        timeout: int = 10,
        force_restart: bool = False,
        raise_errors: bool = False
    ) -> Dict[str, Union[bool, str]]:
        """
        Restart one or multiple accessory containers with status reporting
        
        Args:
            names: Container name(s) to restart (str or List[str])
            timeout: Timeout in seconds for stopping containers
            force_restart: If True, forces restart even if container isn't running
            raise_errors: If True, raises exceptions on failures
        
        Returns:
            Dictionary with restart status for each container:
            {
                "container1": True,  # Success
                "container2": "Error message",  # Failure
                ...
            }
        
        Example:
            >>> restart_accessories(["redis", "postgres"])
            {'redis': True, 'postgres': 'Container not found'}
        """
        if isinstance(names, str):
            names = [names]
        
        results = {}
        
        for name in names:
            try:
                if not name or not isinstance(name, str):
                    msg = f"Invalid container name: {name}"
                    _logger.error(msg)
                    results[name] = msg
                    continue
                
                container = self.docker_client.containers.get(name)
                
                if container.status != "running" and not force_restart:
                    msg = f"Container {name} is not running (status: {container.status}). Use --force or -f to force restart"
                    _logger.warning(msg)
                    results[name] = msg
                    continue
                
                container.restart(timeout=timeout)
                _logger.info(f"Successfully restarted container: {name}")
                results[name] = True
                
            except docker.errors.NotFound:
                msg = f"Container {name} not found"
                _logger.error(msg)
                results[name] = msg
                if raise_errors:
                    raise ValueError(msg)
            except docker.errors.APIError as e:
                msg = f"Failed to restart {name}: {e.explanation}"
                _logger.error(msg)
                results[name] = msg
                if raise_errors:
                    raise RuntimeError(msg)
            except Exception as e:
                msg = f"Unexpected error restarting {name}: {str(e)}"
                _logger.error(msg)
                results[name] = msg
                if raise_errors:
                    raise RuntimeError(msg)
        
        return results
        
def setup_docker_environment(ssh_client: SSHManager):
    # Check Docker installation
    cmds = ["docker", "--version"]
    _, output = ssh_client.execute_commands(cmds)
    if "Docker version" not in output:
        raise RuntimeError("Docker not installed on target server")
    
    # Create required directories
    ssh_client.execute_commands("mkdir -p /opt/odoo/{addons,data}")


def deploy_odoo_container(config):
    # Connect to Docker daemon via SSH transport
    docker_client = docker.DockerClient(
        base_url=f"ssh://{config['user']}@{config['host']}"
    )
    
    # Pull images
    docker_client.images.pull(f"odoo:{config['odoo_version']}")
    docker_client.images.pull("postgres:13")

    # Create network
    network = docker_client.networks.create("odoo-network", driver="bridge")

    # Start PostgreSQL container
    db_container = docker_client.containers.run(
        "postgres:13",
        name="odoo-db",
        environment={
            "POSTGRES_DB": "odoo",
            "POSTGRES_USER": config["db_user"],
            "POSTGRES_PASSWORD": config["db_password"]
        },
        network="odoo-network",
        detach=True,
        restart_policy={"Name": "always"}
    )

    # Start Odoo container
    odoo_container = docker_client.containers.run(
        f"odoo:{config['odoo_version']}",
        name="odoo-app",
        volumes={
            config['addons_path']: {'bind': '/mnt/extra-addons', 'mode': 'rw'},
            '/opt/odoo/data': {'bind': '/var/lib/odoo', 'mode': 'rw'}
        },
        ports={'8069/tcp': config['port']},
        environment={
            'HOST': 'odoo-db',
            'USER': config['db_user'],
            'PASSWORD': config['db_password']
        },
        network="odoo-network",
        detach=True,
        restart_policy={"Name": "always"}
    )
    return db_container, odoo_container
