# 🚀 Quick Start Guide

## 📝 Default Credentials

### Dev Mode (AUTH_DEV_MODE=true) - No login needed
Auto-authenticated as: `dev@example.com`

### Manual Login (AUTH_DEV_MODE=false)
```
Email:    test@example.com
Password: Test@123456
```

---

## One Command Start

```bash
./start.sh
```

**Result**: Dashboard loads without login ✅

---

## Current Configuration

| Setting | Value |
|---------|-------|
| Dev Mode | ✅ ENABLED (no login needed) |
| Database | SQLite at ./data/app.db |
| Environment | development |
| API | http://localhost:8000 |
| Frontend | http://localhost:5173 |

---

## How to Use

### Development Mode (Current - Recommended)
```bash
./start.sh
# ✅ No login required
# ✅ Dashboard loads instantly
# ✅ Full feature access
```

### Test with Login (Optional)
```bash
# 1. Edit .env: Change AUTH_DEV_MODE=true to false
# 2. Restart: ./start.sh
# 3. Login with credentials above
```

---

## Database Management

```bash
# Create additional test users
python setup_dev_user.py

# Reset database
rm ./data/app.db
python setup_dev_user.py
./start.sh
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Still seeing login? | Check `AUTH_DEV_MODE=true` in .env, restart app |
| API not responding? | Check port 8000 is free, look at terminal logs |
| Database error? | Run `rm ./data/app.db && python setup_dev_user.py` |

---

## URLs

- **Frontend**: http://localhost:5173
- **API Docs**: http://localhost:8000/docs
- **API Server**: http://localhost:8000

---

## Key Environment Variables

```bash
AUTH_DEV_MODE=true              # Dev mode (no login)
ENVIRONMENT=development         # Local dev
DATABASE_TYPE=sqlite            # SQLite for local
SQLITE_PATH=./data/app.db      # Database location
```

