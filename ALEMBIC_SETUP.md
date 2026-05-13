# Alembic Setup Complete ✅

## What Was Set Up

### 1. **Requirements Updated**
- Added `alembic==1.14.0` to `requirements.txt`

### 2. **Alembic Project Initialized**
```
alembic/
├── __init__.py
├── env.py                          ← Alembic environment config
├── script.py.mako                  ← Migration template
├── alembic.ini                     ← Configuration file
└── versions/
    ├── __init__.py
    └── 001_initial_schema.py       ← Initial migration (creates tables)
```

### 3. **Initial Migration Created**
- **File**: `alembic/versions/001_initial_schema.py`
- **Tables Created**:
  - `users` - User profiles and CV analysis
  - `seen_jobs` - Job tracking for deduplication
- **Includes**: Proper foreign keys, indexes, and cascade deletes

### 4. **Docker Integration**
- **docker-entrypoint.sh**: Runs `alembic upgrade head` on startup
- **Dockerfile**: Uses entrypoint script properly
- ✅ Migrations run automatically before API starts

### 5. **Application Code Updated**
- **app/main.py**: Removed `init_db()` call (Alembic handles migrations)
- **app/core/database.py**: Removed initialization code
- **app/core/init_db.py**: Marked as deprecated

### 6. **Helper Scripts Created**
- **migrate.bat** (Windows) - Easy migration commands
- **migrate.sh** (Linux/Mac) - Easy migration commands

### 7. **Documentation Created**
- **ALEMBIC_QUICK_REF.md** - Quick command reference
- **DATABASE.md** - Comprehensive schema documentation
- **MIGRATIONS.md** - Detailed migration guide
- **INSTALL.md** - Updated with migration steps

---

## Quick Start Guide

### Docker (Easiest)
```bash
docker-compose up -d
```
✅ Migrations run automatically!

### Local Development

**1. Install dependencies:**
```bash
pip install -r requirements.txt
```

**2. Run migrations:**
```bash
alembic upgrade head
```

**3. Start the app:**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Using Helper Scripts

**Windows (PowerShell):**
```powershell
.\migrate.bat upgrade          # Apply migrations
.\migrate.bat create "Description"  # Create new migration
.\migrate.bat history          # See all migrations
```

**Linux/Mac (Bash):**
```bash
./migrate.sh upgrade           # Apply migrations
./migrate.sh create "Description"  # Create new migration
./migrate.sh history           # See all migrations
```

---

## Common Tasks

### Add a New Column to Users Table

**1. Modify model** in `app/core/database.py`:
```python
class User(Base):
    __tablename__ = "users"
    # ... existing columns
    phone = Column(String(20), nullable=True)  # NEW
```

**2. Generate migration:**
```bash
alembic revision --autogenerate -m "Add phone to users"
```

**3. Apply it:**
```bash
alembic upgrade head
```

### Rollback Last Migration
```bash
alembic downgrade -1
```

### View Migration History
```bash
alembic history
```

### Check Current Database Version
```bash
alembic current
```

---

## File Changes Summary

| File | Change | Reason |
|------|--------|--------|
| `requirements.txt` | Added alembic==1.14.0 | Database migrations |
| `app/main.py` | Removed init_db() | Alembic handles it |
| `app/core/database.py` | Removed init_db() function | Alembic handles it |
| `docker-entrypoint.sh` | Added alembic upgrade | Auto-migrations on startup |
| `Dockerfile` | Uses entrypoint.sh | Proper migration execution |
| `INSTALL.md` | Added migration steps | Documentation |

---

## Alembic Project Structure

```
Project Root/
├── alembic/
│   ├── env.py                    ← Configuration (imports models)
│   ├── script.py.mako            ← Template for new migrations
│   └── versions/
│       └── 001_initial_schema.py ← Initial tables
├── alembic.ini                    ← Main config file
├── app/
│   ├── core/
│   │   ├── database.py           ← ORM models (Base metadata source)
│   │   └── config.py             ← DATABASE_URL from env
│   └── main.py
├── docker-entrypoint.sh          ← Runs migrations on startup
├── requirements.txt              ← Includes alembic
└── migrate.bat / migrate.sh      ← Helper scripts
```

---

## Migration Workflow

```
Model Change → Generate Migration → Review → Apply → Test
    ↓              ↓                  ↓        ↓      ↓
database.py    alembic revision    .py file  upgrade  ✅
               --autogenerate
```

---

## Key Benefits

✅ **Version Control** - All schema changes are tracked in Git
✅ **Reversible** - Can rollback any migration
✅ **Automatic Deployment** - Docker handles migrations automatically
✅ **Team Friendly** - Clear migration history for collaboration
✅ **Safety** - No accidental manual schema changes
✅ **Scalability** - Easy to manage growing schema

---

## Next Steps

1. **Install locally**: `pip install -r requirements.txt`
2. **Test migrations**: `alembic upgrade head`
3. **Try adding a column** to understand the workflow
4. **Read ALEMBIC_QUICK_REF.md** for common commands
5. **Deploy with Docker** and see migrations run automatically

---

## Resources

- 📖 [Alembic Documentation](https://alembic.sqlalchemy.org/)
- 📖 [SQLAlchemy Models](https://docs.sqlalchemy.org/en/20/orm/)
- 📖 [PostgreSQL Docs](https://www.postgresql.org/docs/)
- 📋 See `DATABASE.md` for schema details
- ⚡ See `ALEMBIC_QUICK_REF.md` for command reference

---

**Setup completed successfully!** 🎉
Alembic is ready to manage your database migrations.
