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
        print(out[:1500])
    if err:
        print(f"STDERR: {err[:500]}")

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username=username, password=password, timeout=30)

# Check if JS file is accessible
print("=== Check JS file access ===")
ssh_cmd(ssh, "curl -sI http://localhost:3001/static/js/main.3aa1925d.js | head -10")

# Try serving with nginx directly instead of pm2 serve
print("\n=== Switching to Nginx static serving ===")

nginx_config = '''server {
    listen 80;
    server_name upl.synthnova.me;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name upl.synthnova.me;

    ssl_certificate /etc/letsencrypt/live/upl.synthnova.me/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/upl.synthnova.me/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    root /opt/influence-frontend/build;
    index index.html;

    # Frontend - static files
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Static assets with proper MIME types
    location /static/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Backend API proxy
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

# Stop pm2 serve for frontend (not needed anymore)
print("\n=== Stop PM2 frontend serve ===")
ssh_cmd(ssh, "pm2 delete influence-frontend || true")
ssh_cmd(ssh, "pm2 save")

# Test nginx config and restart
print("\n=== Restart Nginx ===")
ssh_cmd(ssh, "nginx -t")
ssh_cmd(ssh, "systemctl restart nginx")

# Test
print("\n=== Test HTTPS ===")
ssh_cmd(ssh, "curl -sI https://upl.synthnova.me/static/js/main.3aa1925d.js | head -10")
ssh_cmd(ssh, "curl -s https://upl.synthnova.me/ | head -5")

ssh.close()
print("\n✅ Done! Try https://upl.synthnova.me now")
