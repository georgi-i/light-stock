#!/bin/bash
#
# SQLite Database Backup Script for IMS
# This script should be run as the 'ims' user via cron
#
# Usage: ./backup-database.sh
# Cron: 0 2 * * * /home/ims/scripts/backup-database.sh
#

# Configuration
BACKUP_DIR="/home/ims/backups/database"
DATE=$(date +%Y%m%d_%H%M%S)
DB_FILE="/home/ims/app/ims.db"
RETENTION_DAYS=30
LOG_FILE="/home/ims/logs/backup.log"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"
mkdir -p "$(dirname $LOG_FILE)"

# Check if database file exists
if [ ! -f "$DB_FILE" ]; then
    echo "[$(date)] ERROR: Database file not found at $DB_FILE" >> "$LOG_FILE"
    exit 1
fi

# Start backup
echo "[$(date)] Starting SQLite database backup..." >> "$LOG_FILE"

# Perform backup using SQLite's .backup command (safe for live databases)
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

# Optional: Send notification (uncomment if you have mail configured)
# echo "SQLite database backup completed successfully" | mail -s "IMS Backup Success" admin@yourdomain.com

exit 0
