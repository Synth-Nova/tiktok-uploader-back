import paramiko

host = "217.198.12.144"
username = "root"
password = "hF*?5AHJc#JTuF"

LOCAL_ARCHIVE = "/tmp/frontend.tar.gz"
REMOTE_ARCHIVE = "/tmp/frontend.tar.gz"
FRONTEND_REMOTE = "/opt/influence-frontend"

def ssh_cmd(ssh, cmd, timeout=600):
    print(f">>> {cmd[:80]}...")
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('utf-8', errors='ignore')
    err = stderr.read().decode('utf-8', errors='ignore')
    if out:
        print(out[:1500])
    if err and 'warn' not in err.lower():
        print(f"STDERR: {err[:500]}")
    return out

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print(f"Connecting to {host}...")
    ssh.connect(host, username=username, password=password, timeout=30)
    print("Connected!\n")
    
    # Upload archive
    print("=== Uploading archive ===")
    sftp = ssh.open_sftp()
    sftp.put(LOCAL_ARCHIVE, REMOTE_ARCHIVE)
    sftp.close()
    print("Archive uploaded!\n")
    
    # Extract and rebuild
    print("=== Extracting ===")
    ssh_cmd(ssh, f"rm -rf {FRONTEND_REMOTE}/src {FRONTEND_REMOTE}/public")
    ssh_cmd(ssh, f"cd /tmp && tar -xzf {REMOTE_ARCHIVE}")
    ssh_cmd(ssh, f"cp -r /tmp/frontend/src {FRONTEND_REMOTE}/")
    ssh_cmd(ssh, f"cp -r /tmp/frontend/public {FRONTEND_REMOTE}/")
    
    # Verify the change
    print("\n=== Verifying auth change ===")
    ssh_cmd(ssh, f"grep -A5 'VALID_PASSWORD' {FRONTEND_REMOTE}/src/context/AuthContext.tsx")
    
    # Rebuild
    print("\n=== Rebuilding frontend ===")
    ssh_cmd(ssh, f"cd {FRONTEND_REMOTE} && yarn build", timeout=120)
    
    # Restart PM2
    print("\n=== Restarting frontend ===")
    ssh_cmd(ssh, "pm2 restart influence-frontend")
    ssh_cmd(ssh, "pm2 status")
    
    ssh.close()
    print("\n✅ Done! New credentials: admin / rewfdsvcx5")

if __name__ == "__main__":
    main()
