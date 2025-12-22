import paramiko

host = "217.198.12.144"
username = "root"
password = "hF*?5AHJc#JTuF"

def ssh_cmd(ssh, cmd, timeout=60):
    print(f"\n>>> {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('utf-8', errors='ignore')
    err = stderr.read().decode('utf-8', errors='ignore')
    if out:
        print(out[:2000])
    if err:
        print(f"STDERR: {err[:500]}")

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username=username, password=password, timeout=30)

print("=== PM2 Status ===")
ssh_cmd(ssh, "pm2 status")

print("\n=== Frontend build files ===")
ssh_cmd(ssh, "ls -la /opt/influence-frontend/build/")
ssh_cmd(ssh, "ls -la /opt/influence-frontend/build/static/js/")

print("\n=== Check index.html ===")
ssh_cmd(ssh, "cat /opt/influence-frontend/build/index.html")

print("\n=== Test local access ===")
ssh_cmd(ssh, "curl -s http://localhost:3001/ | head -20")
ssh_cmd(ssh, "curl -s http://localhost:3001/static/js/ | head -5")

print("\n=== Nginx error log ===")
ssh_cmd(ssh, "tail -20 /var/log/nginx/error.log")

ssh.close()
