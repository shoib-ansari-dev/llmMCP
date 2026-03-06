# Azure Deployment Guide

Deploy the Document Analysis Agent to Azure VM.

## Prerequisites

1. [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli) installed
2. Azure subscription
3. SSH key pair (will be generated if not exists)

## Quick Deploy

### Step 1: Create Azure VM

```bash
cd deployment/azure
./create-vm.sh
```

This will:
- Create a resource group
- Create an Ubuntu 22.04 VM
- Open ports 80, 443, 8000, 3000
- Save connection info to `connection-info.txt`

### Step 2: Setup VM

SSH into the VM and run setup:

```bash
ssh azureuser@<VM_IP>
```

On the VM:
```bash
# Download setup script
curl -O https://raw.githubusercontent.com/YOUR_REPO/main/deployment/azure/setup-vm.sh
chmod +x setup-vm.sh
./setup-vm.sh
```

### Step 3: Deploy Application

There are 3 ways to provide the `.env` file:

#### Option A: Create .env locally first (Recommended)

```bash
# Copy example and edit with your API key
cp deployment/.env.example deployment/.env
nano deployment/.env  # Add your OPENAI_API_KEY

# Deploy (will auto-detect deployment/.env)
./deployment/azure/deploy-to-vm.sh <VM_IP>
```

#### Option B: Interactive creation

```bash
# Will prompt for API key and create .env
./deployment/azure/deploy-to-vm.sh <VM_IP> --create-env
```

#### Option C: Specify .env file path

```bash
./deployment/azure/deploy-to-vm.sh <VM_IP> --env-file /path/to/your/.env
```

**The script automatically updates `ALLOWED_ORIGINS` and `ALLOWED_HOSTS` with the VM IP.**

## Access URLs

After deployment:
- **Frontend:** http://<VM_IP>:3000
- **API:** http://<VM_IP>:8000
- **API Docs:** http://<VM_IP>:8000/docs

## Security Configuration

The application enforces same-site origin policy:

| Variable | Description |
|----------|-------------|
| `SAME_SITE_ENFORCE` | Enable/disable same-site checking (default: true) |
| `ALLOWED_ORIGINS` | Comma-separated list of allowed frontend origins |
| `ALLOWED_HOSTS` | Comma-separated list of allowed Host headers |

**Only requests from `ALLOWED_ORIGINS` are accepted by the API.**

## Cleanup

To delete all Azure resources:

```bash
az group delete --name doc-agent-rg --yes
```

## Files

| File | Description |
|------|-------------|
| `create-vm.sh` | Creates Azure VM |
| `setup-vm.sh` | Installs Docker on VM |
| `deploy-to-vm.sh` | Deploys code to VM |

## Environment Variables

### Backend (.env)
```bash
OPENAI_API_KEY=your_key
SAME_SITE_ENFORCE=true
ALLOWED_ORIGINS=http://YOUR_IP:3000
ALLOWED_HOSTS=YOUR_IP,YOUR_IP:8000
```

### Frontend (build arg)
```bash
VITE_API_URL=http://YOUR_IP:8000
```

