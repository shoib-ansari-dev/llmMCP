#!/bin/bash

# =================================
# Docker Deployment Script with Auto-Scaling
# =================================
# Scales API pods based on CPU usage (80% threshold)
# =================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
CPU_THRESHOLD=80
MIN_REPLICAS=1
MAX_REPLICAS=5
CHECK_INTERVAL=30

echo -e "${BLUE}╔═══════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║      Document Analysis Agent - Docker Deployment      ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════╝${NC}"
echo ""

# Check for .env file
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo -e "${YELLOW}Creating .env from .env.example...${NC}"
        cp .env.example .env
        echo -e "${RED}⚠ Please edit deployment/.env and add your OPENAI_API_KEY${NC}"
        exit 1
    else
        echo -e "${RED}✗ No .env file found. Please create one with OPENAI_API_KEY${NC}"
        exit 1
    fi
fi

# Check if OPENAI_API_KEY is set
if grep -q "your_api_key_here" .env; then
    echo -e "${RED}✗ Please set your OPENAI_API_KEY in deployment/.env${NC}"
    exit 1
fi

# Function to get current CPU usage of API containers
get_cpu_usage() {
    docker stats --no-stream --format "{{.CPUPerc}}" $(docker-compose ps -q api 2>/dev/null) 2>/dev/null | \
        sed 's/%//g' | \
        awk '{ sum += $1; count++ } END { if (count > 0) print sum/count; else print 0 }' || echo "0"
}

# Function to get current replica count
get_replica_count() {
    docker-compose ps -q api 2>/dev/null | wc -l | tr -d ' '
}

# Function to scale API pods
scale_api() {
    local count=$1
    echo -e "${GREEN}► Scaling API to ${count} replica(s)...${NC}"
    docker-compose up -d --scale api=${count} --no-recreate
    echo -e "${GREEN}✓ Scaled to ${count} replica(s)${NC}"
}

# Auto-scaling function
autoscale() {
    echo -e "${BLUE}Starting auto-scaler...${NC}"
    echo -e "  CPU Threshold: ${CPU_THRESHOLD}%"
    echo -e "  Min Replicas: ${MIN_REPLICAS}"
    echo -e "  Max Replicas: ${MAX_REPLICAS}"
    echo -e "  Check Interval: ${CHECK_INTERVAL}s"
    echo ""
    echo -e "${YELLOW}Press Ctrl+C to stop auto-scaling${NC}"
    echo ""

    while true; do
        CURRENT_REPLICAS=$(get_replica_count)
        CPU_USAGE=$(get_cpu_usage)
        CPU_INT=${CPU_USAGE%.*}

        echo -e "[$(date '+%H:%M:%S')] Replicas: ${CURRENT_REPLICAS}, CPU: ${CPU_USAGE}%"

        # Scale up if CPU > threshold and below max
        if [ "${CPU_INT:-0}" -gt "$CPU_THRESHOLD" ] && [ "$CURRENT_REPLICAS" -lt "$MAX_REPLICAS" ]; then
            NEW_REPLICAS=$((CURRENT_REPLICAS + 1))
            echo -e "${YELLOW}⚡ High CPU detected! Scaling up to ${NEW_REPLICAS}...${NC}"
            scale_api $NEW_REPLICAS
        fi

        # Scale down if CPU < threshold/2 and above min
        SCALE_DOWN_THRESHOLD=$((CPU_THRESHOLD / 2))
        if [ "${CPU_INT:-0}" -lt "$SCALE_DOWN_THRESHOLD" ] && [ "$CURRENT_REPLICAS" -gt "$MIN_REPLICAS" ]; then
            NEW_REPLICAS=$((CURRENT_REPLICAS - 1))
            echo -e "${YELLOW}📉 Low CPU detected. Scaling down to ${NEW_REPLICAS}...${NC}"
            scale_api $NEW_REPLICAS
        fi

        sleep $CHECK_INTERVAL
    done
}

# Parse command
COMMAND=${1:-up}

case $COMMAND in
    build)
        echo -e "${GREEN}► Building Docker images...${NC}"
        docker-compose build --no-cache
        ;;

    up)
        echo -e "${GREEN}► Starting services (1 API replica + auto-scaling)...${NC}"
        docker-compose up -d --build
        echo ""
        echo -e "${GREEN}✓ Services started!${NC}"
        echo ""
        echo -e "  ${BLUE}API (Load Balanced):${NC}  http://localhost:8000"
        echo -e "  ${BLUE}API Docs:${NC}             http://localhost:8000/docs"
        echo -e "  ${BLUE}Frontend:${NC}             http://localhost:3000"
        echo ""

        # Start auto-scaling in background
        echo -e "${GREEN}► Starting auto-scaler in background...${NC}"
        nohup bash -c '
            CPU_THRESHOLD=80
            MIN_REPLICAS=1
            MAX_REPLICAS=5
            CHECK_INTERVAL=30

            while true; do
                CURRENT_REPLICAS=$(docker-compose ps -q api 2>/dev/null | wc -l | tr -d " ")
                CPU_USAGE=$(docker stats --no-stream --format "{{.CPUPerc}}" $(docker-compose ps -q api 2>/dev/null) 2>/dev/null | sed "s/%//g" | awk "{ sum += \$1; count++ } END { if (count > 0) print sum/count; else print 0 }" || echo "0")
                CPU_INT=${CPU_USAGE%.*}

                # Scale up if CPU > threshold and below max
                if [ "${CPU_INT:-0}" -gt "$CPU_THRESHOLD" ] && [ "$CURRENT_REPLICAS" -lt "$MAX_REPLICAS" ]; then
                    NEW_REPLICAS=$((CURRENT_REPLICAS + 1))
                    docker-compose up -d --scale api=${NEW_REPLICAS} --no-recreate
                fi

                # Scale down if CPU < threshold/2 and above min
                SCALE_DOWN_THRESHOLD=$((CPU_THRESHOLD / 2))
                if [ "${CPU_INT:-0}" -lt "$SCALE_DOWN_THRESHOLD" ] && [ "$CURRENT_REPLICAS" -gt "$MIN_REPLICAS" ]; then
                    NEW_REPLICAS=$((CURRENT_REPLICAS - 1))
                    docker-compose up -d --scale api=${NEW_REPLICAS} --no-recreate
                fi

                sleep $CHECK_INTERVAL
            done
        ' > /tmp/doc-agent-autoscale.log 2>&1 &
        echo $! > /tmp/doc-agent-autoscale.pid
        echo -e "${GREEN}✓ Auto-scaler running (PID: $(cat /tmp/doc-agent-autoscale.pid))${NC}"
        echo ""
        echo -e "${YELLOW}Auto-scaling: CPU > 80% → scale up, CPU < 40% → scale down${NC}"
        ;;

    down)
        echo -e "${YELLOW}► Stopping all services...${NC}"

        # Stop auto-scaler if running
        if [ -f /tmp/doc-agent-autoscale.pid ]; then
            PID=$(cat /tmp/doc-agent-autoscale.pid)
            if kill -0 $PID 2>/dev/null; then
                kill $PID 2>/dev/null
                echo -e "${GREEN}✓ Auto-scaler stopped${NC}"
            fi
            rm -f /tmp/doc-agent-autoscale.pid
        fi

        docker-compose down
        echo -e "${GREEN}✓ All services stopped${NC}"
        ;;

    logs)
        docker-compose logs -f ${2:-}
        ;;

    status)
        echo -e "${BLUE}Service Status:${NC}"
        docker-compose ps
        echo ""
        echo -e "${BLUE}Current Replicas:${NC} $(get_replica_count)"
        echo -e "${BLUE}CPU Usage:${NC} $(get_cpu_usage)%"

        # Check auto-scaler status
        if [ -f /tmp/doc-agent-autoscale.pid ]; then
            PID=$(cat /tmp/doc-agent-autoscale.pid)
            if kill -0 $PID 2>/dev/null; then
                echo -e "${BLUE}Auto-scaler:${NC} ${GREEN}Running (PID: $PID)${NC}"
            else
                echo -e "${BLUE}Auto-scaler:${NC} ${RED}Stopped${NC}"
            fi
        else
            echo -e "${BLUE}Auto-scaler:${NC} ${YELLOW}Not started${NC}"
        fi
        ;;

    restart)
        echo -e "${YELLOW}► Restarting services...${NC}"
        docker-compose restart
        echo -e "${GREEN}✓ Services restarted${NC}"
        ;;

    scale)
        # Manual scale (e.g., ./deploy.sh scale 3)
        NUM=${2:-1}
        if [ "$NUM" -lt "$MIN_REPLICAS" ] || [ "$NUM" -gt "$MAX_REPLICAS" ]; then
            echo -e "${RED}✗ Replica count must be between ${MIN_REPLICAS} and ${MAX_REPLICAS}${NC}"
            exit 1
        fi
        scale_api $NUM
        ;;

    autoscale)
        # Run auto-scaling loop
        autoscale
        ;;

    clean)
        echo -e "${RED}► Removing all containers, images, and volumes...${NC}"
        docker-compose down -v --rmi all
        echo -e "${GREEN}✓ Cleaned up${NC}"
        ;;

    *)
        echo "Usage: $0 {build|up|down|logs|status|restart|scale|autoscale|clean}"
        echo ""
        echo "Commands:"
        echo "  build     - Build Docker images"
        echo "  up        - Start all services (1 API replica)"
        echo "  down      - Stop all services"
        echo "  logs      - View logs (optional: service name)"
        echo "  status    - Show service status and CPU usage"
        echo "  restart   - Restart all services"
        echo "  scale N   - Manually scale to N API replicas (1-5)"
        echo "  autoscale - Enable auto-scaling based on CPU (80% threshold)"
        echo "  clean     - Remove all containers, images, volumes"
        exit 1
        ;;
esac

