#!/bin/bash
#
# AWS Lightsail IMS - Initial Server Setup Script
# Run this script as root/sudo on a fresh Ubuntu 22.04 Lightsail instance
#
# Usage: sudo bash setup.sh
#

set -e  # Exit on any error

echo "========================================="
echo "IMS - AWS Lightsail Initial Setup"
echo "========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root or with sudo"
    exit 1
fi

# Update system
echo "[1/10] Updating system packages..."
apt update && apt upgrade -y
apt autoremove -y

# Install essential packages
echo "[2/10] Installing essential packages..."
apt install -y \
    python3.11 \
    python3.11-venv \
    python3-pip \
    sqlite3 \
    nginx \
    supervisor \
    git \
    python3-dev \
    build-essential \
    ufw \
    fail2ban \
    certbot \
    python3-certbot-nginx \
    unattended-upgrades \
    htop \
    iotop \
    nethogs

# Configure UFW firewall
echo "[3/10] Configuring firewall..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

# Configure Fail2Ban
echo "[4/10] Configuring Fail2Ban..."
cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local
cat > /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[sshd]
enabled = true
port = 22
maxretry = 3
bantime = 3600
EOF

# Configure aggressive log rotation for fail2ban (minimize storage)
cat > /etc/logrotate.d/fail2ban << 'EOF'
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
EOF

# Reduce fail2ban log verbosity
sed -i 's/loglevel = INFO/loglevel = NOTICE/' /etc/fail2ban/fail2ban.conf 2>/dev/null || true

systemctl enable fail2ban
systemctl restart fail2ban

# Configure automatic security updates
echo "[5/10] Enabling automatic security updates..."
dpkg-reconfigure -plow unattended-upgrades

# Create application user
echo "[6/10] Creating application user..."
if ! id -u ims > /dev/null 2>&1; then
    useradd -m -s /bin/bash ims
    usermod -aG www-data ims
    echo "User 'ims' created"
else
    echo "User 'ims' already exists"
fi

# Create directory structure
echo "[7/10] Creating directory structure..."
sudo -u ims mkdir -p /home/ims/app
sudo -u ims mkdir -p /home/ims/backups/database
sudo -u ims mkdir -p /home/ims/scripts
sudo -u ims mkdir -p /home/ims/logs

# SQLite - no setup needed (file-based database)
echo "[8/10] SQLite ready (no server installation required)..."
echo "Database will be created automatically on first app run"

# Secure SSH
echo "[9/10] Hardening SSH configuration..."
sed -i 's/#PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sed -i 's/PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
systemctl restart sshd

# Display summary
echo ""
echo "========================================="
echo "[10/10] Setup Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Deploy application code"
echo "2. Configure Nginx"
echo "3. Obtain SSL certificate"
echo "4. Initialize SQLite database (will be created automatically)"
echo ""
echo "IMPORTANT SECURITY NOTES:"
echo "- Root login is now DISABLED"
echo "- Password authentication is DISABLED"
echo "- Firewall (UFW) is ENABLED"
echo "- Fail2Ban is ACTIVE"
echo "- Make sure you have SSH key access before logging out!"
echo ""
echo "Application user: ims"
echo "Application directory: /home/ims/app"
echo ""
