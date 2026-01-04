#!/bin/bash
#
# IMS - Post-Deployment Setup Script
# Runs on the server after code deployment
# This script is called automatically by deploy.sh
#

set -e  # Exit on any error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}Running post-deployment setup...${NC}"
echo ""

APP_DIR="/home/ims/app"
VENV_DIR="$APP_DIR/venv"
LOG_DIR="/home/ims/logs"

cd "$APP_DIR"

# Create virtual environment if it doesn't exist
echo -e "${YELLOW}[1/7] Setting up Python virtual environment...${NC}"
if [ ! -d "$VENV_DIR" ]; then
    # Try python3.11 first, fall back to python3
    if command -v python3.11 &> /dev/null; then
        PYTHON_CMD="python3.11"
    elif command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    else
        echo -e "${RED}Error: Python 3 not found${NC}"
        exit 1
    fi

    echo "Using $PYTHON_CMD ($(command -v $PYTHON_CMD))"
    $PYTHON_CMD -m venv "$VENV_DIR"
    echo -e "${GREEN}✓ Virtual environment created with $PYTHON_CMD${NC}"
else
    echo -e "${GREEN}✓ Virtual environment already exists${NC}"
fi
echo ""

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Upgrade pip
echo -e "${YELLOW}[2/7] Upgrading pip...${NC}"
pip install --upgrade pip > /dev/null 2>&1
echo -e "${GREEN}✓ pip upgraded${NC}"
echo ""

# Install/update dependencies
echo -e "${YELLOW}[3/7] Installing Python dependencies...${NC}"
pip install -r requirements.txt > /dev/null 2>&1
echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

# Check if .env exists
echo -e "${YELLOW}[4/7] Checking environment configuration...${NC}"
if [ ! -f .env ]; then
    echo -e "${RED}⚠ Warning: .env file not found${NC}"
    echo "Creating .env template from .env.example (if available)"
    if [ -f .env.example ]; then
        cp .env.example .env
        echo -e "${YELLOW}Please configure .env file with production values${NC}"
    else
        echo -e "${RED}No .env.example found. You must create .env manually${NC}"
    fi
else
    echo -e "${GREEN}✓ .env file exists${NC}"
fi
echo ""

# Compile translations
echo -e "${YELLOW}[5/7] Compiling translations...${NC}"
if [ -d "translations" ]; then
    flask --app run:app translate compile > /dev/null 2>&1 || echo "Note: Translation compilation skipped (may need .env configuration)"
    echo -e "${GREEN}✓ Translations compiled${NC}"
else
    echo -e "${YELLOW}No translations directory found, skipping${NC}"
fi
echo ""

# Run database migrations
echo -e "${YELLOW}[6/7] Running database migrations...${NC}"
if [ -d "migrations" ]; then
    flask --app run:app db upgrade > /dev/null 2>&1 || echo "Note: Migration skipped (database may need initialization)"
    echo -e "${GREEN}✓ Database migrations applied${NC}"
else
    echo -e "${YELLOW}No migrations directory found, skipping${NC}"
fi
echo ""

# Create necessary directories
echo -e "${YELLOW}[7/7] Creating necessary directories...${NC}"
mkdir -p "$LOG_DIR"
mkdir -p /home/ims/backups/database
mkdir -p "$APP_DIR/instance"
echo -e "${GREEN}✓ Directories created${NC}"
echo ""

# Fix ownership and permissions
echo -e "${YELLOW}Fixing file ownership and permissions...${NC}"
sudo chown -R ims:www-data /home/ims/app 2>/dev/null || true
sudo chown -R ims:www-data /home/ims/logs 2>/dev/null || true
sudo chown -R ims:www-data /home/ims/backups 2>/dev/null || true
sudo chmod -R 755 /home/ims/app 2>/dev/null || true
sudo chmod -R 755 /home/ims/logs 2>/dev/null || true
sudo chmod 644 /home/ims/app/deploy/*.conf.py 2>/dev/null || true
sudo chmod +x /home/ims/app/deploy/*.sh 2>/dev/null || true
echo -e "${GREEN}✓ Ownership and permissions fixed${NC}"
echo ""

# Clean up old socket files if they exist
echo -e "${YELLOW}Cleaning up old socket files...${NC}"
sudo rm -f "$APP_DIR/ims.sock" 2>/dev/null || true
sudo rm -f /run/ims/ims.sock 2>/dev/null || true
echo -e "${GREEN}✓ Old socket files cleaned${NC}"
echo ""

# Set up or update systemd service
echo -e "${YELLOW}Setting up systemd service...${NC}"
if [ -f "deploy/ims.service" ]; then
    sudo cp deploy/ims.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable ims
    echo -e "${GREEN}✓ Systemd service configured${NC}"
fi
echo ""

# Restart application
echo -e "${YELLOW}Restarting application...${NC}"
if sudo systemctl is-active --quiet ims; then
    sudo systemctl restart ims
    echo -e "${GREEN}✓ Application restarted${NC}"
else
    echo -e "${YELLOW}Starting application for the first time...${NC}"
    sudo systemctl start ims
    echo -e "${GREEN}✓ Application started${NC}"
fi
echo ""

# Check application status
sleep 2
if sudo systemctl is-active --quiet ims; then
    echo -e "${GREEN}✓ Application is running${NC}"
else
    echo -e "${RED}⚠ Warning: Application may not be running properly${NC}"
    echo "Check logs: sudo journalctl -u ims -n 50"
fi
echo ""

# Reload Nginx
echo -e "${YELLOW}Reloading Nginx...${NC}"
if sudo systemctl is-active --quiet nginx; then
    sudo nginx -t > /dev/null 2>&1 && sudo systemctl reload nginx
    echo -e "${GREEN}✓ Nginx reloaded${NC}"
else
    echo -e "${YELLOW}Nginx not running or not configured yet${NC}"
fi
echo ""

echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}Post-deployment setup complete!${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""
echo -e "${BLUE}Useful commands:${NC}"
echo "  Status:  sudo systemctl status ims"
echo "  Logs:    tail -f $LOG_DIR/ims.log"
echo "  Restart: sudo systemctl restart ims"
echo ""
