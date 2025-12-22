import paramiko

host = "217.198.12.144"
username = "root"
password = "hF*?5AHJc#JTuF"

def ssh_cmd(ssh, cmd, timeout=300):
    print(f"\n>>> {cmd[:80]}...")
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('utf-8', errors='ignore')
    err = stderr.read().decode('utf-8', errors='ignore')
    exit_code = stdout.channel.recv_exit_status()
    if out:
        print(out[:2000])
    if err and exit_code != 0:
        print(f"STDERR: {err[:800]}")
    return exit_code, out, err

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print(f"Connecting to {host}...")
    ssh.connect(host, username=username, password=password, timeout=30)
    print("Connected!\n")
    
    # 1. Install Nginx and Certbot
    print("=== 1. Installing Nginx & Certbot ===")
    ssh_cmd(ssh, "apt-get update -qq && apt-get install -y nginx certbot python3-certbot-nginx", timeout=120)
    
    # 2. Create Nginx config
    print("\n=== 2. Creating Nginx config ===")
    nginx_config = '''server {
    listen 80;
    server_name upl.synthnova.me;

    location / {
        proxy_pass http://127.0.0.1:3001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    location /api {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        client_max_body_size 500M;
        proxy_connect_timeout 1800s;
        proxy_send_timeout 1800s;
        proxy_read_timeout 1800s;
    }
}'''
    
    ssh_cmd(ssh, f'''cat > /etc/nginx/sites-available/influence << 'NGINXEOF'
{nginx_config}
NGINXEOF''')
    
    # 3. Enable site
    print("\n=== 3. Enabling site ===")
    ssh_cmd(ssh, "rm -f /etc/nginx/sites-enabled/default")
    ssh_cmd(ssh, "ln -sf /etc/nginx/sites-available/influence /etc/nginx/sites-enabled/")
    ssh_cmd(ssh, "nginx -t")
    ssh_cmd(ssh, "systemctl restart nginx")
    
    # 4. Get SSL certificate
    print("\n=== 4. Getting Let's Encrypt SSL ===")
    ssh_cmd(ssh, "certbot --nginx -d upl.synthnova.me --non-interactive --agree-tos --email admin@synthnova.me --redirect", timeout=120)
    
    # 5. Verify
    print("\n=== 5. Checking status ===")
    ssh_cmd(ssh, "systemctl status nginx | head -15")
    ssh_cmd(ssh, "certbot certificates")
    
    ssh.close()
    print("\n" + "="*50)
    print("✅ SSL Setup Complete!")
    print("="*50)
    print("\n🔒 https://upl.synthnova.me")
    print("\nФронтенд и API теперь доступны по HTTPS!")

if __name__ == "__main__":
    main()
