import paramiko
import os
import stat

host = "217.198.12.144"
username = "root"
password = "hF*?5AHJc#JTuF"

# Backend local path
BACKEND_PATH = "/home/user/webapp/my-tiktok-uploader/backend"
REMOTE_PATH = "/opt/influence-backend"

def sftp_upload_dir(sftp, local_dir, remote_dir, ssh):
    """Recursively upload directory via SFTP"""
    
    # Create remote directory
    try:
        sftp.stat(remote_dir)
    except FileNotFoundError:
        print(f"Creating dir: {remote_dir}")
        sftp.mkdir(remote_dir)
    
    for item in os.listdir(local_dir):
        local_path = os.path.join(local_dir, item)
        remote_path = os.path.join(remote_dir, item).replace("\\", "/")
        
        # Skip node_modules, dist, .git
        if item in ['node_modules', 'dist', '.git', 'venv', '__pycache__']:
            continue
            
        if os.path.isdir(local_path):
            sftp_upload_dir(sftp, local_path, remote_path, ssh)
        else:
            print(f"Uploading: {item}")
            sftp.put(local_path, remote_path)

def ssh_command(ssh, command, timeout=600):
    print(f"\n>>> {command[:100]}...")
    stdin, stdout, stderr = ssh.exec_command(command, timeout=timeout)
    out = stdout.read().decode('utf-8', errors='ignore')
    err = stderr.read().decode('utf-8', errors='ignore')
    exit_code = stdout.channel.recv_exit_status()
    if out:
        print(out[:3000])
    if err and 'warn' not in err.lower():
        print(f"STDERR: {err[:1000]}")
    return exit_code, out, err

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print(f"Connecting to {host}...")
    ssh.connect(host, username=username, password=password, timeout=30)
    print("Connected!")
    
    # Clean up old deployment
    print("\n=== Cleaning up old deployment ===")
    ssh_command(ssh, f"rm -rf {REMOTE_PATH}")
    ssh_command(ssh, f"mkdir -p {REMOTE_PATH}")
    
    # Open SFTP
    print("\n=== Uploading backend files via SFTP ===")
    sftp = ssh.open_sftp()
    
    sftp_upload_dir(sftp, BACKEND_PATH, REMOTE_PATH, ssh)
    
    sftp.close()
    print("\n=== Files uploaded successfully! ===")
    
    # Verify uploaded files
    print("\n=== Verifying uploaded files ===")
    ssh_command(ssh, f"ls -la {REMOTE_PATH}")
    ssh_command(ssh, f"ls -la {REMOTE_PATH}/src")
    
    ssh.close()
    print("\n=== Upload complete! ===")

if __name__ == "__main__":
    main()
