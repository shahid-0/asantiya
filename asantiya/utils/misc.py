from datetime import datetime, timezone
import dateutil.parser

def _format_uptime(started_at: str, status: str) -> str:
    try:
        started = dateutil.parser.isoparse(started_at).astimezone(timezone.utc)
        now = datetime.now(timezone.utc)
        delta = now - started

        days = delta.days
        seconds = delta.seconds
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60

        if status == "running":
            if days > 0:
                return f"Up {days} day{'s' if days > 1 else ''}"
            elif hours > 0:
                return f"Up {hours} hour{'s' if hours > 1 else ''}"
            elif minutes > 0:
                return f"Up {minutes} minute{'s' if minutes > 1 else ''}"
            else:
                return "Up less than a minute"
        else:
            return status.capitalize()
    except Exception:
        return status.capitalize()


def _format_ports(port_data: dict) -> str:
    ports = []
    for container_port, mappings in (port_data or {}).items():
        if mappings:
            for mapping in mappings:
                host_ip = mapping.get("HostIp", "")
                host_port = mapping.get("HostPort", "")
                ports.append(f"{host_ip}:{host_port}->{container_port}")
        else:
            ports.append(container_port)  # e.g., exposed but not published
    return ", ".join(ports)
