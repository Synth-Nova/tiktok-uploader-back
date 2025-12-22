import paramiko
import os

host = "217.198.12.144"
username = "root"
password = "hF*?5AHJc#JTuF"

FRONTEND_LOCAL = "/home/user/webapp/my-tiktok-uploader/frontend"
FRONTEND_REMOTE = "/opt/influence-frontend"

def sftp_upload_dir(sftp, local_dir, remote_dir):
    """Recursively upload directory via SFTP"""
    
    try:
        sftp.stat(remote_dir)
    except FileNotFoundError:
        print(f"Creating dir: {remote_dir}")
        sftp.mkdir(remote_dir)
    
    for item in os.listdir(local_dir):
        local_path = os.path.join(local_dir, item)
        remote_path = os.path.join(remote_dir, item).replace("\\", "/")
        
        # Skip node_modules, build, .git
        if item in ['node_modules', 'build', '.git', '__pycache__']:
            continue
            
        if os.path.isdir(local_path):
            sftp_upload_dir(sftp, local_path, remote_path)
        else:
            print(f"Uploading: {item}")
            sftp.put(local_path, remote_path)

def ssh_cmd(ssh, cmd, timeout=600):
    print(f"\n>>> {cmd[:80]}...")
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('utf-8', errors='ignore')
    err = stderr.read().decode('utf-8', errors='ignore')
    exit_code = stdout.channel.recv_exit_status()
    if out:
        print(out[:2000])
    if err and exit_code != 0:
        print(f"STDERR: {err[:500]}")
    return exit_code, out, err

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print(f"Connecting to {host}...")
    ssh.connect(host, username=username, password=password, timeout=30)
    print("Connected!")
    
    # Clean and create directory
    print("\n=== Cleaning up ===")
    ssh_cmd(ssh, f"rm -rf {FRONTEND_REMOTE}")
    ssh_cmd(ssh, f"mkdir -p {FRONTEND_REMOTE}")
    
    # Upload frontend
    print("\n=== Uploading frontend files ===")
    sftp = ssh.open_sftp()
    sftp_upload_dir(sftp, FRONTEND_LOCAL, FRONTEND_REMOTE)
    sftp.close()
    print("\n=== Files uploaded! ===")
    
    # Verify upload
    ssh_cmd(ssh, f"ls -la {FRONTEND_REMOTE}")
    ssh_cmd(ssh, f"cat {FRONTEND_REMOTE}/src/services/api.ts | head -10")
    
    ssh.close()

if __name__ == "__main__":
    main()
