# Docker Deployment

This directory contains all deployment-related files for the Document Analysis Agent.

## Architecture

```
                    ┌─────────────────┐
                    │    Frontend     │
                    │   (React/Nginx) │
                    │    Port: 3000   │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  Load Balancer  │
                    │     (Nginx)     │
                    │    Port: 8000   │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
        ┌─────▼─────┐  ┌─────▼─────┐  ┌─────▼─────┐
        │  API (1)  │  │  API (2)  │  │  API (n)  │
        │ (default) │  │ (scaled)  │  │ (scaled)  │
        └─────┬─────┘  └─────┬─────┘  └─────┬─────┘
              └──────────────┼──────────────┘
                             │
                    ┌────────▼────────┐
                    │    ChromaDB     │
                    │  (Shared Vol)   │
                    └─────────────────┘
```

## Auto-Scaling

- **Default:** 1 API pod
- **Scale up:** When CPU > 80%
- **Scale down:** When CPU < 40%
- **Max replicas:** 5

## Files

| File | Description |
|------|-------------|
| `docker-compose.yml` | Main compose file (1 API pod default) |
| `Dockerfile.api` | API container image |
| `Dockerfile.frontend` | Frontend container image |
| `nginx/loadbalancer-dynamic.conf` | Dynamic load balancer config |
| `nginx/frontend.conf` | Frontend nginx configuration |
| `deploy.sh` | Deployment & auto-scaling script |
| `.env.example` | Environment variables template |

## Quick Start

```bash
# 1. Copy environment file and add your API key
cp .env.example .env
# Edit .env and set OPENAI_API_KEY

# 2. Deploy (starts with 1 API pod + auto-scaling enabled)
./deploy.sh up

# 3. Access
# - Frontend: http://localhost:3000
# - API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
```

## Commands

```bash
# Start all services (1 API replica + auto-scaling)
./deploy.sh up

# Manually scale to N replicas
./deploy.sh scale 3

# Check status, CPU usage, and auto-scaler
./deploy.sh status

# View logs
./deploy.sh logs
./deploy.sh logs api

# Stop all services (including auto-scaler)
./deploy.sh down

# Clean up everything
./deploy.sh clean
```

## Auto-Scaling Configuration

Edit `deploy.sh` to adjust:

```bash
CPU_THRESHOLD=80      # Scale up when CPU > 80%
MIN_REPLICAS=1        # Minimum API pods
MAX_REPLICAS=5        # Maximum API pods
CHECK_INTERVAL=30     # Check every 30 seconds
```

## Volumes

- `chroma-data`: Shared volume for ChromaDB persistence across pods

## Health Checks

All services have health checks:
- **API pods**: `GET /` every 30s
- **Load balancer**: `GET /health` every 30s
- **Frontend**: `GET /health` every 30s

