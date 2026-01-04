# IMS Troubleshooting Guide

## Fixed: systemd service won't start

### Problem 1: Gunicorn could not be executed
```
The process /home/ims/app/venv/bin/gunicorn could not be executed
```

**Root Cause:** Overly strict security settings blocked access to the virtual environment.

**Solution Applied:**
- Changed `ProtectHome=true` → `ProtectHome=read-only`
- Changed `ProtectSystem=strict` → `ProtectSystem=full`
- Enhanced `PATH` environment variable

### Problem 2: Mount namespacing error
```
Failed to set up mount namespacing: /run/systemd/unit-root/home/ims/app/gunicorn.pid: No such file or directory
```

**Root Cause:** Systemd tried to mount the PID file before it existed.

**Solution Applied:**
- Moved PID file from `/home/ims/app/gunicorn.pid` → `/home/ims/logs/gunicorn.pid`
- The `/home/ims/logs` directory is already in `ReadWritePaths` and exists before service starts

### Steps to Fix on Server

1. **Redeploy the updated configuration:**
   ```bash
   ./deploy/deploy.sh [your-server-ip] [your-pem-file]
   ```

   OR manually update on the server:

2. **SSH into your server:**
   ```bash
   ssh -i ~/.ssh/your-key.pem ubuntu@your-server-ip
   ```

3. **Update the systemd service file:**
   ```bash
   sudo cp /home/ims/app/deploy/ims.service /etc/systemd/system/
   sudo systemctl daemon-reload
   ```

4. **Verify the virtual environment exists:**
   ```bash
   ls -la /home/ims/app/venv/bin/gunicorn
   ```

   If it doesn't exist:
   ```bash
   cd /home/ims/app
   ./deploy/post-deploy.sh
   ```

5. **Start the service:**
   ```bash
   sudo systemctl start ims
   sudo systemctl status ims
   ```

6. **Check the logs if it still fails:**
   ```bash
   # Systemd logs
   sudo journalctl -u ims -n 50 --no-pager

   # Application logs
   tail -f /home/ims/logs/error.log
   tail -f /home/ims/logs/access.log
   ```

## Common Issues and Solutions

### 1. Nginx Shows Default Page Instead of Application

**Symptom:** Accessing public IP shows nginx welcome page, but localhost works.

**Root Cause:** Nginx is not configured to proxy to the application.

**Solution:**
```bash
# SSH into server
ssh -i ~/.ssh/your-key.pem ubuntu@your-server-ip

# Configure nginx with your DuckDNS domain
cd /home/ims/app
sudo nano deploy/nginx.conf
# Replace 'yourcompany.duckdns.org' with your actual domain

# Install the configuration
sudo cp deploy/nginx.conf /etc/nginx/sites-available/ims
sudo ln -sf /etc/nginx/sites-available/ims /etc/nginx/sites-enabled/ims
sudo rm -f /etc/nginx/sites-enabled/default

# Test and reload nginx
sudo nginx -t
sudo systemctl reload nginx
```

### 2. Gunicorn Socket Issues

**Symptom:**
```
502 Bad Gateway
connect() to unix:/run/ims/ims.sock failed
```

**Solutions:**

a) **Check if socket exists:**
```bash
ls -la /run/ims/ims.sock
```

If it doesn't exist, the service may not be running:
```bash
sudo systemctl status ims
sudo systemctl start ims
```

b) **Check socket permissions:**
```bash
stat /run/ims/ims.sock
# Should show: ims:www-data
```

If permissions are wrong, restart the service (systemd will recreate it correctly):
```bash
sudo systemctl restart ims
```

c) **Remove stale socket:**
```bash
sudo systemctl stop ims
sudo rm -f /run/ims/ims.sock
sudo systemctl start ims
```

**Note:** The socket is now in `/run/ims/` (standard location) instead of `/home/ims/app/` to work with systemd security settings.

### 3. Virtual Environment Missing
**Symptom:** `gunicorn: command not found` or similar

**Solution:**
```bash
cd /home/ims/app
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Python 3.11 Not Available
**Symptom:** `python3.11: command not found`

**Solution:**
```bash
# Install Python 3.11 on Ubuntu
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev -y
```

OR the post-deploy script will now automatically fall back to `python3`.

### 3. Permission Issues
**Symptom:**
```
[Errno 13] Permission denied: '/home/ims/app/deploy/gunicorn.conf.py'
```

**Root Cause:** Files extracted during deployment are owned by the deployment user (ubuntu) instead of the application user (ims).

**Solution:**
```bash
# Fix ownership and permissions
cd /home/ims/app
sudo chown -R ims:www-data /home/ims/app
sudo chown -R ims:www-data /home/ims/logs
sudo chown -R ims:www-data /home/ims/backups
sudo chmod -R 755 /home/ims/app
sudo chmod -R 755 /home/ims/logs

# Restart the service
sudo systemctl restart ims
```

**Note:** The post-deploy script now automatically fixes permissions, so redeploying will fix this issue.

### 4. Database Not Initialized
**Symptom:** Application starts but shows database errors

**Solution:**
```bash
cd /home/ims/app
source venv/bin/activate
flask --app run:app db upgrade
```

### 5. .env File Missing or Incorrect
**Symptom:** Configuration errors, secret key not set

**Solution:**
```bash
cd /home/ims/app
nano .env
```

Ensure you have at minimum:
```env
FLASK_APP=run.py
SECRET_KEY=your-very-long-random-secret-key-here
DATABASE_URL=sqlite:///instance/ims.db
FLASK_ENV=production
```

Generate a secure secret key:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

## Useful Diagnostic Commands

### Check Service Status
```bash
sudo systemctl status ims
sudo systemctl is-active ims
```

### View Logs
```bash
# Last 50 lines of systemd logs
sudo journalctl -u ims -n 50

# Follow systemd logs in real-time
sudo journalctl -u ims -f

# Application error logs
tail -f /home/ims/logs/error.log

# Application access logs
tail -f /home/ims/logs/access.log
```

### Test Gunicorn Manually
```bash
cd /home/ims/app
source venv/bin/activate
gunicorn --config deploy/gunicorn.conf.py run:app
```

### Check Nginx
```bash
sudo nginx -t                    # Test config
sudo systemctl status nginx      # Check status
sudo tail -f /var/log/nginx/error.log
```

### Check Sockets and Ports
```bash
# Check if gunicorn socket exists
ls -la /run/ims/ims.sock

# Check socket permissions (should be owned by ims:www-data)
stat /run/ims/ims.sock

# Check if nginx is listening on port 80/443
sudo netstat -tlnp | grep :80
sudo netstat -tlnp | grep :443
```

### Restart Services
```bash
# Restart IMS application
sudo systemctl restart ims

# Restart Nginx
sudo systemctl restart nginx

# Reload Nginx without downtime
sudo nginx -t && sudo systemctl reload nginx
```

## Complete Fresh Install

If everything is broken, start fresh:

```bash
# Stop services
sudo systemctl stop ims
sudo systemctl disable ims

# Clean up
sudo rm -rf /home/ims/app
sudo rm /etc/systemd/system/ims.service

# Redeploy
./deploy/deploy.sh [server-ip] [pem-file]
```

## Getting Help

If issues persist:

1. Check all logs mentioned above
2. Verify all environment variables in `.env`
3. Ensure Python 3.11+ is installed
4. Check disk space: `df -h`
5. Check memory: `free -h`
6. Review security group settings (ports 22, 80, 443 open)
