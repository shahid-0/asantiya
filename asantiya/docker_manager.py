import docker
from pathlib import Path
from tabulate import tabulate
from typing import Annotated, List, Optional, Dict, Union
import docker.errors
from rich.progress import (
    Progress,  
    TextColumn,
    BarColumn,
    TransferSpeedColumn,
)
from asantiya.schemas.models import AccessoryConfig, AppConfig, Builder
from asantiya.utils.docker import ensure_network, sort_by_dependencies
from asantiya.utils.config import load_config
from asantiya.logger import setup_logging
from asantiya.utils.misc import _format_ports, _format_uptime

_logger = setup_logging()

class DockerManager:
    
    def __init__(self, config_path: Optional[Path] = None):
        self.docker = docker
        self.docker_client = None
        self.config: AppConfig = self._load_config(config_path)

    def _load_config(self, config_path):
        if config_path is None:
            config_path = Path().cwd() / "deploy.yaml"
            
        return load_config(config_path)
            
    def connect(self) -> docker.DockerClient:
        try:
            if not self.config.builder.local:
                self.docker_client = self.docker.DockerClient(base_url=self.config.builder.remote)
            else:
                self.docker_client = self.docker.from_env()
            self.check_docker_version()
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
    
    def _get_service_name(self, accessory: AccessoryConfig, service_name: str) -> str:
        """if accessory.config is none make asantiya-{service_name}

        Args:
            accessory (AccessoryConfig): accessory config
            service_name (str): name of service

        Returns:
            str
        """
        
        service_name = accessory.service if accessory.service else "asantiya-{name}".format(name=service_name)
        return service_name
        
    def _find_accessory_by_name(self, name: str):
        _accessory = None
        for accessory in self.config.accessories.keys():
            if name == self._get_service_name(self.config.accessories[accessory], accessory):
                _accessory = self._get_service_name(self.config.accessories[accessory], accessory)
                break

        if not _accessory:
            _logger.error(f"Error: No accessory named '{name}' in configuration")
            return None

        return _accessory

    def delete_image(self, image_name: str, force: bool = False, prune: bool = True) -> bool:
        """
        Delete a single Docker image with enhanced error handling
        
        Args:
            image_name: Name or ID of the image to delete
            force: Force removal if image is in use
            prune: Remove dangling child images
        
        Returns:
            bool: True if deleted successfully, False otherwise
        
        Raises:
            ValueError: If image_name is empty
            RuntimeError: If deletion fails for non-404 reasons
        """
        if not image_name:
            raise ValueError("Image name cannot be empty")
        
        try:
            _logger.info(f"Attempting to delete image: {image_name}")
            image = self.docker_client.images.get(image_name)
            
            # Get tags before deletion for logging
            tags = image.tags or ["<untagged>"]
            
            self.docker_client.images.remove(
                image.id,
                force=force,
                noprune=not prune
            )
            
            _logger.info(f"Successfully deleted image: {tags[0]} (ID: {image.id[:12]})")
            return True
            
        except docker.errors.ImageNotFound:
            _logger.warning(f"Image not found: {image_name}")
            return False
        except docker.errors.APIError as e:
            error_msg = f"Failed to delete {image_name}: {e.explanation}"
            _logger.error(error_msg)
            raise RuntimeError(error_msg)
        
    def delete_images(self, image_names: List[str], force: bool = False, stop_on_error: bool = False) -> Dict[str, Union[bool, str]]:
        """
        Delete multiple Docker images with comprehensive status reporting
        
        Args:
            image_names: List of image names/IDs to delete
            force: Force removal if images are in use
            stop_on_error: Whether to stop on first failure
        
        Returns:
            Dict[str, Union[bool, str]]: 
                Key: image name
                Value: True if deleted, False if not found, or error message
        
        Example:
            >>> delete_images(["python:3.8", "redis"], force=True)
            {
                "python:3.8": True,
                "redis": "Error: image is referenced in multiple repositories"
            }
        """
        results = {}
        
        for name in image_names:
            try:
                success = self.delete_image(name, force=force)
                results[name] = success
            except Exception as e:
                results[name] = str(e)
                if stop_on_error:
                    break
        
        return results

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
                    
    def create_accessory(self, config: AccessoryConfig, service_name: str) -> docker.models.containers.Container:
        """Create a single accessory container"""
        service_name = config.service if config.service else f"asantiya-{service_name}"
        try:
            # Check if container already exists
            try:
                existing_container = self.docker_client.containers.get(service_name)
                
                if existing_container.status == "running":
                    _logger.info(f"Container {service_name} is already running")
                    return existing_container
                    
                _logger.info(f"Found stopped container {service_name} - starting it")
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
                name=service_name,
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
            raise RuntimeError(f"Failed to create {service_name}: {e.explanation}")
        
    def list_accessory_services(self) -> List[str]:
        """
        List all service names from the accessories configuration.
        
        Args:
            config: The loaded AppConfig containing accessories configuration
        
        Returns:
            A list of service names
            Example:
                ["redis-service", "database-service"]
        """
        config = self.config.accessories
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
            name = self._find_accessory_by_name(name)
            if not name:
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
        names = [names] if isinstance(names, str) else names
        
        results = {}
        for name in names:
            try:
                self.stop_accessory(name, force, raise_errors)
                results[name] = True
            except Exception as e:
                results[name] = str(e)
        return results
    
    def stop_app_container(self, force: bool = False):
        """
        force: If True, removes running containers (with SIGKILL)
        """
        try:
            container = self.docker_client.containers.get(self.config.service)
            if container.status == "running":
                container.stop(timeout=5,) # More graceful than kill()
                _logger.info(f"Successfully stopped container: {self.config.service}")
            if force:
                container.remove(v=force)
                _logger.info(f"Remove container: {self.config.service}")
        except docker.errors.NotFound:
            msg = f"Container {self.config.service} not found"
            _logger.error(msg)
        except docker.errors.APIError as e:
            msg = f"Failed to stop {self.config.service}: {e.explanation}"
            _logger.error(msg)   
              
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
    
    def create_all_accessories(self) -> Dict[str, str]:
        """Create containers in dependency order"""
        results = {}
        configs = self.config.accessories
        ordered_services = sort_by_dependencies(configs)

        for service_name in ordered_services:
            config = configs[service_name]
            try:
                container = self.create_accessory(config, service_name)
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
        Start/Restart one or multiple accessory containers with status reporting
        
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
                _logger.info(f"Successfully started/restarted container: {name}")
                results[name] = True
                
            except docker.errors.NotFound:
                msg = f"Container {name} not found"
                _logger.error(msg)
                results[name] = msg
                if raise_errors:
                    raise ValueError(msg)
            except docker.errors.APIError as e:
                msg = f"Failed to start/restart {name}: {e.explanation}"
                _logger.error(msg)
                results[name] = msg
                if raise_errors:
                    raise RuntimeError(msg)
            except Exception as e:
                msg = f"Unexpected error starting/restarting {name}: {str(e)}"
                _logger.error(msg)
                results[name] = msg
                if raise_errors:
                    raise RuntimeError(msg)
        
        return results
        
    def list_configured_containers(self) -> None:
        """
        Collects configured containers and displays them in a docker ps-like format.
        """
        try:
            all_containers = self.docker_client.containers.list(all=True)
            rows = self._get_container_table_rows(self.config.accessories, all_containers)
            self._print_container_table(rows)
        except docker.errors.APIError as e:
            print(f"❌ Docker API error: {e.explanation}")
        except Exception as e:
            print(f"❌ Error listing containers: {str(e)}")

    def _get_container_table_rows(self, configs: Dict[str, AccessoryConfig], all_containers) -> List[List[str]]:
        rows = []

        for service_name, accessory in configs.items():
            matched = None
            for container in all_containers:
                if container.name == self._get_service_name(accessory, service_name):
                    matched = container
                    break

            if matched:
                container_id = matched.id[:12]
                image = matched.image.tags[0] if matched.image.tags else "untagged"
                status = _format_uptime(
                    matched.attrs["State"]["StartedAt"],
                    matched.attrs["State"]["Status"]
                )

                port_data = matched.attrs['NetworkSettings']['Ports']
                ports_str = _format_ports(port_data)

                rows.append([
                    container_id,
                    image[:20],
                    status,
                    ports_str,
                    matched.name,
                ])
            else:
                rows.append(["-", "-", "Not created", "-", accessory.service])

        return rows

    def _print_container_table(self, rows: List[List[str]]) -> None:
        headers = ["CONTAINER ID", "IMAGE", "STATUS", "PORTS", "NAMES"]
        print(tabulate(rows, headers=headers, tablefmt="github"))
        
    def show_accessory_logs(
        self,
        name: str,
        follow: bool = False,
        tail: int = 100,
        timestamps: bool = False
    ) -> None:
        """
        Display logs for an accessory container
        
        Args:
            name: Name of the container (must exist in config)
            follow: Keep streaming new log output (like tail -f)
            tail: Number of lines to show from the end of logs
            timestamps: Show timestamps for each log line
        """
        name = self._find_accessory_by_name(name)
        if not name:
            return

        try:
            container = self.docker_client.containers.get(name)
            
            print(f"=== Showing logs for {name} ({container.image.tags[0] if container.image.tags else 'no image'}) ===")
            
            # Get and display logs
            logs = container.logs(
                stream=follow,
                follow=follow,
                tail=str(tail),
                timestamps=timestamps
            )
            
            if follow:
                try:
                    for line in logs:
                        print(line.decode('utf-8').strip())
                except KeyboardInterrupt:
                    print("\nStopping log stream...")
            else:
                print(logs.decode('utf-8'))
                
        except docker.errors.NotFound:
            _logger.warning(f"Container '{name}' not found (is it running?)")
        except docker.errors.APIError as e:
            _logger.error(f"Docker error: {e.explanation}")
        except Exception as e:
            _logger.error(f"Unexpected error: {str(e)}")
            
    def reboot_single_accessory(
        self,
        accessory_name: str,
        force: bool = False
    ) -> Union[bool, str]:
        """
        Reboot a single accessory container (stop, remove, recreate)
        
        Args:
            accessory_name: Name of the accessory from config
            force: Remove associated volumes when deleting container
        
        Returns:
            True if successful, error message if failed
        """
        if accessory_name not in self.config.accessories:
            return f"Accessory '{accessory_name}' not found in configuration"

        try:
            accessory = self.config.accessories[accessory_name]
            container_name = accessory.service

            # 1. Stop and remove existing container
            try:
                container = self.docker_client.containers.get(container_name)
                if container.status == "running":
                    container.stop(timeout=10)
                container.remove(v=force)
                _logger.info(f"Removed old container: {container_name}")
            except docker.errors.NotFound:
                _logger.warning(f"No existing container found for {accessory_name}")
            except docker.errors.APIError as e:
                raise RuntimeError(f"Failed to remove {container_name}: {e.explanation}")

            # 2. Create new container
            new_container = self.create_accessory(accessory, accessory_name)
            _logger.info(f"Successfully rebooted {accessory_name} (new container: {new_container.id[:12]})")
            return True

        except Exception as e:
            error_msg = f"Failed to reboot {accessory_name}: {str(e)}"
            _logger.error(error_msg)
            return error_msg
        
    def reboot_all_accessories(
        self,
        force: bool = False
    ) -> None:
        """
        Reboot all accessory containers
        
        Args:
            force: Remove associated volumes when deleting containers
        
        Returns: None
        """
        for accessory_name in self.config.accessories.keys():
            self.reboot_single_accessory(
                accessory_name,
                force=force
            )
   
    def build_image_from_dockerfile(
        self,
        builder: Builder,
        tag: str,
        build_args: Optional[Dict[str, str]] = None,
        quiet: bool = False,
        rm: bool = True,
        pull: bool = False
    ) -> docker.models.images.Image:
        """
        Build a Docker image from a Dockerfile with real-time log output
        
        Args:
            builder: Configured Builder instance
            tag: Image name and tag (e.g., 'myapp:1.0')
            build_args: Dictionary of build arguments
            quiet: Suppress build output
            rm: Remove intermediate containers after build
            pull: Always attempt to pull newer versions of base images
        
        Returns:
            The built Docker image object
        
        Raises:
            ValueError: If Dockerfile doesn't exist
            RuntimeError: If build fails
        """
        try:
            
            if not quiet:
                _logger.info(f"🏗️ Building {tag} for {builder.platform}")
            
            # Build the image with real-time streaming
            stream = self.docker_client.api.build(
                path=str(builder.dockerfile),
                platform=builder.platform,
                tag=tag,
                buildargs=build_args,
                rm=rm,
                pull=pull,
                decode=True  # Important for streaming logs
            )
            
            # Process build output in real-time
            image_id = None
            for chunk in stream:
                if not quiet:
                    if 'stream' in chunk:
                        line = chunk['stream'].strip()
                        if line:
                            _logger.info(f"│ {line}")
                    elif 'aux' in chunk:
                        image_id = chunk['aux']['ID']
                    elif 'error' in chunk:
                        _logger.error(f"❌ ERROR: {chunk['error']}")
                        raise RuntimeError(chunk['error'])
                    elif 'status' in chunk:
                        _logger.info(f"⏳ {chunk['status']}")
                        if 'progress' in chunk:
                            _logger.info(f"   {chunk['progress']}")
            
            if not quiet:
                _logger.info("=" * 60)
                if image_id:
                    _logger.info(f"✅ Successfully built {tag} (ID: {image_id[:12]})")
                else:
                    _logger.info("⚠️  Build completed but no image ID received")
            
            return self.docker_client.images.get(tag)
            
        except docker.errors.BuildError as e:
            error_msg = "Build failed:\n"
            for entry in e.build_log:
                if 'stream' in entry and entry['stream'].strip():
                    error_msg += f"  {entry['stream'].strip()}\n"
            raise RuntimeError(error_msg)
        except docker.errors.APIError as e:
            raise RuntimeError(f"Docker API error: {e.explanation}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error: {str(e)}")    
    
    def deploy_app(self) -> None:
        """
        Deploy app to the server
        
        Returns:
            The built Docker image object
        
        Raises:
            ValueError: If Dockerfile doesn't exist
            RuntimeError: If build fails
        """
        try:
            config = self.config
            
            # Prepare container config
            host_port, container_port = config.app_ports.split(':')
            self.stop_app_container(force=True)
            name = self.list_accessory_services() 
            self.stop_accessories(name, True)
            self.delete_image(config.image, force=True)
            
            image = self.build_image_from_dockerfile(config.builder, self.config.image)
            results = self.create_all_accessories()
            _logger.info(f"Successfully deployed in order: {', '.join(results.keys())}")
            try:
                container = self.docker_client.containers.run(
                    image=image,
                    name=config.service,
                    # environment=config.env,
                    ports={f"{container_port}/tcp": int(host_port)},
                    # volumes=self._parse_volumes(config.volumes),
                    # network=config.network,
                    detach=True,
                    # restart_policy={"Name": config.options.restart},
                    labels={"managed_by": "odooops"}
                )
            
                return container
            except docker.errors.NotFound:
                msg = f"Container {config.service} not found"
                _logger.error(msg)
            except docker.errors.APIError as e:
                raise RuntimeError(f"Failed to run {config.service}: {e.explanation}")
            
        except Exception as e:
            raise RuntimeError(f"Unexpected error: {str(e)}")
        
    def remove_app(self) -> None:
        self.stop_app_container(force=True)
        name = self.list_accessory_services() 
        self.stop_accessories(name, True)
        self.delete_image(self.config.image, force=True)
    
    def start_app(self) -> None:
        names = self.list_accessory_services() 
        self.restart_accessories(names=names, force_restart=True)
        
        try:
            container = self.docker_client.containers.get(self.config.service)
            if container.status != "running":
                container.start()
                msg = f"Container {self.config.service} start running"
                _logger.info(msg)
        except docker.errors.NotFound:
            msg = f"Container {self.config.service} not found"
            _logger.error(msg)
        except docker.errors.APIError as e:
            raise RuntimeError(f"Unexpected error while starting the app: {self.config.service}: {e.explanation}")