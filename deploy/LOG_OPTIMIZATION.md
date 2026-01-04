# Log Storage Optimization for Cost-Optimized Deployment

## Overview
This document explains the aggressive log rotation strategy implemented for the $3.50/month AWS Lightsail instance with 20 GB storage.

---

## Storage Constraints

### Available Storage
- **Total**: 20 GB SSD
- **System & packages**: ~5 GB
- **Application code**: <100 MB
- **Database**: ~100 MB (5,000 products)
- **Backups**: ~1-2 GB (30 days)
- **Available**: ~13 GB

### Log Storage Target
To maintain available space, logs should consume **less than 500 MB** total.

---

## Log Rotation Configuration

### 1. Fail2ban Logs (Most Aggressive)

**Configuration** (automatically set by setup.sh):
```
Location: /var/log/fail2ban.log
Rotation: Daily
Retention: 3 days
Compression: Yes (gzip)
Max size: ~3-5 MB uncompressed, ~500 KB compressed
```

**Rationale:**
- Fail2ban logs are primarily for debugging
- Once SSH is properly secured, minimal activity
- 3-day retention sufficient for identifying attack patterns
- Most aggressive rotation to save space

**Storage Impact:**
- Before: ~50-100 MB/month (without rotation)
- After: ~2-5 MB/month (3-day retention)
- **Savings: ~45-95 MB/month**

### 2. Application Logs (Moderate)

**Configuration**:
```
Location: /home/ims/app/logs/*.log
Rotation: Daily
Retention: 14 days
Compression: Yes (gzip)
Max size: ~50-100 MB
```

**Rationale:**
- 14 days sufficient for debugging application issues
- Compressed logs save ~80% space
- Application activity moderate (small user base)

**Storage Impact:**
- ~50-100 MB with 14-day retention
- Acceptable for troubleshooting

### 3. Nginx Logs (Moderate)

**Configuration**:
```
Location: /var/log/nginx/ims_*.log
Rotation: Daily
Retention: 14 days
Compression: Yes (gzip)
Max size: ~100-200 MB
```

**Rationale:**
- Access logs useful for monitoring traffic patterns
- Error logs critical for debugging
- 14 days provides good visibility

**Storage Impact:**
- ~100-200 MB with 14-day retention
- Most of log storage budget

### 4. System Logs (Default)

**Configuration**:
```
Location: /var/log/syslog, /var/log/auth.log, etc.
Rotation: Weekly
Retention: 4 weeks
Compression: Yes
Max size: ~50-100 MB
```

**Rationale:**
- Ubuntu default configuration
- Reasonable balance for system monitoring

---

## Automatic Configuration

The `setup.sh` script automatically configures:

1. **Fail2ban log rotation** (aggressive):
   - Creates `/etc/logrotate.d/fail2ban`
   - Daily rotation, 3-day retention
   - Automatic log flushing after rotation

2. **Reduced fail2ban verbosity**:
   - Changes log level from INFO to NOTICE
   - Reduces log volume by ~40-60%

3. **Application log rotation**:
   - Configured manually in DEPLOYMENT.md
   - 14-day retention for debugging

---

## Storage Monitoring

### Check Log Disk Usage

```bash
# Total log directory size
sudo du -sh /var/log/

# Individual log sizes
sudo du -h /var/log/ | sort -h | tail -20

# Fail2ban log size
sudo ls -lh /var/log/fail2ban.log*

# Application log size
sudo du -sh /home/ims/app/logs/

# Nginx log size
sudo du -sh /var/log/nginx/
```

### Expected Log Storage Usage

| Log Type | Retention | Storage |
|----------|-----------|---------|
| Fail2ban | 3 days | ~5 MB |
| Application | 14 days | ~100 MB |
| Nginx | 14 days | ~200 MB |
| System | 4 weeks | ~100 MB |
| **Total** | - | **~405 MB** |

---

## Manual Log Cleanup (If Needed)

### Emergency Cleanup

If you're running low on disk space:

```bash
# 1. Remove old compressed logs (force)
sudo find /var/log -name "*.gz" -mtime +7 -delete
sudo find /home/ims/app/logs -name "*.gz" -mtime +7 -delete

# 2. Truncate large log files (keeps file, removes content)
sudo truncate -s 0 /var/log/fail2ban.log
sudo truncate -s 0 /var/log/nginx/ims_access.log
sudo truncate -s 0 /var/log/nginx/ims_error.log

# 3. Force log rotation
sudo logrotate -f /etc/logrotate.conf

# 4. Restart services to release file handles
sudo systemctl restart fail2ban nginx
sudo supervisorctl restart ims
```

### Reduce Retention (If Consistently Low on Space)

```bash
# Reduce fail2ban to 1 day
sudo nano /etc/logrotate.d/fail2ban
# Change: rotate 3 → rotate 1

# Reduce nginx to 7 days
sudo nano /etc/logrotate.d/ims
# Change: rotate 14 → rotate 7

# Apply changes
sudo logrotate -f /etc/logrotate.conf
```

---

## Log Verbosity Settings

### Fail2ban

**Current**: NOTICE level
- Logs bans and unbans
- Minimal operational logs
- No debug information

**To increase (if debugging)**:
```bash
sudo nano /etc/fail2ban/fail2ban.conf
# Change: loglevel = NOTICE → loglevel = INFO
sudo systemctl restart fail2ban
```

### Nginx

**Current**: Standard combined format
- One line per request
- Includes: IP, timestamp, request, status, size, referrer, user-agent

**To reduce (if needed)**:
```bash
sudo nano /etc/nginx/sites-available/ims
# Comment out access_log for static files (already done)
# Or use minimal format instead of combined
```

### Application (Flask)

**Current**: INFO level (production)
- Application errors logged
- Request logging via Gunicorn

**To reduce**:
```bash
# In .env file
FLASK_LOG_LEVEL=WARNING  # Only log warnings and errors
```

---

## Backup Log Monitoring

### Backup Logs

**Location**: `/home/ims/logs/backup.log`

**Configuration**:
```bash
# Add to application log rotation
sudo nano /etc/logrotate.d/ims

# Add:
/home/ims/logs/backup.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    create 0640 ims ims
}
```

**Expected Size**: ~1-2 MB/month

---

## Best Practices

### DO:
✅ Monitor disk usage weekly: `df -h`
✅ Review log sizes monthly: `sudo du -sh /var/log/`
✅ Keep log rotation aggressive (3-14 days max)
✅ Compress all rotated logs
✅ Test log rotation: `sudo logrotate -d /etc/logrotate.conf`

### DON'T:
❌ Disable log rotation (disk will fill up)
❌ Increase retention beyond 30 days
❌ Keep uncompressed logs
❌ Log at DEBUG level in production
❌ Store large debug dumps

---

## Troubleshooting

### Problem: Disk space running low

**Check disk usage:**
```bash
df -h
# If /dev/root > 80%, investigate
```

**Find large files:**
```bash
sudo du -ah / | sort -h | tail -20
```

**Check log sizes:**
```bash
sudo du -sh /var/log/*
sudo du -sh /home/ims/app/logs/
```

**Solution:**
1. Force log rotation: `sudo logrotate -f /etc/logrotate.conf`
2. Clean old backups: `find /home/ims/backups -mtime +30 -delete`
3. Remove old compressed logs: `find /var/log -name "*.gz" -mtime +7 -delete`

### Problem: Fail2ban log growing too fast

**Check log size:**
```bash
sudo ls -lh /var/log/fail2ban.log*
```

**If > 10 MB:**
1. Check for attacks: `sudo fail2ban-client status sshd`
2. Verify IP whitelist: `sudo fail2ban-client get sshd whitelisted`
3. Consider reducing retention to 1 day

### Problem: Application logs growing

**Check Gunicorn logs:**
```bash
sudo ls -lh /home/ims/app/logs/
```

**Solutions:**
1. Reduce Flask log level to WARNING
2. Reduce retention to 7 days
3. Investigate what's being logged excessively

---

## Performance Impact

### Log Rotation Performance

- **Daily rotation**: ~1-2 seconds CPU time
- **Compression**: Minimal impact (runs in background)
- **Disk I/O**: Negligible for small logs

### Storage Performance

- **20 GB SSD**: Fast enough for application + logs
- **Log writes**: Async, buffered by OS
- **Compression**: Saves disk space, slightly slower reads

---

## Upgrade Path

### If Logs Become Issue

Consider upgrading to:

**$5/month plan (40 GB SSD)**
- Double storage capacity
- Can increase log retention to 30 days
- More headroom for growth

**Or external logging**:
- Free: Papertrail (100 MB/month free)
- Free: Loggly (200 MB/day free)
- AWS CloudWatch Logs (pay-as-you-go)

---

## Summary

### Storage Savings

| Before Optimization | After Optimization |
|---------------------|-------------------|
| Fail2ban: ~100 MB/month | Fail2ban: ~5 MB/month |
| No rotation | All logs rotated |
| Uncompressed | Compressed |
| ~1-2 GB logs | ~400 MB logs |

**Total Savings: ~600-1600 MB**

### Key Configurations

1. ✅ Fail2ban: 3-day retention (aggressive)
2. ✅ Application: 14-day retention (moderate)
3. ✅ Nginx: 14-day retention (moderate)
4. ✅ All logs compressed
5. ✅ Reduced log verbosity

### Maintenance

- **Weekly**: Check disk space (`df -h`)
- **Monthly**: Review log sizes (`du -sh /var/log/`)
- **As needed**: Force rotation or cleanup

---

**Document Version**: 1.0
**Last Updated**: 2026-01-04
**Deployment Type**: Cost-Optimized (20 GB storage)
