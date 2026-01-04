#!/bin/bash
#
# PostgreSQL Database Setup Script for IMS (NOT NEEDED FOR SQLITE)
#
# ⚠️  THIS SCRIPT IS NOT REQUIRED FOR THE DEFAULT SQLITE DEPLOYMENT
#
# This script is kept for reference only. The IMS application now uses SQLite by default,
# which requires no database server installation or configuration.
#
# If you prefer to use PostgreSQL instead of SQLite, you can:
# 1. Run this script to set up PostgreSQL
# 2. Update your .env file to use the PostgreSQL DATABASE_URL
# 3. Install psycopg2-binary: pip install psycopg2-binary
#
# Usage: sudo bash setup-database.sh
#

set -e

echo "⚠️  WARNING: This script sets up PostgreSQL, but IMS uses SQLite by default."
echo "If you want to use SQLite (recommended), you don't need to run this script."
echo ""
read -p "Do you want to continue with PostgreSQL setup? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled. Use SQLite (no setup needed)."
    exit 0
fi

echo "========================================="
echo "IMS - PostgreSQL Database Setup"
echo "========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root or with sudo"
    exit 1
fi

# Generate strong password
DB_PASSWORD=$(openssl rand -base64 32)

echo "Creating PostgreSQL database and user..."
echo ""

# Create database and user
sudo -u postgres psql << EOF
-- Create database
CREATE DATABASE ims_production;

-- Create user
CREATE USER ims_user WITH ENCRYPTED PASSWORD '$DB_PASSWORD';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE ims_production TO ims_user;

-- Additional permissions for PostgreSQL 15+
\c ims_production
GRANT ALL ON SCHEMA public TO ims_user;
EOF

echo ""
echo "========================================="
echo "Database Setup Complete!"
echo "========================================="
echo ""
echo "Database Name: ims_production"
echo "Database User: ims_user"
echo "Database Password: $DB_PASSWORD"
echo ""
echo "⚠️  IMPORTANT: Save this password securely!"
echo "Add it to your .env file:"
echo ""
echo "DATABASE_URL=postgresql://ims_user:$DB_PASSWORD@localhost/ims_production"
echo ""

# Configure PostgreSQL authentication
echo "Configuring PostgreSQL authentication..."
PG_VERSION=$(ls /etc/postgresql/ | head -1)
PG_HBA="/etc/postgresql/$PG_VERSION/main/pg_hba.conf"

# Backup original
cp "$PG_HBA" "$PG_HBA.backup"

# Update authentication
cat > "$PG_HBA" << 'EOF'
# PostgreSQL Client Authentication Configuration

# TYPE  DATABASE        USER            ADDRESS                 METHOD

# "local" is for Unix domain socket connections only
local   all             postgres                                peer
local   all             all                                     md5

# IPv4 local connections:
host    all             all             127.0.0.1/32            md5

# IPv6 local connections:
host    all             all             ::1/128                 md5

# Reject all other connections
host    all             all             0.0.0.0/0               reject
EOF

# Restart PostgreSQL
systemctl restart postgresql

echo "PostgreSQL authentication configured"
echo ""
echo "Testing database connection..."
sudo -u postgres psql -d ims_production -c "SELECT version();" > /dev/null 2>&1 && echo "✓ Database connection successful" || echo "✗ Database connection failed"
echo ""
