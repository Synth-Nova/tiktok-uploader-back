import paramiko
import os

host = "217.198.12.144"
username = "root"
password = "hF*?5AHJc#JTuF"

LOCAL_ARCHIVE = "/tmp/frontend.tar.gz"
REMOTE_ARCHIVE = "/tmp/frontend.tar.gz"
FRONTEND_REMOTE = "/opt/influence-frontend"

def ssh_cmd(ssh, cmd, timeout=600):
    print(f"\n>>> {cmd[:100]}...")
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('utf-8', errors='ignore')
    err = stderr.read().decode('utf-8', errors='ignore')
    exit_code = stdout.channel.recv_exit_status()
    if out:
        print(out[:3000])
    if err:
        print(f"STDERR: {err[:1000]}")
    return exit_code, out, err

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print(f"Connecting to {host}...")
    ssh.connect(host, username=username, password=password, timeout=30)
    print("Connected!")
    
    # Upload archive via SFTP
    print("\n=== Uploading archive via SFTP ===")
    sftp = ssh.open_sftp()
    sftp.put(LOCAL_ARCHIVE, REMOTE_ARCHIVE)
    sftp.close()
    print("Archive uploaded!")
    
    # Extract archive
    print("\n=== Extracting archive ===")
    ssh_cmd(ssh, f"rm -rf {FRONTEND_REMOTE}")
    ssh_cmd(ssh, f"mkdir -p {FRONTEND_REMOTE}")
    ssh_cmd(ssh, f"cd /opt && tar -xzf {REMOTE_ARCHIVE}")
    ssh_cmd(ssh, f"mv /opt/frontend/* {FRONTEND_REMOTE}/ && rmdir /opt/frontend")
    
    # Verify
    print("\n=== Verifying extraction ===")
    ssh_cmd(ssh, f"ls -la {FRONTEND_REMOTE}")
    
    # Check API URL
    print("\n=== Checking API URL ===")
    ssh_cmd(ssh, f"cat {FRONTEND_REMOTE}/src/services/api.ts | head -10")
    
    # Install dependencies
    print("\n=== Installing dependencies ===")
    ssh_cmd(ssh, f"cd {FRONTEND_REMOTE} && yarn install", timeout=300)
    
    # Build frontend
    print("\n=== Building frontend ===")
    ssh_cmd(ssh, f"cd {FRONTEND_REMOTE} && yarn build", timeout=600)
    
    # Check build output
    print("\n=== Checking build output ===")
    ssh_cmd(ssh, f"ls -la {FRONTEND_REMOTE}/build")
    
    # Setup nginx or serve
    print("\n=== Setting up serve ===")
    ssh_cmd(ssh, "npm install -g serve")
    
    # Add frontend to PM2
    print("\n=== Adding frontend to PM2 ===")
    ssh_cmd(ssh, f"pm2 delete influence-frontend 2>/dev/null || true")
    ssh_cmd(ssh, f"pm2 serve {FRONTEND_REMOTE}/build 3001 --name influence-frontend --spa")
    
    ssh_cmd(ssh, "pm2 save")
    ssh_cmd(ssh, "pm2 status")
    
    ssh.close()
    print("\n=== Frontend deployment complete! ===")

if __name__ == "__main__":
    main()
