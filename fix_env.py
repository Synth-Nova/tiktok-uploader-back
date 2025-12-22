import paramiko

host = "217.198.12.144"
username = "root"
password = "hF*?5AHJc#JTuF"

REMOTE_PATH = "/opt/influence-backend"

def ssh_command(ssh, command, timeout=60):
    print(f"\n>>> {command[:100]}...")
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
    
    # Check current .env.production
    print("\n=== Current .env.production ===")
    ssh_command(ssh, f"cat {REMOTE_PATH}/.env.production")
    
    # Update .env.production with correct credentials
    print("\n=== Updating .env.production ===")
    env_content = '''DATABASE_URL="postgresql://influence:InfluencePass2024!@localhost:5432/influence?schema=public"
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
PORT=3000
HEADLESS=true'''
    
    ssh_command(ssh, f'''cat > {REMOTE_PATH}/.env.production << 'ENVEOF'
{env_content}
ENVEOF''')
    
    # Verify
    print("\n=== Updated .env.production ===")
    ssh_command(ssh, f"cat {REMOTE_PATH}/.env.production")
    
    # Restart PM2 processes
    print("\n=== Restarting PM2 processes ===")
    ssh_command(ssh, "pm2 restart all")
    
    import time
    time.sleep(3)
    
    # Check status
    print("\n=== PM2 status ===")
    ssh_command(ssh, "pm2 status")
    
    # Test API again
    print("\n=== Testing API ===")
    ssh_command(ssh, "curl -s http://localhost:3000/api/batches")
    
    ssh.close()
    print("\n=== Fix complete! ===")

if __name__ == "__main__":
    main()
