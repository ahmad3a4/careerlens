# Alembic Quick Reference

## 🚀 Quick Commands

```bash
# ✅ Run all pending migrations (Docker does this automatically)
alembic upgrade head

# 📝 Create new migration after model changes
alembic revision --autogenerate -m "Description here"

# ⏮️  Rollback last migration
alembic downgrade -1

# 📋 Show all migrations
alembic history

# 📍 Show current database version
alembic current

# 🔍 Show detailed migration info
alembic show <revision_id>
```

## Using Helper Scripts

### Windows PowerShell
```powershell
# Upgrade to latest
.\migrate.bat upgrade

# Create new migration
.\migrate.bat create "Add user preferences"

# See history
.\migrate.bat history
```

### macOS/Linux
```bash
# Upgrade to latest
./migrate.sh upgrade

# Create new migration
./migrate.sh create "Add user preferences"

# See history
./migrate.sh history
```

## Typical Workflow

### 1️⃣ Modify Your Model
Edit `app/core/database.py` and add/change columns:
```python
class User(Base):
    __tablename__ = "users"
    # ... existing columns
    new_column = Column(String(255), nullable=True)  # NEW
```

### 2️⃣ Generate Migration
```bash
alembic revision --autogenerate -m "Add new_column to users"
```

### 3️⃣ Review Migration
Open `alembic/versions/xxx_add_new_column_to_users.py` and verify:
- `upgrade()` function creates the column
- `downgrade()` function drops it

### 4️⃣ Apply Migration
```bash
alembic upgrade head
```

### 5️⃣ Verify
```bash
alembic current  # Should show your new migration
```

## Emergency Rollback

If a migration causes issues:

```bash
# Rollback one step
alembic downgrade -1

# Rollback to specific version (from history)
alembic downgrade <revision_id>

# Check what we're at now
alembic current
```

## Docker Deployment

No manual steps needed! The container automatically:
1. Installs requirements
2. **Runs `alembic upgrade head`** ← Happens in docker-entrypoint.sh
3. Starts the FastAPI server

To deploy:
```bash
docker-compose up -d
```

Check logs:
```bash
docker-compose logs -f careerlens
```

## Structure

```
alembic/
├── versions/
│   └── 001_initial_schema.py      ← Database tables created here
├── env.py                          ← Alembic config (don't modify much)
└── script.py.mako                  ← Template for new migrations
```

## Key Files Modified for Alembic

- `requirements.txt` - Added alembic==1.14.0
- `alembic/env.py` - Configured for auto-migrations
- `docker-entrypoint.sh` - Runs migrations before app startup
- `app/main.py` - Removed init_db() call (Alembic handles it now)
- `INSTALL.md` - Added migration steps

## Troubleshooting

### "ModuleNotFoundError: No module named 'app'"
Make sure you're running Alembic from project root:
```bash
cd /path/to/cv_matcher_V2
alembic upgrade head
```

### Migration file is empty
Auto-generation might not detect your changes. Edit the migration file:
```python
def upgrade() -> None:
    op.add_column('users', sa.Column('new_field', sa.String()))

def downgrade() -> None:
    op.drop_column('users', 'new_field')
```

### Can't connect to database
Check `.env` file has valid `DATABASE_URL`:
```
DATABASE_URL=postgresql://user:password@localhost:5432/careerlens
```

---

**Questions?** See `DATABASE.md` for detailed docs
