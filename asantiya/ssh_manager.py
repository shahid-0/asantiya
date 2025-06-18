import paramiko
from pathlib import Path
from typing import List

class SSHManager:

    def __init__(self):
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    def connect(self, host_name: str, username: str, key_path: str = None, password: str = None):
        if key_path:    
            key_path = Path(key_path).expanduser()
            key = paramiko.RSAKey.from_private_key_file(str(key_path))
            self.ssh.connect(host_name, username=username, pkey=key, timeout=10)
        else:
            self.ssh.connect(host_name, username=username, password=password, timeout=10)

    def execute_commands(self, commands: List[str]):
        _, stdout, stderr = self.ssh.exec_command(" ".join(commands))
        output = stdout.read().decode('utf-8') + stderr.read().decode('utf-8')
        exit_code = stdout.channel.recv_exit_status()
        return exit_code, output

    def close(self):
        self.ssh.close()
