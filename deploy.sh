#!/bin/bash
# ═══════════════════════════════════════════════════════════
# LivItUpDeals Deployment Script
# Automatically syncs website files to hosting server
# ═══════════════════════════════════════════════════════════

set -e  # Exit on error

# ─── CONFIGURATION ─────────────────────────────────────────
# EDIT THESE VALUES FOR YOUR HOSTING:

FTP_HOST="ftp.yourhosting.com"
FTP_USER="your_ftp_username"
FTP_PASS="your_ftp_password"
REMOTE_DIR="/public_html"

# Alternatively, use SFTP (recommended if available):
# SFTP_HOST="yourhosting.com"
# SFTP_USER="your_ssh_username"
# SFTP_PORT="22"
# REMOTE_DIR="/home/username/public_html"

# ─── LOCAL PATHS ───────────────────────────────────────────
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
DATA_DIR="$PROJECT_DIR/data"
HTML_FILE="$PROJECT_DIR/index.html"

# ─── COLORS FOR OUTPUT ─────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ═══════════════════════════════════════════════════════════

echo -e "${GREEN}═══════════════════════════════════════════════${NC}"
echo -e "${GREEN}  LivItUpDeals - Deployment Script${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════${NC}\n"

# ─── VALIDATE FILES ────────────────────────────────────────
echo "📋 Validating files..."

if [ ! -f "$HTML_FILE" ]; then
    echo -e "${RED}❌ Error: index.html not found!${NC}"
    exit 1
fi

if [ ! -f "$DATA_DIR/products.json" ]; then
    echo -e "${YELLOW}⚠️  Warning: products.json not found${NC}"
    echo "   Run: python pipeline.py --update-website first"
    exit 1
fi

echo -e "${GREEN}✓${NC} index.html found"
echo -e "${GREEN}✓${NC} products.json found"

# ─── CHOOSE UPLOAD METHOD ──────────────────────────────────
echo -e "\n📤 Select upload method:"
echo "  1) FTP (most compatible)"
echo "  2) SFTP/SCP (more secure, requires SSH)"
echo "  3) Rsync over SSH (fastest, requires SSH)"
read -p "Enter choice [1-3]: " upload_method

case $upload_method in
    1)
        echo -e "\n${YELLOW}📡 Uploading via FTP...${NC}"
        
        # Check if lftp is installed
        if ! command -v lftp &> /dev/null; then
            echo -e "${RED}❌ lftp not installed. Install with:${NC}"
            echo "   brew install lftp  # macOS"
            echo "   sudo apt-get install lftp  # Linux"
            exit 1
        fi
        
        lftp -u "$FTP_USER","$FTP_PASS" "$FTP_HOST" <<EOF
set ssl:verify-certificate no
cd $REMOTE_DIR
put $HTML_FILE
mkdir -p data
cd data
put $DATA_DIR/products.json
bye
EOF
        ;;
        
    2)
        echo -e "\n${YELLOW}📡 Uploading via SFTP/SCP...${NC}"
        
        if [ -z "$SFTP_HOST" ]; then
            echo -e "${RED}❌ SFTP not configured. Edit deploy.sh first.${NC}"
            exit 1
        fi
        
        scp -P "$SFTP_PORT" "$HTML_FILE" "$SFTP_USER@$SFTP_HOST:$REMOTE_DIR/"
        scp -P "$SFTP_PORT" "$DATA_DIR/products.json" "$SFTP_USER@$SFTP_HOST:$REMOTE_DIR/data/"
        ;;
        
    3)
        echo -e "\n${YELLOW}📡 Uploading via Rsync...${NC}"
        
        if [ -z "$SFTP_HOST" ]; then
            echo -e "${RED}❌ Rsync not configured. Edit deploy.sh first.${NC}"
            exit 1
        fi
        
        rsync -avz -e "ssh -p $SFTP_PORT" \
            "$HTML_FILE" \
            "$DATA_DIR/products.json" \
            "$SFTP_USER@$SFTP_HOST:$REMOTE_DIR/"
        ;;
        
    *)
        echo -e "${RED}❌ Invalid choice${NC}"
        exit 1
        ;;
esac

# ─── SUCCESS ───────────────────────────────────────────────
echo -e "\n${GREEN}═══════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════${NC}"
echo -e "\n📊 Uploaded files:"
echo -e "   • index.html"
echo -e "   • data/products.json"
echo -e "\n🌐 Visit your site to verify!"
echo ""

exit 0
