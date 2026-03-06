#!/bin/bash

# ===========================================
# Document Analysis Agent - Full Stack Runner
# Runs: API + Frontend + MCP Server
# ===========================================

set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}╔═══════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║     Document Analysis Agent - Full Stack Launcher     ║${NC}"
echo -e "${CYAN}╚═══════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠ Warning: .env file not found${NC}"
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${YELLOW}  Created .env from .env.example${NC}"
        echo -e "${YELLOW}  Please add your OPENAI_API_KEY to .env${NC}"
    fi
    echo ""
fi

# Check virtual environment
if [ ! -d ".venv" ]; then
    echo -e "${RED}✗ Virtual environment not found${NC}"
    echo -e "  Run: python3.11 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
echo -e "${GREEN}✓ Activating Python virtual environment${NC}"
source .venv/bin/activate

# Load environment variables
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs 2>/dev/null) || true
fi

# Set development environment (SQLite by default)
export ENVIRONMENT=${ENVIRONMENT:-development}
export AUTH_DEV_MODE=${AUTH_DEV_MODE:-true}

echo -e "${GREEN}✓ Environment: $ENVIRONMENT${NC}"
if [ "$ENVIRONMENT" = "development" ]; then
    echo -e "${GREEN}✓ Database: SQLite (./data/app.db)${NC}"
else
    echo -e "${GREEN}✓ Database: PostgreSQL${NC}"
fi

# Check for node_modules
if [ ! -d "frontend/node_modules" ]; then
    echo -e "${YELLOW}Installing frontend dependencies...${NC}"
    cd frontend && npm install && cd ..
fi

# Create data directory for ChromaDB and SQLite
mkdir -p data/chroma

# PIDs for cleanup
PIDS=()

# Function to cleanup on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}Shutting down all services...${NC}"
    for pid in "${PIDS[@]}"; do
        kill "$pid" 2>/dev/null || true
    done
    # Kill any remaining background jobs
    jobs -p | xargs -r kill 2>/dev/null || true
    echo -e "${GREEN}✓ All services stopped${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM EXIT

# Start FastAPI server
echo -e "${GREEN}► Starting FastAPI server...${NC}"
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000 2>&1 | sed 's/^/  [API] /' &
PIDS+=($!)
sleep 2

# Start React frontend
echo -e "${GREEN}► Starting React frontend...${NC}"
cd frontend
npm run dev 2>&1 | sed 's/^/  [React] /' &
PIDS+=($!)
cd ..
sleep 2

# Start MCP server (in background, logs to file)
echo -e "${GREEN}► Starting MCP server...${NC}"
python mcp_server.py > /dev/null 2>&1 &
PIDS+=($!)

echo ""
echo -e "${CYAN}╔═══════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║              All Services Running!                    ║${NC}"
echo -e "${CYAN}╠═══════════════════════════════════════════════════════╣${NC}"
echo -e "${CYAN}║${NC}                                                       ${CYAN}║${NC}"
echo -e "${CYAN}║${NC}  ${GREEN}🚀 API Server:${NC}      http://localhost:8000           ${CYAN}║${NC}"
echo -e "${CYAN}║${NC}  ${GREEN}📚 API Docs:${NC}        http://localhost:8000/docs      ${CYAN}║${NC}"
echo -e "${CYAN}║${NC}  ${GREEN}🌐 React Frontend:${NC}  http://localhost:5173           ${CYAN}║${NC}"
echo -e "${CYAN}║${NC}  ${GREEN}🔧 MCP Server:${NC}      Running (stdio transport)       ${CYAN}║${NC}"
echo -e "${CYAN}║${NC}                                                       ${CYAN}║${NC}"
echo -e "${CYAN}╠═══════════════════════════════════════════════════════╣${NC}"
echo -e "${CYAN}║${NC}  ${YELLOW}Press Ctrl+C to stop all services${NC}                   ${CYAN}║${NC}"
echo -e "${CYAN}╚═══════════════════════════════════════════════════════╝${NC}"
echo ""

# Wait for all background processes
wait

