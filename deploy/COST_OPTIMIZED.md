# Cost-Optimized AWS Lightsail Deployment

## Overview
This deployment is configured for **maximum cost efficiency** while maintaining security and functionality. Perfect for small businesses, personal projects, or testing environments.

## Total Monthly Cost: **~$4.50/month** (~$54/year)

### Cost Breakdown
- **Lightsail Instance** ($3.50/month): Smallest plan (512 MB RAM, 1 vCPU, 20 GB SSD, 1 TB transfer)
- **Static IP**: $0 (included with instance)
- **Data Transfer**: $0 (1 TB included)
- **Automated Snapshots**: ~$1.00/month (20 GB @ $0.05/GB)
- **Domain**: $0 (no custom domain - access via IP)
- **SSL Certificate**: $0 (HTTP-only or optional free domain)

## Configuration Highlights

### Instance Specifications
```
Plan: $3.50/month
RAM: 512 MB
vCPU: 1 core
Storage: 20 GB SSD
Transfer: 1 TB/month
OS: Ubuntu 22.04 LTS
```

**Note:** This is AWS Lightsail's cheapest plan and sufficient for:
- 5-10 concurrent users
- Thousands of products
- Moderate daily usage
- Small team inventory management

### Database
- **SQLite** (file-based, no separate server)
- Zero installation or configuration
- Zero additional cost
- Perfect for small to medium databases

### Access Method
- **DuckDNS domain**: `https://yourcompany.duckdns.org`
- Free domain with HTTPS
- Let's Encrypt SSL certificate
- No DNS costs

### Security
Despite being cost-optimized, full security is maintained:
- ✅ HTTPS with Let's Encrypt SSL
- ✅ Valid SSL certificate (not self-signed)
- ✅ UFW Firewall configured
- ✅ Fail2Ban active (SSH brute force protection)
- ✅ Rate limiting on all endpoints
- ✅ SSH key-only authentication
- ✅ HSTS enabled (force HTTPS)
- ✅ Security headers configured
- ✅ CSRF protection
- ✅ 2FA available
- ✅ Automated daily backups

## DuckDNS Domain with HTTPS

### Free Domain + SSL Certificate
This deployment uses **DuckDNS** for a free subdomain and **Let's Encrypt** for a free SSL certificate:

✅ **What You Get:**
- Free subdomain: `yourcompany.duckdns.org`
- Valid SSL certificate (trusted by all browsers)
- Automatic certificate renewal (every 90 days)
- HTTPS encryption
- No cost forever

### Setup Process (15 minutes)
1. **Register at DuckDNS.org** (free, no email required)
2. **Choose subdomain** (e.g., `myims.duckdns.org`)
3. **Point to Lightsail IP** (one-time setup)
4. **Configure Nginx** (use provided config file)
5. **Run Certbot** to get SSL certificate
6. **Access via HTTPS** - done!

See `deploy/DUCKDNS_SETUP.md` for detailed step-by-step instructions.

## Performance Expectations

### Suitable For:
✅ Small businesses (5-10 employees)
✅ Personal projects and testing
✅ Product databases up to 10,000+ items
✅ Moderate daily usage (100-500 requests/day)
✅ Single-location operations

### Not Suitable For:
❌ High-traffic websites (>1,000 concurrent users)
❌ Large databases (>50,000 products with images)
❌ Heavy concurrent write operations
❌ Multi-location with high data sync requirements

## Resource Optimization

### Instance Optimization (512 MB RAM)
The deployment is optimized for low memory:
- **Gunicorn**: 3 workers (2*CPU + 1)
- **Nginx**: Minimal buffer sizes
- **SQLite**: No separate database server memory usage
- **Supervisor**: Lightweight process management

### Storage Optimization (20 GB SSD)
```
Space Allocation:
- System & packages: ~5 GB
- Application code: <100 MB
- SQLite database: ~100 MB (for 5,000 products)
- Backups (30 days): ~1-2 GB
- Logs: ~500 MB (with rotation)
- Available: ~13 GB free
```

### Transfer Optimization (1 TB/month)
With 1 TB monthly transfer, you can handle:
- ~1,000,000 page views/month (average 1 MB per page load)
- Or ~10,000 page views/day
- More than sufficient for small inventory systems

## Scaling Up (When Needed)

### When to Upgrade

Upgrade to $5/month plan (1 GB RAM) if:
- Running out of memory (check with `free -h`)
- Need more concurrent users (10-20)
- Database growing beyond 100 MB
- Application feels slow

### When to Switch to PostgreSQL

Consider PostgreSQL if:
- Database exceeds 1 GB
- Need complex analytical queries
- Require database replication
- Heavy concurrent write operations

### When to Move to Larger Instance

Consider $10/month plan (2 GB RAM) if:
- More than 20 concurrent users
- Adding more features/services
- Need better performance
- Running multiple applications

## Monitoring & Alerts

### Set Up AWS Billing Alerts
1. Go to AWS Billing Console
2. Create billing alarm for **$6/month**
3. Receive email if costs exceed threshold

### Monitor Resource Usage
```bash
# Check memory usage
free -h

# Check disk space
df -h

# Check database size
ls -lh /home/ims/app/ims.db

# Check backup space
du -sh /home/ims/backups/
```

### Automatic Cleanup
- Logs rotated automatically (14-day retention)
- Backups cleaned automatically (30-day retention)
- Prevents disk space issues

## Comparison: Cost vs Features

### This Setup ($4.50/month with HTTPS)
✅ Full-featured inventory system
✅ HTTPS with valid SSL certificate
✅ Free domain (DuckDNS)
✅ Barcode scanning support
✅ 2FA authentication
✅ Bilingual (English/Bulgarian)
✅ Automated backups
✅ 99.9% uptime SLA
✅ 1 TB transfer
✅ Automated security updates
✅ Automatic SSL renewal

### Alternative Cloud Providers (Comparison)
- **DigitalOcean** ($4/month droplet): Similar specs, but no static IP included
- **Vultr** ($3.50/month): Similar, but no managed snapshots
- **Heroku** (Free tier): No longer available, paid starts at $7/month
- **AWS EC2** (t3.micro): ~$8-10/month with similar specs
- **Self-hosted VPS**: $3-5/month but requires more technical expertise

### On-Premises (Comparison)
- **Hardware cost**: $200-500 upfront
- **Electricity**: $5-10/month
- **Internet**: Business line required
- **Maintenance**: Your time
- **Reliability**: No SLA

**Verdict**: AWS Lightsail $3.50/month plan is the most cost-effective managed solution.

## Backup & Disaster Recovery

### Included Backups
- **Daily database backups**: Automated at 2 AM
- **Retention**: 30 days
- **Location**: `/home/ims/backups/`
- **Lightsail snapshots**: Weekly (configurable)

### Backup Restoration
Full disaster recovery possible with:
1. Lightsail snapshot restore (~5 minutes)
2. Database backup restore (~1 minute)
3. Total recovery time: ~10 minutes

### Total Backup Storage
- Database backups: ~1 GB (30 days * ~30 MB)
- Lightsail snapshots: ~1 GB ($1/month)

## Security Best Practices

### Essential (Already Configured)
- ✅ UFW firewall enabled
- ✅ Fail2Ban active
- ✅ SSH key-only authentication
- ✅ Root login disabled
- ✅ Security headers configured
- ✅ Rate limiting active

### Recommended (Manual Setup)
1. **Restrict SSH to Your IP:**
   ```bash
   sudo ufw delete allow 22
   sudo ufw allow from YOUR_IP to any port 22
   ```

2. **Restrict HTTP Access (Optional):**
   ```bash
   # Only allow your office/home IP
   sudo ufw delete allow 80
   sudo ufw allow from YOUR_IP to any port 80
   ```

3. **Setup VPN Access:**
   - Use Tailscale (free for personal use)
   - Access server through encrypted VPN tunnel
   - Keep firewall restrictive

### Advanced (For Sensitive Data)
- Use a free domain and enable HTTPS
- Setup VPN for all access
- Enable additional audit logging
- Regular security scans

## Maintenance Requirements

### Weekly (~5 minutes)
- Check error logs
- Verify backups completed
- Review disk space

### Monthly (~15 minutes)
- Apply security updates: `sudo apt update && sudo apt upgrade -y`
- Test backup restoration
- Review access logs

### Quarterly (~30 minutes)
- Review security configuration
- Check for application updates
- Optimize database (SQLite vacuum)

## FAQ

**Q: Is 512 MB RAM enough?**
A: Yes, for 5-10 concurrent users with moderate usage. Monitor with `free -h`.

**Q: Can I upgrade later?**
A: Yes, AWS Lightsail allows easy plan upgrades (no downgrade though).

**Q: Is DuckDNS reliable?**
A: Yes, DuckDNS has been free and stable since 2013. Used by thousands of users worldwide.

**Q: What if I run out of storage?**
A: Upgrade to $5/month plan (40 GB) or clean up old backups/logs manually.

**Q: Can I use my own domain later?**
A: Yes, easily. Point your domain's DNS to your Lightsail IP and run Certbot again with your domain.

**Q: How do I know if I'm hitting resource limits?**
A: Monitor with `htop`, `free -h`, `df -h`. If consistently >80% RAM/disk, upgrade.

**Q: Is SQLite production-ready?**
A: Yes, for small to medium projects. Used by many production systems. Not for very high concurrent writes.

---

## Quick Start Deployment

1. **Create Lightsail Instance** ($3.50/month plan)
2. **Register DuckDNS domain** (free, 2 minutes)
3. **Run setup script**: `sudo bash deploy/setup.sh`
4. **Deploy application**: Upload code and install dependencies
5. **Configure Nginx**: Copy `deploy/nginx.conf` (update domain)
6. **Get SSL certificate**: `sudo certbot --nginx -d yourdomain.duckdns.org`
7. **Start application**: Configure Supervisor
8. **Access**: `https://yourdomain.duckdns.org`

**Total setup time**: 2-4 hours
**Monthly cost**: $4.50 (with HTTPS!)
**Maintenance**: ~1 hour/month

---

**Document Version**: 1.0
**Last Updated**: 2026-01-04
**Deployment Type**: Cost-Optimized (HTTPS, SQLite)
