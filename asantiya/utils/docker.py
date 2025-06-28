from docker.errors import APIError
from docker import DockerClient
from typing import Dict, List
from asantiya.schemas.models import AccessoryConfig
from asantiya.logger import setup_logging

_logger = setup_logging()

def sort_by_dependencies(configs: Dict[str, AccessoryConfig]) -> List[str]:
    """Topological sort to determine startup order using Kahn's algorithm"""
    # Build dependency graph
    graph = {name: set(cfg.depends_on) for name, cfg in configs.items()}
    ordered = []
    no_deps = [name for name, deps in graph.items() if not deps]

    while no_deps:
        node = no_deps.pop()
        ordered.append(node)
        
        # Remove this node from all dependencies
        for other, deps in graph.items():
            if node in deps:
                deps.remove(node)
                if not deps:  # No more dependencies
                    no_deps.append(other)
    
    if len(ordered) != len(configs):
        raise ValueError("Circular dependency detected")
    
    return ordered

def ensure_network(client: DockerClient, network_name: str) -> None:
    """Create network if it doesn't exist"""
    try:
        if not any(net.name == network_name for net in client.networks.list()):
            client.networks.create(
                network_name,
                driver="bridge",
                labels={"managed_by": "odooops"},
                check_duplicate=True
            )
        else:
            _logger.info(f"    ✓ {network_name} already exists")
    except APIError as e:
        raise RuntimeError(f"Network creation failed: {e.explanation}")
    
