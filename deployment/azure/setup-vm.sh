#!/bin/bash

# =================================
# Azure VM Setup Script
# =================================
# Run this on the Azure VM after SSH'ing in
# =================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔═══════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║       Setting up Document Analysis Agent VM           ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════╝${NC}"
echo ""

# Update system
echo -e "${GREEN}► Updating system packages...${NC}"
sudo apt-get update
sudo apt-get upgrade -y

# Install Docker
echo -e "${GREEN}► Installing Docker...${NC}"
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
fi

# Install Docker Compose
echo -e "${GREEN}► Installing Docker Compose...${NC}"
if ! command -v docker-compose &> /dev/null; then
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# Install Git
echo -e "${GREEN}► Installing Git...${NC}"
sudo apt-get install -y git

# Create app directory
echo -e "${GREEN}► Creating application directory...${NC}"
sudo mkdir -p /opt/doc-agent
sudo chown $USER:$USER /opt/doc-agent

# Get public IP
PUBLIC_IP=$(curl -s ifconfig.me)
echo -e "${GREEN}► Detected public IP: ${PUBLIC_IP}${NC}"

echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              Setup Complete!                          ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Clone your repository:"
echo "   cd /opt/doc-agent"
echo "   git clone <your-repo-url> ."
echo ""
echo "2. Copy the environment file:"
echo "   cp deployment/.env.example deployment/.env"
echo ""
echo "3. Edit the environment file with your settings:"
echo "   nano deployment/.env"
echo ""
echo "4. Update ALLOWED_ORIGINS and ALLOWED_HOSTS:"
echo "   ALLOWED_ORIGINS=http://${PUBLIC_IP}:3000"
echo "   ALLOWED_HOSTS=${PUBLIC_IP},localhost"
echo ""
echo "5. Start the application:"
echo "   cd deployment"
echo "   ./deploy.sh up"
echo ""
echo -e "${YELLOW}NOTE: You may need to log out and back in for Docker permissions${NC}"
