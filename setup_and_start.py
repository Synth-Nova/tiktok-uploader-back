import paramiko
import time

host = "217.198.12.144"
username = "root"
password = "hF*?5AHJc#JTuF"

REMOTE_PATH = "/opt/influence-backend"

def ssh_command(ssh, command, timeout=600):
    print(f"\n>>> {command[:100]}...")
    stdin, stdout, stderr = ssh.exec_command(command, timeout=timeout)
    out = stdout.read().decode('utf-8', errors='ignore')
    err = stderr.read().decode('utf-8', errors='ignore')
    exit_code = stdout.channel.recv_exit_status()
    if out:
        print(out[:4000])
    if err:
        print(f"STDERR: {err[:1500]}")
    return exit_code, out, err

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print(f"Connecting to {host}...")
    ssh.connect(host, username=username, password=password, timeout=30)
    print("Connected!")
    
    # 1. Create proper .env file
    print("\n=== 1. Creating .env file ===")
    env_content = '''DATABASE_URL="postgresql://influence:InfluencePass2024!@localhost:5432/influence?schema=public"
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
PORT=3000
HEADLESS=true
NODE_ENV=production'''
    
    ssh_command(ssh, f'''cat > {REMOTE_PATH}/.env << 'ENVEOF'
{env_content}
ENVEOF''')
    
    ssh_command(ssh, f"cat {REMOTE_PATH}/.env")
    
    # 2. Install dependencies
    print("\n=== 2. Installing npm dependencies ===")
    exit_code, out, err = ssh_command(ssh, f"cd {REMOTE_PATH} && yarn install 2>&1", timeout=300)
    
    # 3. Generate Prisma client
    print("\n=== 3. Generating Prisma client ===")
    ssh_command(ssh, f"cd {REMOTE_PATH} && npx prisma generate 2>&1", timeout=120)
    
    # 4. Run database migrations
    print("\n=== 4. Running Prisma migrations ===")
    ssh_command(ssh, f"cd {REMOTE_PATH} && npx prisma migrate deploy 2>&1", timeout=120)
    
    # 5. Check database tables
    print("\n=== 5. Checking database tables ===")
    ssh_command(ssh, "PGPASSWORD='InfluencePass2024!' psql -U influence -d influence -h localhost -c '\\dt'")
    
    # 6. Build TypeScript
    print("\n=== 6. Building TypeScript ===")
    ssh_command(ssh, f"cd {REMOTE_PATH} && yarn build 2>&1", timeout=180)
    
    # 7. Check built files
    print("\n=== 7. Checking built files ===")
    ssh_command(ssh, f"ls -la {REMOTE_PATH}/dist/")
    
    ssh.close()
    print("\n=== Setup complete! ===")

if __name__ == "__main__":
    main()
