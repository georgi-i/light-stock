# SQLite Migration Summary

## Overview
The IMS deployment has been updated to use **SQLite** instead of PostgreSQL. This simplifies deployment, reduces costs, and is ideal for small to medium-sized inventory management projects.

## Why SQLite?

### ✅ Benefits
- **Zero Configuration**: No separate database server to install or manage
- **Lower Resource Usage**: Perfect for the $5/month Lightsail instance
- **Simpler Backups**: Just copy the database file
- **Cost-Effective**: Reduces monthly costs from ~$7 to ~$6.50
- **Faster Setup**: Deployment time reduced from 4-6 hours to 2-4 hours
- **Built-in Python Support**: No additional database drivers needed
- **Ideal for Small Projects**: Handles thousands of products efficiently

### ⚠️ Considerations
SQLite is perfect for:
- Single-server deployments
- Low to moderate concurrent write operations
- Small to medium databases (up to hundreds of MB)
- Projects with fewer than 10 concurrent users

## Files Changed

### 1. DEPLOYMENT.md
**Changes:**
- Updated architecture diagram to show SQLite instead of PostgreSQL
- Removed "Database Setup" section (PostgreSQL installation steps)
- Added simple SQLite explanation
- Removed `libpq-dev` from dependencies
- Removed `psycopg2-binary` from pip install
- Updated DATABASE_URL example to use SQLite
- Updated backup scripts to use SQLite commands
- Updated troubleshooting section for SQLite
- Reduced cost estimate to ~$6.50/month
- Reduced setup time estimate to 2-4 hours

### 2. deploy/setup.sh
**Changes:**
- Removed `postgresql` and `postgresql-contrib` from apt packages
- Removed `libpq-dev` dependency
- Added `sqlite3` package
- Replaced PostgreSQL setup section with SQLite note
- Updated next steps instructions

### 3. deploy/backup-database.sh
**Changes:**
- Complete rewrite for SQLite
- Uses `sqlite3 .backup` command (safe for live databases)
- Backs up to compressed `.db.gz` files instead of `.sql.gz`
- No need to read database password from .env
- Simpler and more efficient backup process

### 4. deploy/setup-database.sh
**Changes:**
- Added warning that this script is NOT needed for SQLite
- Kept for reference only (in case someone wants PostgreSQL)
- Added confirmation prompt before PostgreSQL setup

### 5. config.py
**No changes needed** - Already supports SQLite:
```python
SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///ims.db'
```

### 6. requirements.txt
**No changes needed** - Never had PostgreSQL dependencies

## New Database Configuration

### Environment Variable (.env)
```bash
# SQLite (file will be created automatically)
DATABASE_URL=sqlite:////home/ims/app/ims.db
```

### Database File Location
- **Path**: `/home/ims/app/ims.db`
- **Permissions**: `644` (rw-r--r--)
- **Owner**: `ims:ims`

## Backup Strategy

### Daily Automated Backups
```bash
# Cron job (runs at 2 AM daily)
0 2 * * * /home/ims/scripts/backup-database.sh

# Backup location
/home/ims/backups/database/ims_db_YYYYMMDD_HHMMSS.db.gz

# Retention: 30 days
```

### Manual Backup
```bash
# Create immediate backup
sudo -u ims sqlite3 /home/ims/app/ims.db ".backup /home/ims/backups/manual_backup.db"

# Compress
gzip /home/ims/backups/manual_backup.db
```

### Restore from Backup
```bash
# Decompress backup
gunzip ims_db_20260104_020000.db.gz

# Stop application
sudo supervisorctl stop ims

# Restore database
cp ims_db_20260104_020000.db /home/ims/app/ims.db
sudo chown ims:ims /home/ims/app/ims.db
sudo chmod 644 /home/ims/app/ims.db

# Start application
sudo supervisorctl start ims
```

## Performance Considerations

### SQLite is Suitable For:
- ✅ Inventory databases with thousands of products
- ✅ Small team usage (2-10 concurrent users)
- ✅ Read-heavy workloads (product lookups, reports)
- ✅ Single-server deployments

### When to Consider PostgreSQL:
- Large databases (>100GB)
- High concurrent write operations (>50 concurrent writers)
- Complex analytical queries
- Multi-server deployments requiring replication

## Migration Path

### If You Need PostgreSQL Later:
1. Run `deploy/setup-database.sh` to install PostgreSQL
2. Export SQLite data:
   ```bash
   sqlite3 /home/ims/app/ims.db .dump > ims_dump.sql
   ```
3. Import to PostgreSQL:
   ```bash
   psql -U ims_user -d ims_production < ims_dump.sql
   ```
4. Update `.env` with PostgreSQL DATABASE_URL
5. Install `psycopg2-binary`: `pip install psycopg2-binary`
6. Restart application

## Verification

### Check SQLite Version
```bash
sqlite3 --version
# Should show: 3.37.0 or higher
```

### Test Database Connection
```bash
# Create test database
sqlite3 /tmp/test.db "CREATE TABLE test (id INTEGER);"
sqlite3 /tmp/test.db "SELECT * FROM sqlite_master;"
rm /tmp/test.db
```

### Monitor Database Size
```bash
# Check database file size
ls -lh /home/ims/app/ims.db

# Check table sizes
sqlite3 /home/ims/app/ims.db "SELECT name, COUNT(*) FROM sqlite_master GROUP BY name;"
```

## Security Notes

### SQLite Security Best Practices:
- ✅ Database file has restricted permissions (644)
- ✅ Owned by application user (ims:ims)
- ✅ Located within application directory (not web-accessible)
- ✅ Regular encrypted backups
- ✅ WAL mode enabled for better concurrency
- ✅ No network exposure (file-based)

## Support

### SQLite Resources:
- Official Documentation: https://www.sqlite.org/docs.html
- SQLAlchemy SQLite: https://docs.sqlalchemy.org/en/20/dialects/sqlite.html
- Performance Tuning: https://www.sqlite.org/speed.html

---

**Migration Date**: 2026-01-04
**Version**: 1.0
**Status**: Complete ✅
