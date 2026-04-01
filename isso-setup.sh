#!/bin/bash
# ============================================================
# Isso setup script for comments.michaelbeijer.co.uk
# Run this on the Hetzner VPS as root (or with sudo)
# ============================================================
set -euo pipefail

DOMAIN="comments.michaelbeijer.co.uk"
ISSO_DIR="/opt/isso"
EMAIL="info@michaelbeijer.co.uk"

echo "=== 1. Creating Isso directory ==="
mkdir -p "$ISSO_DIR"
cd "$ISSO_DIR"

echo "=== 2. Writing isso.conf ==="
cat > isso.conf <<'CONF'
[general]
dbpath = /db/comments.db
host =
    https://michaelbeijer.co.uk
    https://www.michaelbeijer.co.uk
max-age = 15m
notify = smtp
reply-notifications = true
gravatar = false
latest-enabled = false

[moderation]
enabled = false

[guard]
enabled = true
ratelimit = 2
direct-reply = 3
require-author = false
require-email = false

[markup]
options = autolink, fenced-code
allowed-elements =
allowed-attributes =

[admin]
enabled = true
password = $ISSO_ADMIN_PASSWORD

[smtp]
host = smtp-relay.brevo.com
port = 587
security = starttls
username = $ISSO_SMTP_USERNAME
password = $ISSO_SMTP_PASSWORD
to = info@michaelbeijer.co.uk
from = info@michaelbeijer.co.uk
timeout = 10
CONF

echo "=== 3. Writing .env file ==="
echo "IMPORTANT: Edit .env with your actual credentials before starting!"
cat > .env <<'ENV'
ISSO_ADMIN_PASSWORD=CHANGE_ME
ISSO_SMTP_USERNAME=CHANGE_ME
ISSO_SMTP_PASSWORD=CHANGE_ME
ENV
chmod 600 .env

echo "=== 4. Writing docker-compose.yml ==="
cat > docker-compose.yml <<YAML
version: "3"

services:
  isso:
    image: ghcr.io/isso-comments/isso:release
    container_name: isso
    restart: always
    ports:
      - "127.0.0.1:8042:8080"
    volumes:
      - ./isso.conf:/config/isso.conf
      - ./db:/db
    env_file:
      - .env
YAML

echo "=== 5. Creating database directory ==="
mkdir -p db

echo "=== 6. Starting Isso container ==="
docker compose up -d

echo "=== 7. Setting up nginx reverse proxy ==="
cat > /etc/nginx/sites-available/isso <<'NGINX'
server {
    listen 80;
    server_name comments.michaelbeijer.co.uk;

    location / {
        proxy_pass http://127.0.0.1:8042;
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Script-Name "";
    }
}
NGINX

ln -sf /etc/nginx/sites-available/isso /etc/nginx/sites-enabled/isso
# Remove old Remark42 config if it exists
rm -f /etc/nginx/sites-enabled/remark42 /etc/nginx/sites-available/remark42
nginx -t && systemctl reload nginx

echo "=== 8. Getting SSL certificate ==="
certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos -m "$EMAIL"

echo "=== 9. Reloading nginx with SSL ==="
systemctl reload nginx

echo ""
echo "============================================"
echo "  Isso is live at https://${DOMAIN}"
echo "============================================"
echo ""
echo "Admin panel: https://${DOMAIN}/admin"
echo ""
echo "IMPORTANT: Stop the old Remark42 container:"
echo "  cd /opt/remark42 && docker compose down"
echo ""
