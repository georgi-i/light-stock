# AWS Lightsail Deployment Guide

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Architecture Overview](#architecture-overview)
3. [AWS Lightsail Setup](#aws-lightsail-setup)
4. [Security Configuration](#security-configuration)
5. [Database Setup](#database-setup)
6. [Application Deployment](#application-deployment)
7. [SSL/TLS Configuration](#ssltls-configuration)
8. [Backup Strategy](#backup-strategy)
9. [Monitoring & Logging](#monitoring--logging)
10. [Post-Deployment Checklist](#post-deployment-checklist)

---

## Prerequisites

### AWS Account Requirements
- ✅ AWS account with Lightsail access
- ✅ Admin user with:
  - MFA enabled
  - IAM policy limited to Lightsail resources only
- ✅ Budget alerts configured
- ✅ Billing alarms set up

### Local Requirements
- SSH key pair for server access
- Strong passwords for production secrets
- DuckDNS account (free): https://www.duckdns.org
- Email address for SSL certificate notifications

---

## Architecture Overview

```
┌─────────────────────────────────────────────────┐
│                                                 │
│  Internet                                       │
│     ↓                                           │
│  [Route 53]  ← Optional DNS                     │
│     ↓                                           │
│  [Static IP] ← Lightsail Static IP              │
│     ↓                                           │
│  ┌──────────────────────────────────┐          │
│  │   Lightsail Instance ($5/month)   │          │
│  │  ┌──────────────────────────┐    │          │
│  │  │  Nginx (Reverse Proxy)   │    │          │
│  │  │  - Port 443 (HTTPS)      │    │          │
│  │  │  - Port 80 (HTTP→HTTPS)  │    │          │
│  │  └────────┬─────────────────┘    │          │
│  │           ↓                       │          │
│  │  ┌──────────────────────────┐    │          │
│  │  │  Gunicorn (WSGI Server)  │    │          │
│  │  │  - Unix Socket           │    │          │
│  │  │  - 4 workers             │    │          │
│  │  └────────┬─────────────────┘    │          │
│  │           ↓                       │          │
│  │  ┌──────────────────────────┐    │          │
│  │  │  Flask Application       │    │          │
│  │  │  - Python 3.11+          │    │          │
│  │  │  - Virtual Environment   │    │          │
│  │  └────────┬─────────────────┘    │          │
│  │           ↓                       │          │
│  │  ┌──────────────────────────┐    │          │
│  │  │  SQLite Database         │    │          │
│  │  │  - File-based (ims.db)   │    │          │
│  │  │  - Encrypted backups     │    │          │
│  │  └──────────────────────────┘    │          │
│  └──────────────────────────────────┘          │
│                                                 │
│  [Lightsail Snapshots] ← Automated backups     │
│                                                 │
└─────────────────────────────────────────────────┘
```

**Recommended Lightsail Plan:** $3.50/month (Most Cost-Effective)
- 512 MB RAM
- 1 vCPU
- 20 GB SSD
- 1 TB transfer
- Ubuntu 22.04 LTS

**Note:** This is the cheapest Lightsail plan and sufficient for a small inventory system with moderate usage (5-10 concurrent users).

---

## AWS Lightsail Setup

### Step 1: Create Lightsail Instance

1. **Login to AWS Console**
   ```
   - Use admin account with MFA
   - Navigate to Lightsail service
   ```

2. **Create Instance**
   ```
   - Region: Choose closest to your users
   - Platform: Linux/Unix
   - Blueprint: OS Only → Ubuntu 22.04 LTS
   - Plan: $3.50/month (512 MB RAM, 1 vCPU, 20 GB SSD)
   - Instance name: ims-production
   ```

3. **Configure SSH Key**
   ```bash
   # Download the default SSH key from Lightsail
   # OR upload your own public key
   chmod 400 ~/Downloads/LightsailDefaultKey.pem
   ```

### Step 2: Attach Static IP

1. **Create Static IP**
   ```
   - Go to Networking tab
   - Create static IP
   - Name: ims-static-ip
   - Attach to: ims-production
   ```

2. **Note the Static IP** (e.g., 54.123.45.67)
   - You'll need this for DNS and SSL configuration

### Step 3: Configure Firewall

1. **Default Rules to Keep:**
   ```
   SSH     TCP   22    ✅ (restrict to your IP later)
   HTTP    TCP   80    ✅
   HTTPS   TCP   443   ✅
   ```

2. **Remove/Disable unused ports**

3. **Restrict SSH Access (Recommended):**
   ```
   - Edit SSH rule
   - Change from "All IP addresses" to your office/home IP
   - Example: 203.0.113.0/24
   ```

---

## Security Configuration

### Step 1: Initial Server Hardening

SSH into your instance:
```bash
ssh -i LightsailDefaultKey.pem ubuntu@54.123.45.67
```

**Update system:**
```bash
sudo apt update && sudo apt upgrade -y
sudo apt autoremove -y
```

### Step 2: Configure UFW Firewall

```bash
# Enable UFW
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH (change port if you modified it)
sudo ufw allow 22/tcp

# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable
sudo ufw status
```

### Step 3: Disable Root Login

```bash
# Edit SSH config
sudo nano /etc/ssh/sshd_config

# Ensure these settings:
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
AllowUsers ubuntu

# Restart SSH
sudo systemctl restart sshd
```

### Step 4: Install Fail2Ban

```bash
# Install fail2ban
sudo apt install fail2ban -y

# Create local config
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local
sudo nano /etc/fail2ban/jail.local

# Configure SSH protection:
[sshd]
enabled = true
port = 22
maxretry = 3
bantime = 3600

# Start fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### Step 5: Configure Automatic Security Updates

```bash
sudo apt install unattended-upgrades -y
sudo dpkg-reconfigure -plow unattended-upgrades
```

---

## Database Setup

### SQLite Database

SQLite is used for this deployment - no separate database server installation required. The database file (`ims.db`) will be stored in `/home/ims/app/`.

**Benefits:**
- ✅ Zero configuration required
- ✅ No separate database server to manage
- ✅ Lower resource usage (perfect for $5 Lightsail instance)
- ✅ Simple backups (just copy the file)
- ✅ Ideal for small to medium projects (thousands of products)

**Note:** The database file will be created automatically when you run migrations or initialization scripts.

---

## Application Deployment

### Step 1: Install Dependencies

```bash
# Install Python and system dependencies
sudo apt install python3.11 python3.11-venv python3-pip -y
sudo apt install nginx supervisor git -y
sudo apt install python3-dev build-essential -y
```

### Step 2: Create Application User

```bash
# Create dedicated user for the application
sudo useradd -m -s /bin/bash ims
sudo usermod -aG www-data ims
```

### Step 3: Deploy Application

```bash
# Switch to ims user
sudo su - ims

# Create application directory
mkdir -p /home/ims/app
cd /home/ims/app

# Clone or upload your application
# Option 1: Git clone (if using private repo, set up SSH keys)
git clone https://github.com/yourusername/ims.git .

# Option 2: Upload via SCP from your local machine
# (From your local machine):
# scp -i LightsailDefaultKey.pem -r light-stock/* ubuntu@54.123.45.67:/tmp/ims/
# Then on server:
# sudo mv /tmp/ims/* /home/ims/app/
# sudo chown -R ims:ims /home/ims/app/

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn

# Create .env file with production settings
nano .env
```

### Step 4: Configure Production Environment

```bash
# /home/ims/app/.env
FLASK_APP=run.py
FLASK_ENV=production
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')

# Database (SQLite - file will be created automatically)
DATABASE_URL=sqlite:////home/ims/app/ims.db

# Security
SECURITY_PASSWORD_SALT=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
SECURITY_TOTP_SECRETS={"1": "$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"}

# Session (HTTPS with DuckDNS)
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax
PERMANENT_SESSION_LIFETIME=1800

# Application Settings
DEFAULT_LANGUAGE=en
ITEMS_PER_PAGE=20
LOW_STOCK_THRESHOLD=10
```

### Step 5: Initialize Database

```bash
# Still as ims user
cd /home/ims/app
source venv/bin/activate

# Initialize database
flask db upgrade  # If using Flask-Migrate
# OR
python init_db.py

# Create admin user
flask create-user \
  --username admin \
  --email admin@yourdomain.com \
  --password "$(openssl rand -base64 32)" \
  --role admin \
  --language en

# Save the generated password securely!
```

### Step 6: Configure Gunicorn

```bash
# Create Gunicorn config
sudo nano /home/ims/app/gunicorn.conf.py
```

```python
# /home/ims/app/gunicorn.conf.py
import multiprocessing

# Server socket
bind = 'unix:/home/ims/app/ims.sock'
umask = 0o007

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1  # For 1 CPU = 3 workers
worker_class = 'sync'
worker_connections = 1000
timeout = 120
keepalive = 5

# Logging
accesslog = '/home/ims/app/logs/access.log'
errorlog = '/home/ims/app/logs/error.log'
loglevel = 'info'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = 'ims-gunicorn'

# Server mechanics
daemon = False
pidfile = '/home/ims/app/gunicorn.pid'

# Security
limit_request_line = 4096
limit_request_fields = 100
limit_request_field_size = 8190
```

```bash
# Create logs directory
mkdir -p /home/ims/app/logs
```

### Step 7: Configure Supervisor

```bash
# Exit from ims user
exit

# Create supervisor config
sudo nano /etc/supervisor/conf.d/ims.conf
```

```ini
[program:ims]
command=/home/ims/app/venv/bin/gunicorn -c /home/ims/app/gunicorn.conf.py run:app
directory=/home/ims/app
user=ims
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/home/ims/app/logs/supervisor_err.log
stdout_logfile=/home/ims/app/logs/supervisor_out.log
environment=PATH="/home/ims/app/venv/bin"
```

```bash
# Update supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl status ims
```

---

## Domain Setup (DuckDNS)

### Step 1: Register DuckDNS Domain

1. **Go to DuckDNS.org**: https://www.duckdns.org
2. **Sign in** with GitHub, Google, or other provider (no registration needed)
3. **Create subdomain**: Choose your subdomain (e.g., `yourcompany`)
   - Your domain will be: `yourcompany.duckdns.org`
4. **Add your Lightsail Static IP**: Enter your static IP in the "current ip" field
5. **Copy your token**: Save the DuckDNS token (you'll need it for auto-updates)

### Step 2: Setup DuckDNS Auto-Update (Optional)

DuckDNS needs to know your IP. Since Lightsail has a static IP, this is a one-time setup, but you can automate it:

```bash
# Create DuckDNS update script
sudo nano /home/ims/scripts/duckdns-update.sh
```

```bash
#!/bin/bash
# DuckDNS IP Update Script
echo url="https://www.duckdns.org/update?domains=yourcompany&token=YOUR_DUCKDNS_TOKEN&ip=" | curl -k -o /home/ims/logs/duck.log -K -
```

```bash
# Make executable
sudo chmod +x /home/ims/scripts/duckdns-update.sh
sudo chown ims:ims /home/ims/scripts/duckdns-update.sh

# Add to crontab (update every 5 minutes - optional for static IP)
sudo crontab -e -u ims
# Add: */5 * * * * /home/ims/scripts/duckdns-update.sh >/dev/null 2>&1
```

---

## Nginx Configuration

```bash
sudo nano /etc/nginx/sites-available/ims
```

**Important:** Replace `yourcompany.duckdns.org` with your actual DuckDNS subdomain throughout the configuration.

```nginx
# /etc/nginx/sites-available/ims
# Configuration for DuckDNS domain with HTTPS

# Rate limiting zones
limit_req_zone $binary_remote_addr zone=login_limit:10m rate=5r/m;
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=30r/m;
limit_req_zone $binary_remote_addr zone=general_limit:10m rate=100r/m;

# HTTP - Redirect to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name yourcompany.duckdns.org;

    # Allow Certbot validation
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    # Redirect all other traffic to HTTPS
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS - Main configuration
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name yourcompany.duckdns.org;

    # SSL Configuration (will be added by Certbot)
    # ssl_certificate /etc/letsencrypt/live/yourcompany.duckdns.org/fullchain.pem;
    # ssl_certificate_key /etc/letsencrypt/live/yourcompany.duckdns.org/privkey.pem;

    # SSL Settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    ssl_session_tickets off;

    # OCSP Stapling
    ssl_stapling on;
    ssl_stapling_verify on;
    resolver 8.8.8.8 8.8.4.4 valid=300s;
    resolver_timeout 5s;

    # Security Headers (HTTP-only)
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self';" always;

    # Logging
    access_log /var/log/nginx/ims_access.log combined buffer=32k flush=5s;
    error_log /var/log/nginx/ims_error.log warn;

    # Max upload size
    client_max_body_size 10M;
    client_body_timeout 30s;
    client_header_timeout 30s;

    # Buffer settings
    client_body_buffer_size 16K;
    client_header_buffer_size 1k;
    large_client_header_buffers 4 8k;

    # Root directory for static files
    root /home/ims/app;

    # Static files with caching
    location /static {
        alias /home/ims/app/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
        access_log off;

        # Security headers for static files
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-Frame-Options "DENY" always;
    }

    # Rate limiting for login endpoints
    location /auth/login {
        limit_req zone=login_limit burst=3 nodelay;
        limit_req_status 429;

        include proxy_params;
        proxy_pass http://unix:/home/ims/app/ims.sock;
    }

    # Rate limiting for 2FA
    location /auth/verify-2fa {
        limit_req zone=login_limit burst=5 nodelay;
        limit_req_status 429;

        include proxy_params;
        proxy_pass http://unix:/home/ims/app/ims.sock;
    }

    # Rate limiting for scanner API
    location /scanner/api/ {
        limit_req zone=api_limit burst=10 nodelay;
        limit_req_status 429;

        include proxy_params;
        proxy_pass http://unix:/home/ims/app/ims.sock;
    }

    # Health check endpoint (no rate limiting)
    location = /health {
        access_log off;
        include proxy_params;
        proxy_pass http://unix:/home/ims/app/ims.sock;
    }

    # Main application with general rate limiting
    location / {
        limit_req zone=general_limit burst=20 nodelay;
        limit_req_status 429;

        include proxy_params;
        proxy_pass http://unix:/home/ims/app/ims.sock;

        # Proxy settings
        proxy_redirect off;
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
        proxy_busy_buffers_size 8k;

        # Headers
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Port $server_port;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Deny access to hidden files
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
        return 404;
    }

    # Deny access to backup files
    location ~ ~$ {
        deny all;
        access_log off;
        log_not_found off;
        return 404;
    }

    # Deny access to sensitive files
    location ~ /\.(env|git|gitignore|htaccess|htpasswd) {
        deny all;
        access_log off;
        log_not_found off;
        return 404;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/ims /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default  # Remove default site

# Test configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

---

## SSL/TLS Configuration (Let's Encrypt)

### Obtain SSL Certificate with Certbot

Now that Nginx is configured with your DuckDNS domain, obtain a free SSL certificate:

```bash
# Obtain SSL certificate for your DuckDNS domain
sudo certbot --nginx -d yourcompany.duckdns.org

# Follow the prompts:
# 1. Enter your email address for urgent renewal notices
# 2. Agree to Terms of Service (A)
# 3. Choose whether to share email with EFF (Y/N)
# 4. Certbot will automatically configure SSL and HTTP->HTTPS redirect

# Verify certificate
sudo certbot certificates
```

**Certbot will automatically:**
- Update your Nginx configuration with SSL certificates
- Configure HTTP to HTTPS redirect
- Set up automatic certificate renewal (certificates renew every 90 days)

### Test SSL Configuration

```bash
# Test automatic renewal
sudo certbot renew --dry-run

# If successful, you'll see: "Congratulations, all simulated renewals succeeded"
```

### Verify Auto-Renewal Cron Job

```bash
# Check that renewal timer is active
sudo systemctl status certbot.timer

# Certbot auto-renewal runs twice daily
```

**Access your application:**
- Open browser to: `https://yourcompany.duckdns.org`
- You should see a valid SSL certificate (green padlock)

---

## Backup Strategy

### Step 1: Configure Database Backups

```bash
# Create backup script
sudo nano /home/ims/scripts/backup-database.sh
```

```bash
#!/bin/bash
# /home/ims/scripts/backup-database.sh

BACKUP_DIR="/home/ims/backups/database"
DATE=$(date +%Y%m%d_%H%M%S)
DB_FILE="/home/ims/app/ims.db"
RETENTION_DAYS=30
LOG_FILE="/home/ims/logs/backup.log"

# Create backup directory
mkdir -p $BACKUP_DIR
mkdir -p "$(dirname $LOG_FILE)"

# Check if database exists
if [ ! -f "$DB_FILE" ]; then
    echo "[$(date)] ERROR: Database file not found at $DB_FILE" >> "$LOG_FILE"
    exit 1
fi

# Start backup
echo "[$(date)] Starting SQLite database backup..." >> "$LOG_FILE"

# Backup database (SQLite file copy with compression)
if sqlite3 "$DB_FILE" ".backup /tmp/ims_backup_temp.db" && \
   gzip -c /tmp/ims_backup_temp.db > "$BACKUP_DIR/ims_db_$DATE.db.gz"; then

    # Clean up temp file
    rm -f /tmp/ims_backup_temp.db

    BACKUP_SIZE=$(du -h "$BACKUP_DIR/ims_db_$DATE.db.gz" | cut -f1)
    echo "[$(date)] ✓ Backup completed: ims_db_$DATE.db.gz ($BACKUP_SIZE)" >> "$LOG_FILE"

    # Remove old backups
    DELETED=$(find "$BACKUP_DIR" -name "ims_db_*.db.gz" -mtime +$RETENTION_DAYS -delete -print | wc -l)
    if [ "$DELETED" -gt 0 ]; then
        echo "[$(date)] Removed $DELETED old backup(s)" >> "$LOG_FILE"
    fi

    # Verify backup integrity
    if gzip -t "$BACKUP_DIR/ims_db_$DATE.db.gz" > /dev/null 2>&1; then
        echo "[$(date)] ✓ Backup integrity verified" >> "$LOG_FILE"
    else
        echo "[$(date)] ✗ WARNING: Backup integrity check failed!" >> "$LOG_FILE"
    fi

else
    echo "[$(date)] ✗ ERROR: Backup failed!" >> "$LOG_FILE"
    rm -f /tmp/ims_backup_temp.db
    exit 1
fi

# Display backup summary
TOTAL_BACKUPS=$(ls -1 "$BACKUP_DIR"/ims_db_*.db.gz 2>/dev/null | wc -l)
TOTAL_SIZE=$(du -sh "$BACKUP_DIR" 2>/dev/null | cut -f1)
echo "[$(date)] Total backups: $TOTAL_BACKUPS (Total size: $TOTAL_SIZE)" >> "$LOG_FILE"

exit 0
```

```bash
# Make executable
sudo chmod +x /home/ims/scripts/backup-database.sh
sudo chown ims:ims /home/ims/scripts/backup-database.sh

# Create backup directories
sudo mkdir -p /home/ims/backups/database
sudo mkdir -p /home/ims/logs
sudo chown -R ims:ims /home/ims/backups/
sudo chown -R ims:ims /home/ims/logs/

# Test backup
sudo -u ims /home/ims/scripts/backup-database.sh
```

### Step 2: Configure Automated Backups

```bash
# Add to crontab
sudo crontab -e -u ims

# Add these lines:
# Daily database backup at 2 AM
0 2 * * * /home/ims/scripts/backup-database.sh

# Weekly full application backup at 3 AM on Sundays
0 3 * * 0 tar -czf /home/ims/backups/app_$(date +\%Y\%m\%d).tar.gz -C /home/ims app --exclude='app/venv' --exclude='app/__pycache__'
```

### Step 3: Configure Lightsail Snapshots

1. **Automatic Snapshots:**
   ```
   - Go to Lightsail Console
   - Select your instance
   - Go to "Snapshots" tab
   - Enable automatic snapshots
   - Set time: Daily at 04:00 UTC
   - Retention: Keep 7 snapshots
   ```

2. **Manual Snapshots:**
   - Take before major updates
   - Label clearly: "ims-before-v2-update"

---

## Monitoring & Logging

### Step 1: Configure Log Rotation

```bash
sudo nano /etc/logrotate.d/ims
```

```
/home/ims/app/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 ims ims
    sharedscripts
    postrotate
        supervisorctl restart ims > /dev/null
    endscript
}

/var/log/nginx/ims_*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data adm
    sharedscripts
    postrotate
        [ -f /var/run/nginx.pid ] && kill -USR1 `cat /var/run/nginx.pid`
    endscript
}

# Fail2ban logs (aggressive rotation for minimal storage)
/var/log/fail2ban.log {
    daily
    rotate 3
    compress
    delaycompress
    notifempty
    missingok
    postrotate
        fail2ban-client flushlogs >/dev/null 2>&1 || true
    endscript
}
```

**Note:** Fail2ban logs are rotated aggressively (3-day retention) to minimize storage usage on the 20 GB disk. The setup.sh script automatically configures this.

### Step 2: System Monitoring

```bash
# Install monitoring tools
sudo apt install htop iotop nethogs -y

# Check system resources
htop

# Monitor disk space
df -h

# Check application logs
tail -f /home/ims/app/logs/error.log
tail -f /var/log/nginx/ims_error.log
```

### Step 3: Create Health Check Endpoint

Add to your Flask app:

```python
# In app/routes.py
@main_bp.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Check database connection (SQLite)
        from sqlalchemy import text
        db.session.execute(text('SELECT 1'))
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500
```

### Step 4: Setup External Monitoring (Optional)

Consider using free monitoring services:
- **UptimeRobot** (free plan): Monitor uptime
- **Papertrail** (free plan): Centralized logging
- **AWS CloudWatch**: Basic metrics included with Lightsail

---

## Post-Deployment Checklist

### Security Verification

- [ ] SSH access limited to specific IPs
- [ ] Root login disabled
- [ ] Password authentication disabled
- [ ] Fail2Ban configured and running
- [ ] UFW firewall enabled
- [ ] DuckDNS domain configured and resolving
- [ ] SSL certificate installed and valid
- [ ] HTTPS enforced (HTTP redirects to HTTPS)
- [ ] SSL auto-renewal tested
- [ ] Security headers configured in Nginx
- [ ] Strong SECRET_KEY and SECURITY_PASSWORD_SALT set
- [ ] Database password is strong and unique
- [ ] Admin user created via CLI only
- [ ] Registration disabled
- [ ] 2FA available for users
- [ ] Session timeout configured (30 minutes)
- [ ] Rate limiting working on all endpoints

### Application Verification

- [ ] Application running under supervisor
- [ ] Gunicorn serving application correctly
- [ ] Static files served by Nginx
- [ ] Database migrations completed
- [ ] Admin user can login
- [ ] 2FA setup works
- [ ] All routes accessible
- [ ] Bulgarian translation working
- [ ] Scanner functionality tested
- [ ] Stock movements recording correctly
- [ ] Audit logs working

### Backup Verification

- [ ] Daily database backups running
- [ ] Weekly application backups configured
- [ ] Lightsail automatic snapshots enabled
- [ ] Backup restoration tested
- [ ] Backup retention policy set

### Monitoring Verification

- [ ] Log rotation configured
- [ ] Health check endpoint responding
- [ ] Error logs monitored
- [ ] Disk space monitoring
- [ ] Uptime monitoring configured (optional)

### Documentation

- [ ] Admin credentials stored securely (password manager)
- [ ] Database credentials documented
- [ ] SSL renewal process documented
- [ ] Backup restoration procedure documented
- [ ] Incident response plan created

---

## Maintenance Tasks

### Weekly
- Review error logs
- Check disk space usage
- Verify backups completed successfully
- Review failed login attempts

### Monthly
- Apply security updates: `sudo apt update && sudo apt upgrade -y`
- Review access logs for anomalies
- Test backup restoration
- Review user accounts and permissions

### Quarterly
- Full security audit
- Review and update firewall rules
- Performance optimization review
- Capacity planning assessment

---

## Troubleshooting

### Application not starting
```bash
# Check supervisor status
sudo supervisorctl status ims

# Check error logs
tail -f /home/ims/app/logs/error.log
tail -f /home/ims/app/logs/supervisor_err.log

# Restart application
sudo supervisorctl restart ims
```

### SSL certificate issues
```bash
# Check certificate status
sudo certbot certificates

# Test renewal
sudo certbot renew --dry-run

# Force renewal (if needed)
sudo certbot renew --force-renewal

# Check Certbot timer
sudo systemctl status certbot.timer
```

### Nginx not serving site
```bash
# Check Nginx status
sudo systemctl status nginx

# Test Nginx configuration
sudo nginx -t

# Check error log
sudo tail -f /var/log/nginx/error.log

# Restart Nginx
sudo systemctl restart nginx
```

### DuckDNS domain not resolving
```bash
# Check DNS resolution
nslookup yourcompany.duckdns.org
dig yourcompany.duckdns.org

# Verify IP matches your static IP
# If not, update DuckDNS with your current IP

# Test from browser (clear DNS cache)
# Chrome: chrome://net-internals/#dns
```

### Database connection issues
```bash
# Check if database file exists
ls -lh /home/ims/app/ims.db

# Check database permissions
sudo -u ims sqlite3 /home/ims/app/ims.db "SELECT name FROM sqlite_master WHERE type='table';"

# Fix permissions if needed
sudo chown ims:ims /home/ims/app/ims.db
sudo chmod 644 /home/ims/app/ims.db

# Restart application
sudo supervisorctl restart ims
```

### High memory usage
```bash
# Check processes
htop

# Restart application
sudo supervisorctl restart ims

# Check for memory leaks in logs
grep -i "memory" /home/ims/app/logs/error.log
```

---

## Cost Estimation

### Monthly Costs (Most Cost-Optimized Setup with HTTPS)
- Lightsail Instance ($3.50/month): **$3.50**
- Static IP (included): **$0.00**
- Data Transfer (1TB included): **$0.00**
- Automatic Snapshots ($0.05/GB): ~**$1.00**
- DuckDNS Domain: **$0.00** (free forever)
- Let's Encrypt SSL: **$0.00** (free forever)
- **Total: ~$4.50/month**

### Optional Add-ons (If Needed)
- Paid custom domain (instead of DuckDNS): $10-15/year (~$1/month)
- Email service: $0-10/month

**Annual Cost: ~$54/year** (most cost-effective cloud deployment with HTTPS!)

---

## Emergency Contacts & Resources

### AWS Support
- AWS Lightsail Documentation: https://lightsail.aws.amazon.com/ls/docs
- AWS Support Center: https://console.aws.amazon.com/support

### Application Support
- Flask Security: https://flask-security-too.readthedocs.io
- SQLite Documentation: https://www.sqlite.org/docs.html
- SQLAlchemy Documentation: https://docs.sqlalchemy.org/

### Security Resources
- Let's Encrypt Status: https://letsencrypt.status.io/
- SSL Labs Test: https://www.ssllabs.com/ssltest/
- Security Headers Check: https://securityheaders.com/

---

## Migration Checklist Summary

1. ✅ Create Lightsail instance
2. ✅ Attach static IP
3. ✅ Configure firewall
4. ✅ Harden server security
5. ✅ Deploy application (SQLite - no separate database setup needed!)
6. ✅ Configure Gunicorn and Supervisor
7. ✅ Setup Nginx reverse proxy
8. ✅ Obtain SSL certificate
9. ✅ Configure backups
10. ✅ Setup monitoring
11. ✅ Verify all security measures
12. ✅ Test application thoroughly
13. ✅ Document everything

**Estimated Setup Time:** 2-4 hours for first deployment (simplified with SQLite!)

---

*Document Version: 1.0*
*Last Updated: 2026-01-04*
*Maintained by: IMS Admin Team*
