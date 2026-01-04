# IMS Deployment Guide

Complete guide for deploying the Inventory Management System to AWS Lightsail.

## 📋 Prerequisites

### On Your Local Machine
- SSH access configured to your Lightsail instance
- SSH key added to the server

### On AWS Lightsail Server
- Fresh Ubuntu 22.04 instance
- Initial setup completed (run `setup.sh` first if not done)

## 🚀 Quick Deployment

### First-Time Deployment

1. **Make deployment scripts executable** (one-time):
   ```bash
   chmod +x deploy/deploy.sh deploy/post-deploy.sh
   ```

2. **Run initial server setup** (one-time, requires sudo):
   ```bash
   # SSH into your Lightsail instance
   ssh ims@your-server-ip

   # Upload and run setup script
   sudo bash /path/to/setup.sh
   ```

3. **Deploy the application**:
   ```bash
   # From your local machine
   cd /path/to/light-stock
   ./deploy/deploy.sh your-server-ip
   # or
   ./deploy/deploy.sh ims@your-server-ip
   ```

4. **Configure environment variables**:
   ```bash
   ssh ims@your-server-ip
   cd /home/ims/app
   nano .env
   ```

   Update with your production values:
   ```env
   FLASK_ENV=production
   SECRET_KEY=your-secret-key-here
   DATABASE_URL=sqlite:////home/ims/app/instance/ims.db
   # Add other configuration as needed
   ```

5. **Configure Nginx** (one-time):
   ```bash
   sudo cp /home/ims/app/deploy/nginx.conf /etc/nginx/sites-available/ims
   sudo ln -s /etc/nginx/sites-available/ims /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

6. **Set up SSL with Let's Encrypt** (one-time):
   ```bash
   sudo certbot --nginx -d your-domain.com
   ```

### Subsequent Deployments

Once everything is set up, deployments are simple:

```bash
./deploy/deploy.sh your-server-ip
```

That's it! The script will:
- Package your code
- Upload to server
- Extract files
- Install dependencies
- Run migrations
- Restart the application

## 📦 What Gets Deployed

### Included Files
```
✅ app/                    (Application code)
✅ config.py               (Configuration)
✅ run.py                  (Application entry point)
✅ requirements.txt        (Python dependencies)
✅ migrations/             (Database migrations)
✅ translations/           (i18n files)
✅ deploy/                 (Deployment scripts)
✅ messages.pot            (Translation template)
```

### Excluded Files (automatically)
```
❌ venv/                   (Virtual environment)
❌ __pycache__/            (Python cache)
❌ *.pyc, *.pyo            (Compiled Python)
❌ .env                    (Local environment)
❌ *.db, *.sqlite*         (Local database)
❌ .DS_Store               (macOS files)
❌ .git/                   (Git repository)
❌ .vscode/, .idea/        (IDE configs)
❌ *.log                   (Log files)
```

## 🔧 Deployment Script Details

### deploy.sh
Main deployment script run from your local machine.

**What it does:**
1. Tests SSH connection
2. Creates deployment package (excludes unnecessary files)
3. Uploads to server `/tmp/`
4. Extracts to `/home/ims/app/`
5. Preserves existing `.env` file
6. Calls `post-deploy.sh` on server
7. Cleans up temporary files

**Usage:**
```bash
./deploy/deploy.sh your-server-ip
./deploy/deploy.sh ims@your-server-ip
```

### post-deploy.sh
Server-side script that runs automatically after code upload.

**What it does:**
1. Creates/updates Python virtual environment
2. Installs/updates Python dependencies
3. Compiles translations
4. Runs database migrations
5. Creates necessary directories
6. Restarts the application service
7. Reloads Nginx

**Note:** This script is called automatically by `deploy.sh`.

## 🗂️ Server Directory Structure

```
/home/ims/
├── app/                    # Application code (deployed here)
│   ├── venv/              # Python virtual environment (created on server)
│   ├── instance/          # SQLite database directory
│   ├── app/               # Your application code
│   ├── migrations/        # Database migrations
│   └── .env               # Production environment variables
├── logs/                   # Application logs
│   ├── ims.log            # Application log
│   ├── access.log         # Gunicorn access log
│   └── error.log          # Gunicorn error log
├── backups/               # Database backups
│   └── database/          # SQLite backups
└── scripts/               # Utility scripts
```

## 🔍 Troubleshooting

### Check Application Status
```bash
ssh ims@your-server-ip 'sudo systemctl status ims'
```

### View Application Logs
```bash
ssh ims@your-server-ip 'tail -f /home/ims/logs/ims.log'
```

### View Gunicorn Error Logs
```bash
ssh ims@your-server-ip 'tail -f /home/ims/logs/error.log'
```

### Restart Application
```bash
ssh ims@your-server-ip 'sudo systemctl restart ims'
```

### Check Nginx Configuration
```bash
ssh ims@your-server-ip 'sudo nginx -t'
```

### View Nginx Logs
```bash
ssh ims@your-server-ip 'sudo tail -f /var/log/nginx/error.log'
```

### Database Migrations Failed
```bash
ssh ims@your-server-ip
cd /home/ims/app
source venv/bin/activate
flask --app run:app db upgrade
```

## 🔐 Security Checklist

Before going live:
- [ ] `.env` file configured with strong SECRET_KEY
- [ ] Database backups configured (use `backup-database.sh`)
- [ ] SSL certificate installed
- [ ] Firewall (UFW) enabled
- [ ] Fail2Ban active
- [ ] SSH password authentication disabled
- [ ] Regular security updates enabled
- [ ] Application logs being monitored

## 🔄 Rollback Procedure

If a deployment fails, you can rollback:

1. **Check previous deployment archives:**
   ```bash
   ssh ims@your-server-ip 'ls -lh /tmp/ims-deploy-*.tar.gz'
   ```

2. **Manually extract previous version:**
   ```bash
   ssh ims@your-server-ip
   cd /home/ims/app
   tar -xzf /tmp/ims-deploy-YYYYMMDD-HHMMSS.tar.gz
   sudo systemctl restart ims
   ```

## 📊 Monitoring

### Check Service Status
```bash
# Application status
sudo systemctl status ims

# Nginx status
sudo systemctl status nginx

# Disk usage
df -h

# Memory usage
free -h

# Process monitoring
htop
```

### Useful Commands
```bash
# Follow logs in real-time
sudo journalctl -u ims -f

# View last 100 log lines
sudo journalctl -u ims -n 100

# Check for errors only
sudo journalctl -u ims -p err
```

## 🆘 Common Issues

### "Cannot connect to server"
- Verify server IP address
- Check SSH key is configured: `ssh-add -l`
- Ensure server is running in Lightsail console

### "Application not running"
- Check logs: `sudo journalctl -u ims -n 50`
- Verify `.env` file exists and is valid
- Check database permissions
- Restart service: `sudo systemctl restart ims`

### "502 Bad Gateway"
- Application service is down
- Check `sudo systemctl status ims`
- Review error logs: `tail -f /home/ims/logs/error.log`

### "Permission denied"
- Ensure you're using the `ims` user for deployment
- Check file permissions: `ls -la /home/ims/app`

## 📚 Additional Resources

- [Initial Server Setup](./setup.sh) - First-time server configuration
- [Nginx Configuration](./nginx.conf) - Web server configuration
- [Database Backup](./backup-database.sh) - Automated backups
- [Cost Optimization](./COST_OPTIMIZED.md) - Reduce hosting costs
- [SQLite Migration](./SQLITE_MIGRATION.md) - Database setup

---

**Need help?** Check the main [README.md](../README.md) or review server logs for details.
