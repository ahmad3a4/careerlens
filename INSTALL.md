# Installation Guide - CareerLens

> Quick reference guide for getting CareerLens up and running in minutes.

## 🚀 5-Minute Docker Setup (Recommended)

### 1. Create `.env` File
```bash
cp .env.example .env
```

**Then edit `.env` and add your API keys:**
- `OPENROUTER_API_KEY` - Get from https://openrouter.ai/keys
- `RAPID_API_KEY` - Get from https://rapidapi.com

### 2. Start with Docker Compose
```bash
docker-compose up -d
```

### 3. Verify It's Running
```bash
# Check status
docker-compose ps

# View logs
docker-compose logs -f careerlens
```

### 4. Access the API
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs

✅ **Done!** Your API is running.

---

## 🐍 Local Python Setup

### 1. Create `.env` File
```bash
cp .env.example .env
# Edit with your API keys
```

### 2. Setup Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Run Database Migrations
```bash
# Run all pending migrations
alembic upgrade head
```

**Using the migration helper script (Windows):**
```powershell
.\migrate.bat upgrade
```

**Using the migration helper script (macOS/Linux):**
```bash
./migrate.sh upgrade
```

### 5. Run the Application
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 6. Access the API
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs

✅ **Done!** Your API is running.

---

## 📋 What You Need

### Required API Keys (Free Tier Available)

| Service | Link | Purpose |
|---------|------|---------|
| OpenRouter | https://openrouter.ai/keys | LLM/AI Models |
| RapidAPI | https://rapidapi.com | Job Search |

### Software Requirements

| Type | Docker | Local |
|------|--------|-------|
| Docker | ✅ Required | - |
| Python | - | ✅ 3.11+ |
| Git | Optional | Optional |

---

## ⚙️ Environment Variables

Create `.env` file with these values:

```env
# REQUIRED
OPENROUTER_API_KEY=your_key_here
RAPID_API_KEY=your_key_here
DATABASE_URL=sqlite:///./cv_matcher.db

# OPTIONAL
OPENROUTER_MODEL=openai/gpt-4o-mini
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
```

**Database Options:**
- SQLite (default): `sqlite:///./cv_matcher.db`
- PostgreSQL: `postgresql://user:pass@host:5432/db`
- MySQL: `mysql+pymysql://user:pass@host:3306/db`

---

## 🐛 Common Issues

### Port Already in Use

Change port in `docker-compose.yml`:
```yaml
ports:
  - "8001:8000"  # Use 8001 instead of 8000
```

### API Key Errors

Verify in `.env`:
```bash
# Don't use placeholder values
OPENROUTER_API_KEY=sk_...  # Your actual key
RAPID_API_KEY=...          # Your actual key
```

### Module Not Found

```bash
# Ensure venv is activated
source venv/bin/activate  # or ./venv/Scripts/Activate.ps1

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Docker Container Won't Start

```bash
# Check logs
docker-compose logs careerlens

# Common causes:
# 1. Missing .env file
# 2. Invalid API keys
# 3. Port 8000 already in use
```

---

## ✅ Verification

After setup, verify everything works:

```bash
# Docker
docker-compose ps              # Should show 'Up'
curl http://localhost:8000/health

# Local
curl http://localhost:8000/health

# Browser
# Visit http://localhost:8000/docs
# Try the endpoints in the Swagger UI
```

---

## 📚 Next Steps

1. **Read the full README.md** for detailed documentation
2. **Explore the API** at http://localhost:8000/docs
3. **Test endpoints** using Swagger UI (Try it out buttons)
4. **Check logs** for any errors or warnings

---

## 🆘 Still Having Issues?

1. Check README.md Troubleshooting section
2. Verify API keys have available credits
3. Check Docker/Python versions are up to date
4. View logs for detailed error messages:
   ```bash
   docker-compose logs -f careerlens  # Docker
   # or terminal output                # Local
   ```

---

**Need Help?** See the full documentation in [README.md](README.md)
