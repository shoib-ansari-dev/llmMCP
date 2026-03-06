#!/bin/bash

# =================================
# Deploy Application to Azure VM
# =================================
# Deploys the latest code to the Azure VM
# =================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
AZURE_VM_IP="${1:-}"
AZURE_USER="${AZURE_ADMIN_USER:-azureuser}"
APP_DIR="/opt/doc-agent"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

show_usage() {
    echo "Usage: $0 <azure-vm-ip> [options]"
    echo ""
    echo "Options:"
    echo "  --env-file <path>   Path to .env file to upload"
    echo "  --create-env        Interactive prompt to create .env"
    echo ""
    echo "Examples:"
    echo "  $0 20.120.45.123 --env-file ./deployment/.env"
    echo "  $0 20.120.45.123 --create-env"
    echo ""
    echo "You can also create deployment/.env locally first:"
    echo "  cp deployment/.env.example deployment/.env"
    echo "  # Edit deployment/.env with your API key"
    echo "  $0 20.120.45.123"
}

if [ -z "$AZURE_VM_IP" ]; then
    show_usage
    exit 1
fi

# Parse options
ENV_FILE=""
CREATE_ENV=false
shift || true
while [[ $# -gt 0 ]]; do
    case $1 in
        --env-file)
            ENV_FILE="$2"
            shift 2
            ;;
        --create-env)
            CREATE_ENV=true
            shift
            ;;
        --help|-h)
            show_usage
            exit 0
            ;;
        *)
            shift
            ;;
    esac
done

# Find .env file
if [ -z "$ENV_FILE" ]; then
    if [ -f "$PROJECT_ROOT/deployment/.env" ]; then
        ENV_FILE="$PROJECT_ROOT/deployment/.env"
    fi
fi

echo -e "${BLUE}╔═══════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         Deploying to Azure VM: ${AZURE_VM_IP}            ${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════╝${NC}"
echo ""

# Handle .env file
if [ -z "$ENV_FILE" ] || [ ! -f "$ENV_FILE" ]; then
    echo -e "${YELLOW}⚠ No .env file found${NC}"

    if [ "$CREATE_ENV" = true ]; then
        echo -e "${GREEN}► Creating .env file interactively...${NC}"
        echo ""

        # Prompt for required values
        read -p "Enter your OPENAI_API_KEY (xAI/Grok key): " OPENAI_KEY
        if [ -z "$OPENAI_KEY" ]; then
            echo -e "${RED}✗ API key is required${NC}"
            exit 1
        fi

        read -p "Rate limit per minute [60]: " RATE_LIMIT
        RATE_LIMIT=${RATE_LIMIT:-60}

        # Create .env file
        ENV_FILE="$PROJECT_ROOT/deployment/.env"
        cat > "$ENV_FILE" << EOF
# =================================
# Document Analysis Agent - Azure Deployment
# Generated on $(date)
# =================================

# API Key
OPENAI_API_KEY=${OPENAI_KEY}

# ChromaDB
CHROMA_PERSIST_DIRECTORY=/app/data/chroma

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=${RATE_LIMIT}

# Same-Site Security
SAME_SITE_ENFORCE=true
ALLOWED_ORIGINS=http://${AZURE_VM_IP}:3000
ALLOWED_HOSTS=${AZURE_VM_IP},${AZURE_VM_IP}:8000,localhost

# Frontend API URL
VITE_API_URL=http://${AZURE_VM_IP}:8000

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=text
DEBUG=false
EOF
        echo -e "${GREEN}✓ Created .env file at: $ENV_FILE${NC}"
    else
        echo ""
        echo "Please provide .env file using one of these methods:"
        echo ""
        echo "1. Create locally and deploy:"
        echo "   ${YELLOW}cp deployment/.env.example deployment/.env${NC}"
        echo "   ${YELLOW}# Edit deployment/.env with your API key${NC}"
        echo "   ${YELLOW}$0 $AZURE_VM_IP${NC}"
        echo ""
        echo "2. Specify existing .env file:"
        echo "   ${YELLOW}$0 $AZURE_VM_IP --env-file /path/to/.env${NC}"
        echo ""
        echo "3. Create interactively:"
        echo "   ${YELLOW}$0 $AZURE_VM_IP --create-env${NC}"
        echo ""
        exit 1
    fi
fi

echo -e "${GREEN}► Using .env file: ${ENV_FILE}${NC}"

# Validate .env has API key
if grep -q "your_api_key_here" "$ENV_FILE" 2>/dev/null; then
    echo -e "${RED}✗ .env file contains placeholder 'your_api_key_here'${NC}"
    echo -e "${RED}  Please set your actual API key${NC}"
    exit 1
fi

if ! grep -q "OPENAI_API_KEY=" "$ENV_FILE" 2>/dev/null; then
    echo -e "${RED}✗ .env file is missing OPENAI_API_KEY${NC}"
    exit 1
fi

# Create temp .env with updated IP
echo -e "${GREEN}► Configuring .env for Azure VM IP: ${AZURE_VM_IP}${NC}"
TEMP_ENV="/tmp/doc-agent-env-$$"
cp "$ENV_FILE" "$TEMP_ENV"

# Update origins/hosts for this VM IP
sed -i.bak "s|ALLOWED_ORIGINS=.*|ALLOWED_ORIGINS=http://${AZURE_VM_IP}:3000|" "$TEMP_ENV" 2>/dev/null || \
    sed -i '' "s|ALLOWED_ORIGINS=.*|ALLOWED_ORIGINS=http://${AZURE_VM_IP}:3000|" "$TEMP_ENV"

sed -i.bak "s|ALLOWED_HOSTS=.*|ALLOWED_HOSTS=${AZURE_VM_IP},${AZURE_VM_IP}:8000,localhost|" "$TEMP_ENV" 2>/dev/null || \
    sed -i '' "s|ALLOWED_HOSTS=.*|ALLOWED_HOSTS=${AZURE_VM_IP},${AZURE_VM_IP}:8000,localhost|" "$TEMP_ENV"

sed -i.bak "s|VITE_API_URL=.*|VITE_API_URL=http://${AZURE_VM_IP}:8000|" "$TEMP_ENV" 2>/dev/null || \
    sed -i '' "s|VITE_API_URL=.*|VITE_API_URL=http://${AZURE_VM_IP}:8000|" "$TEMP_ENV"

rm -f "${TEMP_ENV}.bak"

echo ""
echo "Configuration:"
grep -E "^(ALLOWED_ORIGINS|ALLOWED_HOSTS|VITE_API_URL)=" "$TEMP_ENV" | while read line; do
    echo "  $line"
done
echo ""

# Sync files
echo -e "${GREEN}► Syncing project files to Azure VM...${NC}"
rsync -avz --progress \
    --exclude '.venv' \
    --exclude 'node_modules' \
    --exclude '__pycache__' \
    --exclude '.git' \
    --exclude 'data' \
    --exclude '*.pyc' \
    --exclude '.env' \
    --exclude 'deployment/.env' \
    "$PROJECT_ROOT/" "${AZURE_USER}@${AZURE_VM_IP}:${APP_DIR}/"

# Upload .env securely
echo -e "${GREEN}► Uploading .env file...${NC}"
scp "$TEMP_ENV" "${AZURE_USER}@${AZURE_VM_IP}:${APP_DIR}/deployment/.env"
rm -f "$TEMP_ENV"

# Deploy on VM
echo -e "${GREEN}► Starting services on VM...${NC}"
ssh "${AZURE_USER}@${AZURE_VM_IP}" << 'ENDSSH'
cd /opt/doc-agent/deployment

echo "Stopping existing services..."
docker-compose down 2>/dev/null || true

echo "Building images..."
docker-compose build

echo "Starting services..."
docker-compose up -d

sleep 5
echo ""
echo "Service Status:"
docker-compose ps
ENDSSH

echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              Deployment Complete!                     ║${NC}"
echo -e "${GREEN}╠═══════════════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║${NC} Frontend: http://${AZURE_VM_IP}:3000"
echo -e "${GREEN}║${NC} API:      http://${AZURE_VM_IP}:8000"
echo -e "${GREEN}║${NC} API Docs: http://${AZURE_VM_IP}:8000/docs"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}Same-site security enabled: Only frontend can access API${NC}"
