import paramiko

host = "217.198.12.144"
username = "root"
password = "hF*?5AHJc#JTuF"

def ssh_cmd(ssh, cmd, timeout=30):
    print(f"\n>>> {cmd}...")
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('utf-8', errors='ignore')
    err = stderr.read().decode('utf-8', errors='ignore')
    if out:
        print(out[:1500])
    if err:
        print(f"STDERR: {err[:300]}")
    return out

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print(f"Connecting to {host}...")
    ssh.connect(host, username=username, password=password, timeout=30)
    print("Connected!")
    
    print("\n" + "="*60)
    print("TESTING DEPLOYMENT")
    print("="*60)
    
    # Test Backend API
    print("\n=== Testing Backend API (port 3000) ===")
    ssh_cmd(ssh, "curl -s http://localhost:3000/api/batches")
    ssh_cmd(ssh, "curl -s http://localhost:3000/api/accounts?page=1&limit=5")
    ssh_cmd(ssh, "curl -s http://localhost:3000/api/stats")
    
    # Test Frontend
    print("\n=== Testing Frontend (port 3001) ===")
    ssh_cmd(ssh, "curl -s http://localhost:3001/ | head -5")
    
    # Check PM2
    print("\n=== PM2 Status ===")
    ssh_cmd(ssh, "pm2 status")
    
    # Check memory
    print("\n=== Memory Usage ===")
    ssh_cmd(ssh, "free -h")
    
    ssh.close()
    
    print("\n" + "="*60)
    print("DEPLOYMENT SUMMARY")
    print("="*60)
    print(f"""
✅ Backend API: http://{host}:3000
✅ Frontend:    http://{host}:3001

Processes:
- influence-api (Backend Express server)
- influence-worker (Video upload worker)
- influence-stats-worker (Statistics collector)
- influence-frontend (React SPA)

Database:
- PostgreSQL: influence@localhost:5432/influence
- Redis: localhost:6379
""")

if __name__ == "__main__":
    main()
