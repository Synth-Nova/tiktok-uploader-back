import paramiko

host = "217.198.12.144"
username = "root"
password = "hF*?5AHJc#JTuF"

REMOTE_PATH = "/opt/influence-backend"

def ssh_command(ssh, command, timeout=120):
    print(f"\n>>> {command[:100]}...")
    stdin, stdout, stderr = ssh.exec_command(command, timeout=timeout)
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
    
    # Stop any existing PM2 processes
    print("\n=== 1. Stopping existing PM2 processes ===")
    ssh_command(ssh, "pm2 kill 2>/dev/null || true")
    
    # Create PM2 ecosystem config for production
    print("\n=== 2. Creating PM2 ecosystem config ===")
    pm2_config = '''module.exports = {
  apps: [
    {
      name: 'influence-api',
      script: 'dist/server.js',
      cwd: '/opt/influence-backend',
      env: {
        NODE_ENV: 'production',
        PORT: 3000
      },
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G'
    },
    {
      name: 'influence-worker',
      script: 'dist/worker.js',
      cwd: '/opt/influence-backend',
      env: {
        NODE_ENV: 'production'
      },
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G'
    },
    {
      name: 'influence-stats-worker',
      script: 'dist/workers/stats.worker.js',
      cwd: '/opt/influence-backend',
      env: {
        NODE_ENV: 'production'
      },
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '500M'
    }
  ]
};'''
    
    ssh_command(ssh, f'''cat > {REMOTE_PATH}/ecosystem.production.config.js << 'EOFPM2'
{pm2_config}
EOFPM2''')
    
    # Start PM2 with the config
    print("\n=== 3. Starting PM2 processes ===")
    ssh_command(ssh, f"cd {REMOTE_PATH} && pm2 start ecosystem.production.config.js")
    
    # Wait a moment for startup
    import time
    time.sleep(3)
    
    # Check status
    print("\n=== 4. Checking PM2 status ===")
    ssh_command(ssh, "pm2 status")
    
    # Check logs
    print("\n=== 5. Checking logs ===")
    ssh_command(ssh, "pm2 logs --nostream --lines 20")
    
    # Save PM2 process list
    print("\n=== 6. Saving PM2 process list ===")
    ssh_command(ssh, "pm2 save")
    
    # Setup PM2 startup
    print("\n=== 7. Setup PM2 auto-startup ===")
    ssh_command(ssh, "pm2 startup systemd -u root --hp /root 2>/dev/null || true")
    
    # Test API endpoint
    print("\n=== 8. Testing API endpoint ===")
    ssh_command(ssh, "curl -s http://localhost:3000/api/batches | head -100 || echo 'API test complete'")
    
    ssh.close()
    print("\n=== PM2 startup complete! ===")

if __name__ == "__main__":
    main()
