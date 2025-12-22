import paramiko
import time

host = "217.198.12.144"
username = "root"
password = "hF*?5AHJc#JTuF"

def ssh_command(ssh, command, timeout=600):
    print(f"\n>>> {command[:100]}...")
    stdin, stdout, stderr = ssh.exec_command(command, timeout=timeout)
    out = stdout.read().decode('utf-8', errors='ignore')
    err = stderr.read().decode('utf-8', errors='ignore')
    exit_code = stdout.channel.recv_exit_status()
    if out:
        print(out[:3000])
    if err and exit_code != 0:
        print(f"STDERR: {err[:1000]}")
    return exit_code, out, err

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print(f"Connecting to {host}...")
    ssh.connect(host, username=username, password=password, timeout=30)
    print("Connected!")
    
    # 1. Clone repository
    print("\n=== 1. Cloning backend repository ===")
    ssh_command(ssh, "rm -rf /opt/influence-backend")
    ssh_command(ssh, "git clone https://github.com/Synth-Nova/influence1.git /opt/influence-backend", timeout=120)
    
    # 2. Create .env file
    print("\n=== 2. Creating .env file ===")
    env_content = '''DATABASE_URL="postgresql://influence:InfluencePass2024!@localhost:5432/influence?schema=public"
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
PORT=3000
HEADLESS=true
NODE_ENV=production'''
    
    ssh_command(ssh, f'''cat > /opt/influence-backend/.env << 'ENVEOF'
{env_content}
ENVEOF''')
    
    # 3. Install dependencies
    print("\n=== 3. Installing npm dependencies ===")
    ssh_command(ssh, "cd /opt/influence-backend && yarn install", timeout=300)
    
    # 4. Generate Prisma client
    print("\n=== 4. Generating Prisma client ===")
    ssh_command(ssh, "cd /opt/influence-backend && npx prisma generate", timeout=60)
    
    # 5. Run database migrations
    print("\n=== 5. Running Prisma migrations ===")
    ssh_command(ssh, "cd /opt/influence-backend && npx prisma migrate deploy", timeout=120)
    
    # 6. Build TypeScript
    print("\n=== 6. Building TypeScript ===")
    ssh_command(ssh, "cd /opt/influence-backend && yarn build", timeout=120)
    
    # 7. Check built files
    print("\n=== 7. Checking built files ===")
    ssh_command(ssh, "ls -la /opt/influence-backend/dist/")
    
    ssh.close()
    print("\n=== Backend deployment complete! ===")

if __name__ == "__main__":
    main()
