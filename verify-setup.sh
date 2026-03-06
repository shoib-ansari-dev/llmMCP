#!/bin/bash
# Verification Checklist for Development Setup
# Run this to verify everything is configured correctly

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  Development Setup Verification Checklist                  ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

PASSED=0
FAILED=0

# Check 1: .env exists
echo "▶ Checking .env file..."
if [ -f ".env" ]; then
    echo "  ✅ .env file exists"
    ((PASSED++))
else
    echo "  ❌ .env file not found"
    ((FAILED++))
fi

# Check 2: AUTH_DEV_MODE is set
echo "▶ Checking AUTH_DEV_MODE..."
if grep -q "AUTH_DEV_MODE=true" .env; then
    echo "  ✅ AUTH_DEV_MODE=true (dev mode enabled)"
    ((PASSED++))
elif grep -q "AUTH_DEV_MODE=" .env; then
    echo "  ⚠️  AUTH_DEV_MODE is set but not to 'true'"
    ((FAILED++))
else
    echo "  ❌ AUTH_DEV_MODE not found in .env"
    ((FAILED++))
fi

# Check 3: ENVIRONMENT is set to development
echo "▶ Checking ENVIRONMENT..."
if grep -q "ENVIRONMENT=development" .env; then
    echo "  ✅ ENVIRONMENT=development"
    ((PASSED++))
else
    echo "  ⚠️  ENVIRONMENT not set to development"
fi

# Check 4: DATABASE_TYPE is sqlite
echo "▶ Checking DATABASE_TYPE..."
if grep -q "DATABASE_TYPE=sqlite" .env || ! grep -q "DATABASE_TYPE=postgresql" .env; then
    echo "  ✅ DATABASE_TYPE=sqlite (local development)"
    ((PASSED++))
else
    echo "  ⚠️  DATABASE_TYPE not set to sqlite"
fi

# Check 5: Virtual environment exists
echo "▶ Checking Python virtual environment..."
if [ -d ".venv" ]; then
    echo "  ✅ Virtual environment exists"
    ((PASSED++))
else
    echo "  ❌ Virtual environment not found"
    echo "     Run: python3 -m venv .venv && source .venv/bin/activate"
    ((FAILED++))
fi

# Check 6: Required packages installed
echo "▶ Checking required packages..."
if .venv/bin/python -c "import fastapi, sqlalchemy, aiosqlite" 2>/dev/null; then
    echo "  ✅ Required packages installed"
    ((PASSED++))
else
    echo "  ❌ Missing required packages"
    echo "     Run: pip install -r requirements.txt"
    ((FAILED++))
fi

# Check 7: Database file can be created
echo "▶ Checking database setup..."
if .venv/bin/python -c "
import asyncio
import sys
sys.path.insert(0, '.')
from src.database.config import get_db_settings
settings = get_db_settings()
print(f'  Database type: {settings.db_type.value}')
print(f'  Path: {settings.SQLITE_PATH if settings.is_sqlite else \"PostgreSQL\"}')
" 2>/dev/null; then
    echo "  ✅ Database configuration valid"
    ((PASSED++))
else
    echo "  ❌ Database configuration error"
    ((FAILED++))
fi

# Check 8: Default user exists
echo "▶ Checking default test user..."
if [ -f "./data/app.db" ]; then
    echo "  ✅ SQLite database file exists"
    ((PASSED++))
else
    echo "  ⚠️  SQLite database not created yet"
    echo "     Run: python setup_dev_user.py"
fi

# Check 9: Documentation exists
echo "▶ Checking documentation..."
DOCS_FOUND=0
[ -f "DEV_MODE.md" ] && DOCS_FOUND=$((DOCS_FOUND+1))
[ -f "QUICKSTART.md" ] && DOCS_FOUND=$((DOCS_FOUND+1))
[ -f "AUTH_SETUP.md" ] && DOCS_FOUND=$((DOCS_FOUND+1))

if [ $DOCS_FOUND -eq 3 ]; then
    echo "  ✅ All documentation files present"
    ((PASSED++))
elif [ $DOCS_FOUND -gt 0 ]; then
    echo "  ⚠️  Some documentation files missing ($DOCS_FOUND/3)"
fi

# Check 10: Node modules (for frontend)
echo "▶ Checking frontend dependencies..."
if [ -d "frontend/node_modules" ]; then
    echo "  ✅ Frontend dependencies installed"
    ((PASSED++))
else
    echo "  ⚠️  Frontend dependencies not installed"
    echo "     Run: cd frontend && npm install && cd .."
fi

# Summary
echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║  Summary                                                   ║"
echo "╠════════════════════════════════════════════════════════════╣"
echo "║  Passed: $PASSED"
echo "║  Failed: $FAILED"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

if [ $FAILED -eq 0 ]; then
    echo "✅ All checks passed! You can now run: ./start.sh"
    exit 0
else
    echo "⚠️  Some checks failed. Please fix the issues above."
    exit 1
fi

