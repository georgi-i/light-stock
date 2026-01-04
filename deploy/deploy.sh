#!/bin/bash
#
# IMS - Deployment Script
# Deploys the application to AWS Lightsail instance
#
# Usage: ./deploy.sh [server_ip] [pem_file]
#        ./deploy.sh user@server_ip /path/to/key.pem
#        ./deploy.sh 1.2.3.4 ~/.ssh/lightsail-key.pem
#

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}IMS - Deployment Script${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""

# Check if server address provided
if [ -z "$1" ]; then
    echo -e "${RED}Error: Server address required${NC}"
    echo "Usage: ./deploy.sh [server_ip] [pem_file]"
    echo "   or: ./deploy.sh user@server_ip /path/to/key.pem"
    echo ""
    echo "Examples:"
    echo "  ./deploy.sh 1.2.3.4 ~/.ssh/lightsail-key.pem"
    echo "  ./deploy.sh ubuntu@1.2.3.4 ~/Downloads/LightsailKey.pem"
    exit 1
fi

SERVER=$1
PEM_FILE=$2

# If only IP provided, add default user
if [[ ! "$SERVER" =~ "@" ]]; then
    SERVER="ubuntu@$SERVER"  # Changed to ubuntu (AWS Lightsail default)
fi

# Check if PEM file provided and exists
SSH_OPTS=""
if [ -n "$PEM_FILE" ]; then
    if [ ! -f "$PEM_FILE" ]; then
        echo -e "${RED}Error: PEM file not found: $PEM_FILE${NC}"
        exit 1
    fi
    # Check PEM file permissions
    PEM_PERMS=$(stat -f "%Lp" "$PEM_FILE" 2>/dev/null || stat -c "%a" "$PEM_FILE" 2>/dev/null)
    if [ "$PEM_PERMS" != "400" ] && [ "$PEM_PERMS" != "600" ]; then
        echo -e "${YELLOW}Warning: PEM file has incorrect permissions (${PEM_PERMS})${NC}"
        echo -e "${YELLOW}Attempting to fix permissions...${NC}"
        chmod 400 "$PEM_FILE"
        echo -e "${GREEN}✓ Fixed PEM file permissions to 400${NC}"
    fi
    SSH_OPTS="-i $PEM_FILE"
    echo -e "${YELLOW}Using PEM file: ${PEM_FILE}${NC}"
fi

echo -e "${YELLOW}Target server: ${SERVER}${NC}"
echo ""

# Test SSH connection
echo -e "${YELLOW}[1/6] Testing SSH connection...${NC}"
if ! ssh $SSH_OPTS -o ConnectTimeout=5 -o BatchMode=yes "$SERVER" "echo 'Connection successful'" > /dev/null 2>&1; then
    echo -e "${RED}Error: Cannot connect to server${NC}"
    echo "Please ensure:"
    echo "  - Server IP is correct"
    echo "  - SSH key/PEM file is correct"
    echo "  - Server is running"
    echo "  - Security group allows SSH (port 22)"
    exit 1
fi
echo -e "${GREEN}✓ SSH connection successful${NC}"
echo ""

# Create temporary deployment directory
echo -e "${YELLOW}[2/6] Creating deployment package...${NC}"
ARCHIVE_NAME="ims-deploy-$(date +%Y%m%d-%H%M%S).tar.gz"

# Get the script's directory and project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Change to project root to ensure paths are correct
cd "$PROJECT_ROOT"

# Create archive excluding unwanted files
tar -czf "$ARCHIVE_NAME" \
    --exclude='venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='*.pyo' \
    --exclude='.env' \
    --exclude='*.db' \
    --exclude='*.sqlite' \
    --exclude='*.sqlite3' \
    --exclude='.DS_Store' \
    --exclude='.git' \
    --exclude='*.log' \
    --exclude='.vscode' \
    --exclude='.idea' \
    --exclude='instance' \
    --exclude='.pytest_cache' \
    --exclude='htmlcov' \
    --exclude='.coverage' \
    --exclude='ims-deploy-*.tar.gz' \
    .

if [ ! -f "$ARCHIVE_NAME" ] || [ ! -s "$ARCHIVE_NAME" ]; then
    echo -e "${RED}Error: Failed to create deployment archive${NC}"
    exit 1
fi

ARCHIVE_SIZE=$(du -h "$ARCHIVE_NAME" | cut -f1)
echo -e "${GREEN}✓ Deployment package created: $ARCHIVE_NAME ($ARCHIVE_SIZE)${NC}"
echo -e "${GREEN}✓ Archive saved in: $PROJECT_ROOT${NC}"
echo ""

# Upload archive to server
echo -e "${YELLOW}[3/6] Uploading files to server...${NC}"
scp $SSH_OPTS "$ARCHIVE_NAME" "$SERVER:/tmp/"
echo -e "${GREEN}✓ Files uploaded${NC}"
echo ""

# Extract on server and run post-deployment
echo -e "${YELLOW}[4/6] Extracting files on server...${NC}"
ssh $SSH_OPTS "$SERVER" << 'ENDSSH'
    set -e

    # Colors for SSH session
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    NC='\033[0m'

    # Find the uploaded archive
    ARCHIVE=$(ls -t /tmp/ims-deploy-*.tar.gz 2>/dev/null | head -1)

    if [ -z "$ARCHIVE" ]; then
        echo "Error: Deployment archive not found"
        exit 1
    fi

    # Extract to application directory
    sudo mkdir -p /home/ims/app
    cd /home/ims/app

    # Backup current .env if exists
    if [ -f .env ]; then
        sudo cp .env .env.backup
        echo "✓ Backed up existing .env file"
    fi

    # Extract archive (need sudo to write to /home/ims/app)
    sudo tar -xzf "$ARCHIVE"

    # Fix ownership immediately after extraction
    sudo chown -R ims:www-data /home/ims/app

    # Restore .env if it was backed up
    if [ -f .env.backup ]; then
        sudo mv .env.backup .env
        sudo chown ims:www-data .env
        echo "✓ Restored .env file"
    fi

    # Make scripts executable
    sudo chmod +x /home/ims/app/deploy/*.sh 2>/dev/null || true

    # Clean up
    rm "$ARCHIVE"

    echo -e "${GREEN}✓ Files extracted to /home/ims/app${NC}"
ENDSSH
echo -e "${GREEN}✓ Extraction complete${NC}"
echo ""

# Run post-deployment setup
echo -e "${YELLOW}[5/6] Running post-deployment setup...${NC}"
ssh $SSH_OPTS "$SERVER" << 'ENDSSH'
    set -e
    cd /home/ims/app

    # Run post-deployment setup (using bash to avoid chmod issues)
    bash deploy/post-deploy.sh
ENDSSH
echo -e "${GREEN}✓ Post-deployment setup complete${NC}"
echo ""

# Note: Archive kept locally for reference
echo -e "${YELLOW}[6/6] Finalizing...${NC}"
echo -e "${GREEN}✓ Deployment archive preserved locally: $ARCHIVE_NAME${NC}"
echo ""

# Display success message
echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}Deployment Successful!${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "1. Configure your .env file on the server:"
if [ -n "$SSH_OPTS" ]; then
    echo "   ssh $SSH_OPTS $SERVER"
else
    echo "   ssh $SERVER"
fi
echo "   nano /home/ims/app/.env"
echo ""
echo "2. If this is first deployment, configure Nginx and SSL"
echo ""
echo "3. Check application status:"
if [ -n "$SSH_OPTS" ]; then
    echo "   ssh $SSH_OPTS $SERVER 'sudo systemctl status ims'"
else
    echo "   ssh $SERVER 'sudo systemctl status ims'"
fi
echo ""
echo "4. View logs:"
if [ -n "$SSH_OPTS" ]; then
    echo "   ssh $SSH_OPTS $SERVER 'tail -f /home/ims/logs/ims.log'"
else
    echo "   ssh $SERVER 'tail -f /home/ims/logs/ims.log'"
fi
echo ""
