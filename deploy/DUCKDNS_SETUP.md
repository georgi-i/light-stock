# DuckDNS Setup Guide for IMS

## Overview
This guide walks you through setting up a free DuckDNS subdomain with Let's Encrypt SSL certificate for your IMS deployment on AWS Lightsail.

**Total Cost: $0** (DuckDNS and Let's Encrypt are free forever!)

---

## Prerequisites

Before you begin, ensure you have:
- ✅ AWS Lightsail instance running
- ✅ Static IP attached to your instance
- ✅ SSH access to your server
- ✅ Nginx installed (done by setup.sh script)
- ✅ Certbot installed (done by setup.sh script)

---

## Step 1: Register DuckDNS Domain

### 1.1 Sign Up for DuckDNS

1. **Go to**: https://www.duckdns.org
2. **Sign in** with one of these providers (no email required):
   - GitHub
   - Google
   - Reddit
   - Twitter
   - Persona

3. **You're done!** No verification emails or payment info needed.

### 1.2 Create Your Subdomain

1. **Choose a subdomain**: Enter your desired name (e.g., `myims`, `inventory`, `yourcompany`)
   - Available characters: letters, numbers, hyphens
   - Must be unique across all DuckDNS users
   - Example: `myims` → `myims.duckdns.org`

2. **Add your Lightsail Static IP**:
   - In the "current ip" field, enter your Lightsail static IP
   - Example: `54.123.45.67`

3. **Click "add domain"**

4. **Save your token**: Copy the token from the top of the page
   - You'll need this if you want to update your IP automatically
   - Keep it secret!

### 1.3 Verify DNS Resolution

Wait 1-2 minutes for DNS propagation, then test:

```bash
# Test DNS resolution (from your local machine or server)
nslookup myims.duckdns.org

# Or use dig
dig myims.duckdns.org

# You should see your Lightsail static IP in the response
```

---

## Step 2: Configure Nginx for DuckDNS

### 2.1 Update Nginx Configuration

SSH into your Lightsail instance:

```bash
ssh -i LightsailDefaultKey.pem ubuntu@YOUR_STATIC_IP
```

Edit the Nginx configuration:

```bash
sudo nano /etc/nginx/sites-available/ims
```

**Replace all instances of `yourcompany.duckdns.org` with your actual DuckDNS subdomain** (e.g., `myims.duckdns.org`).

Use nano's search and replace:
- Press `Ctrl+\`
- Search for: `yourcompany.duckdns.org`
- Replace with: `myims.duckdns.org` (your actual subdomain)
- Press `A` to replace all
- Press `Ctrl+X`, then `Y`, then `Enter` to save

### 2.2 Test Nginx Configuration

```bash
# Test for syntax errors
sudo nginx -t

# Should see: "syntax is ok" and "test is successful"
```

### 2.3 Enable Site and Restart Nginx

```bash
# Enable the site
sudo ln -s /etc/nginx/sites-available/ims /etc/nginx/sites-enabled/

# Remove default site
sudo rm /etc/nginx/sites-enabled/default

# Test again
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx

# Check status
sudo systemctl status nginx
```

---

## Step 3: Obtain SSL Certificate (Let's Encrypt)

### 3.1 Run Certbot

Now obtain a free SSL certificate from Let's Encrypt:

```bash
# Run Certbot with your DuckDNS domain
sudo certbot --nginx -d myims.duckdns.org
```

**Follow the prompts:**

1. **Enter email address**: For urgent renewal and security notices
   ```
   Enter email address: your-email@example.com
   ```

2. **Agree to Terms of Service**: Type `A` and press Enter
   ```
   (A)gree/(C)ancel: A
   ```

3. **Share email with EFF** (optional): Type `Y` or `N`
   ```
   (Y)es/(N)o: N
   ```

4. **Certbot will automatically:**
   - Verify domain ownership (via HTTP challenge)
   - Download SSL certificates
   - Update Nginx configuration
   - Configure HTTP→HTTPS redirect
   - Set up automatic renewal

### 3.2 Verify SSL Certificate

```bash
# Check certificate details
sudo certbot certificates

# You should see:
# Certificate Name: myims.duckdns.org
# Domains: myims.duckdns.org
# Expiry Date: [90 days from now]
# Certificate Path: /etc/letsencrypt/live/myims.duckdns.org/fullchain.pem
# Private Key Path: /etc/letsencrypt/live/myims.duckdns.org/privkey.pem
```

### 3.3 Test Auto-Renewal

SSL certificates expire every 90 days but renew automatically. Test the renewal process:

```bash
# Dry run (test without actually renewing)
sudo certbot renew --dry-run

# Should see: "Congratulations, all simulated renewals succeeded"
```

### 3.4 Verify Auto-Renewal Timer

```bash
# Check that the renewal timer is active
sudo systemctl status certbot.timer

# Should show: "active (waiting)"
```

The timer runs twice daily to check for certificate expiration and renews automatically when needed.

---

## Step 4: Update Application Configuration

### 4.1 Update .env File

```bash
# Switch to application user
sudo su - ims

# Edit .env file
nano /home/ims/app/.env
```

Update the session cookie setting:

```bash
# Change this:
SESSION_COOKIE_SECURE=False

# To this:
SESSION_COOKIE_SECURE=True
```

Save and exit (`Ctrl+X`, `Y`, `Enter`).

### 4.2 Restart Application

```bash
# Exit from ims user
exit

# Restart application with supervisor
sudo supervisorctl restart ims

# Check status
sudo supervisorctl status ims
```

---

## Step 5: Test Your Secure Application

### 5.1 Access via HTTPS

Open your browser and navigate to:

```
https://myims.duckdns.org
```

**You should see:**
- ✅ Green padlock icon in browser address bar
- ✅ Valid SSL certificate
- ✅ "Connection is secure" message
- ✅ HTTP automatically redirects to HTTPS

### 5.2 Verify SSL Certificate

In your browser:
1. Click the padlock icon
2. Click "Certificate" or "Connection is secure"
3. Verify:
   - Issued to: `myims.duckdns.org`
   - Issued by: `Let's Encrypt`
   - Valid until: [90 days from now]

### 5.3 Test HTTP→HTTPS Redirect

```bash
# Test that HTTP redirects to HTTPS
curl -I http://myims.duckdns.org

# Should show:
# HTTP/1.1 301 Moved Permanently
# Location: https://myims.duckdns.org/
```

### 5.4 Test SSL Grade (Optional)

Check your SSL configuration quality:
1. Go to: https://www.ssllabs.com/ssltest/
2. Enter your domain: `myims.duckdns.org`
3. Click "Submit"
4. Wait for results (2-3 minutes)
5. Target grade: **A** or **A+**

---

## Step 6: Optional - DuckDNS Auto-Update Script

Since you're using a Lightsail **static IP**, your IP won't change, so this is **optional**. However, if you want to ensure DuckDNS always has the correct IP:

### 6.1 Create Update Script

```bash
# Create script directory
sudo mkdir -p /home/ims/scripts

# Create update script
sudo nano /home/ims/scripts/duckdns-update.sh
```

Add the following (replace with your values):

```bash
#!/bin/bash
# DuckDNS IP Update Script

DOMAIN="myims"  # Your subdomain (without .duckdns.org)
TOKEN="your-duckdns-token-here"  # Your DuckDNS token

echo url="https://www.duckdns.org/update?domains=$DOMAIN&token=$TOKEN&ip=" | curl -k -o /home/ims/logs/duck.log -K -
```

### 6.2 Make Executable

```bash
# Make executable
sudo chmod +x /home/ims/scripts/duckdns-update.sh
sudo chown ims:ims /home/ims/scripts/duckdns-update.sh

# Test it
sudo -u ims /home/ims/scripts/duckdns-update.sh

# Check log
cat /home/ims/logs/duck.log
# Should show: OK
```

### 6.3 Add to Crontab (Optional)

```bash
# Edit crontab
sudo crontab -e -u ims

# Add this line (updates every 5 minutes):
*/5 * * * * /home/ims/scripts/duckdns-update.sh >/dev/null 2>&1
```

---

## Troubleshooting

### Problem: DNS not resolving

**Symptoms:** `nslookup` doesn't return your IP

**Solution:**
1. Wait 5 minutes for DNS propagation
2. Check DuckDNS dashboard - ensure domain is active
3. Verify IP is correct in DuckDNS
4. Clear your local DNS cache:
   ```bash
   # Linux
   sudo systemd-resolve --flush-caches

   # macOS
   sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder

   # Windows
   ipconfig /flushdns
   ```

### Problem: Certbot validation fails

**Symptoms:** Certbot can't verify domain ownership

**Solution:**
1. Ensure Nginx is running: `sudo systemctl status nginx`
2. Ensure port 80 is open in Lightsail firewall
3. Ensure UFW allows port 80: `sudo ufw status`
4. Test domain resolves: `nslookup myims.duckdns.org`
5. Try again: `sudo certbot --nginx -d myims.duckdns.org`

### Problem: SSL certificate not showing as valid

**Symptoms:** Browser shows "Not Secure" or certificate error

**Solution:**
1. Check Nginx config: `sudo nginx -t`
2. Verify certificate exists: `sudo certbot certificates`
3. Check Nginx SSL config:
   ```bash
   sudo nano /etc/nginx/sites-available/ims
   # Look for ssl_certificate lines
   ```
4. Restart Nginx: `sudo systemctl restart nginx`
5. Clear browser cache and try again

### Problem: HTTP not redirecting to HTTPS

**Symptoms:** Can access via HTTP without redirect

**Solution:**
1. Check Nginx config for redirect:
   ```bash
   sudo nano /etc/nginx/sites-available/ims
   # Look for: return 301 https://$server_name$request_uri;
   ```
2. Test Nginx config: `sudo nginx -t`
3. Restart Nginx: `sudo systemctl restart nginx`

### Problem: Auto-renewal failing

**Symptoms:** Certificate expires or renewal test fails

**Solution:**
1. Test renewal: `sudo certbot renew --dry-run`
2. Check renewal timer: `sudo systemctl status certbot.timer`
3. Check Certbot logs: `sudo cat /var/log/letsencrypt/letsencrypt.log`
4. Ensure ports 80 and 443 are accessible
5. Manually renew: `sudo certbot renew --force-renewal`

---

## Maintenance

### Monthly Tasks

**Check SSL certificate expiry:**
```bash
sudo certbot certificates
```

**Test renewal:**
```bash
sudo certbot renew --dry-run
```

**Verify HTTPS is working:**
```bash
curl -I https://myims.duckdns.org
```

### When to Update DuckDNS IP

Only if your Lightsail static IP changes (rare):
1. Go to DuckDNS.org
2. Sign in
3. Update IP field
4. Click "update ip"

---

## Security Notes

✅ **What You've Achieved:**
- End-to-end encryption (HTTPS)
- Valid SSL certificate (not self-signed)
- Automatic HTTP→HTTPS redirect
- Auto-renewing certificates (90-day validity, renews at 60 days)
- HSTS enabled (forces HTTPS)
- A/A+ SSL grade

✅ **Best Practices:**
- Keep DuckDNS token secret
- Never commit token to git
- Monitor SSL certificate expiry
- Test auto-renewal quarterly

---

## Cost Summary

| Item | Cost |
|------|------|
| DuckDNS subdomain | $0.00 (free forever) |
| Let's Encrypt SSL | $0.00 (free forever) |
| Auto-renewal | $0.00 (automatic) |
| DNS hosting | $0.00 (included) |
| **Total** | **$0.00** |

No credit card required. No expiration. No hidden fees.

---

## FAQ

**Q: Can I use multiple subdomains?**
A: Yes! DuckDNS allows up to 5 subdomains per account for free.

**Q: Will my SSL certificate expire?**
A: Certificates are valid for 90 days and auto-renew at 60 days. No action needed.

**Q: Can I switch to a custom domain later?**
A: Yes! Just point your domain's DNS to your Lightsail IP and run Certbot again.

**Q: What happens if DuckDNS shuts down?**
A: DuckDNS has been free since 2013. If needed, you can switch to another free DNS service or buy a domain.

**Q: Is DuckDNS production-ready?**
A: Yes! Many small businesses and personal projects use DuckDNS in production.

**Q: Can I use this for commercial purposes?**
A: Yes! DuckDNS and Let's Encrypt are free for commercial use.

---

**Setup Complete!** 🎉

Your IMS application is now accessible at:
- ✅ `https://myims.duckdns.org`
- ✅ Secure HTTPS connection
- ✅ Valid SSL certificate
- ✅ $0 cost

**Next Steps:**
- Create your admin user
- Configure 2FA
- Add your inventory
- Start scanning!

---

**Document Version**: 1.0
**Last Updated**: 2026-01-04
**Setup Time**: ~15 minutes
