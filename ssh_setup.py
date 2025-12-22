import paramiko
import time
import sys

host = "217.198.12.144"
username = "root"
password = "hF*?5AHJc#JTuF"

def ssh_command(ssh, command, timeout=300):
    print(f"\n>>> Executing: {command[:100]}...")
    stdin, stdout, stderr = ssh.exec_command(command, timeout=timeout)
    out = stdout.read().decode('utf-8', errors='ignore')
    err = stderr.read().decode('utf-8', errors='ignore')
    exit_code = stdout.channel.recv_exit_status()
    if out:
        print(out[:2000])
    if err:
        print(f"STDERR: {err[:500]}")
    return exit_code, out, err

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print(f"Connecting to {host}...")
    ssh.connect(host, username=username, password=password, timeout=30)
    print("Connected!")
    
    # Check current status
    print("\n=== Checking system status ===")
    ssh_command(ssh, "cat /etc/os-release | head -3")
    ssh_command(ssh, "free -h")
    ssh_command(ssh, "df -h /")
    
    # Check if Node.js is installed
    exit_code, out, _ = ssh_command(ssh, "which node && node --version")
    if exit_code != 0:
        print("\n=== Node.js not installed, installing... ===")
        ssh_command(ssh, "apt-get update -qq")
        ssh_command(ssh, "curl -fsSL https://deb.nodesource.com/setup_22.x | bash -", timeout=120)
        ssh_command(ssh, "apt-get install -y nodejs", timeout=120)
    
    # Check services
    print("\n=== Checking services ===")
    ssh_command(ssh, "which yarn || npm install -g yarn")
    ssh_command(ssh, "which pm2 || npm install -g pm2")
    ssh_command(ssh, "systemctl is-active postgresql || echo 'PostgreSQL not running'")
    ssh_command(ssh, "systemctl is-active redis-server || echo 'Redis not running'")
    ssh_command(ssh, "which google-chrome || echo 'Chrome not installed'")
    
    ssh.close()
    print("\n=== Check complete ===")

if __name__ == "__main__":
    main()
