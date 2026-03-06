#!/bin/bash

# =================================
# Azure VM Deployment Script
# =================================
# Deploys Document Analysis Agent to Azure VM
# =================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔═══════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     Document Analysis Agent - Azure Deployment        ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════╝${NC}"
echo ""

# Configuration (set these or use environment variables)
RESOURCE_GROUP="${AZURE_RESOURCE_GROUP:-doc-agent-rg}"
LOCATION="${AZURE_LOCATION:-eastus}"
VM_NAME="${AZURE_VM_NAME:-doc-agent-vm}"
VM_SIZE="${AZURE_VM_SIZE:-Standard_B2s}"
ADMIN_USER="${AZURE_ADMIN_USER:-azureuser}"
DNS_NAME="${AZURE_DNS_NAME:-doc-agent}"

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo -e "${RED}✗ Azure CLI not installed. Please install: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli${NC}"
    exit 1
fi

# Check if logged in
if ! az account show &> /dev/null; then
    echo -e "${YELLOW}Please log in to Azure...${NC}"
    az login
fi

echo -e "${GREEN}► Creating resource group: ${RESOURCE_GROUP}${NC}"
az group create --name "$RESOURCE_GROUP" --location "$LOCATION" --output none

echo -e "${GREEN}► Creating VM: ${VM_NAME}${NC}"
az vm create \
    --resource-group "$RESOURCE_GROUP" \
    --name "$VM_NAME" \
    --image Ubuntu2204 \
    --size "$VM_SIZE" \
    --admin-username "$ADMIN_USER" \
    --generate-ssh-keys \
    --public-ip-sku Standard \
    --output none

# Get public IP
PUBLIC_IP=$(az vm show -d -g "$RESOURCE_GROUP" -n "$VM_NAME" --query publicIps -o tsv)

echo -e "${GREEN}► Opening ports 80, 443, 8000, 3000${NC}"
az vm open-port --resource-group "$RESOURCE_GROUP" --name "$VM_NAME" --port 80 --priority 100 --output none
az vm open-port --resource-group "$RESOURCE_GROUP" --name "$VM_NAME" --port 443 --priority 101 --output none
az vm open-port --resource-group "$RESOURCE_GROUP" --name "$VM_NAME" --port 8000 --priority 102 --output none
az vm open-port --resource-group "$RESOURCE_GROUP" --name "$VM_NAME" --port 3000 --priority 103 --output none

echo -e "${GREEN}► Setting up DNS name: ${DNS_NAME}${NC}"
az network public-ip update \
    --resource-group "$RESOURCE_GROUP" \
    --name "${VM_NAME}PublicIP" \
    --dns-name "$DNS_NAME" \
    --output none 2>/dev/null || true

FQDN=$(az network public-ip show --resource-group "$RESOURCE_GROUP" --name "${VM_NAME}PublicIP" --query dnsSettings.fqdn -o tsv 2>/dev/null || echo "")

echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              VM Created Successfully!                 ║${NC}"
echo -e "${GREEN}╠═══════════════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║${NC} Public IP: ${PUBLIC_IP}"
if [ -n "$FQDN" ]; then
echo -e "${GREEN}║${NC} FQDN: ${FQDN}"
fi
echo -e "${GREEN}║${NC} SSH: ssh ${ADMIN_USER}@${PUBLIC_IP}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. SSH into the VM: ssh ${ADMIN_USER}@${PUBLIC_IP}"
echo "2. Run the setup script: ./setup-vm.sh"
echo ""

# Save connection info
cat > connection-info.txt << EOF
Azure VM Connection Info
========================
Resource Group: ${RESOURCE_GROUP}
VM Name: ${VM_NAME}
Public IP: ${PUBLIC_IP}
FQDN: ${FQDN:-N/A}
SSH Command: ssh ${ADMIN_USER}@${PUBLIC_IP}

Frontend URL: http://${PUBLIC_IP}:3000
API URL: http://${PUBLIC_IP}:8000
API Docs: http://${PUBLIC_IP}:8000/docs
EOF

echo -e "${GREEN}Connection info saved to connection-info.txt${NC}"

