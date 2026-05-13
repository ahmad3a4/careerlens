# Alembic Setup Verification Checklist

## ✅ Installation Verification

Run this to verify Alembic is properly set up:

```bash
# 1. Verify Alembic is installed
python -m pip list | grep -i alembic
# Expected: alembic 1.14.0

# 2. Check Alembic can find migrations
alembic current
# Expected: Output showing current revision (or None if fresh)

# 3. Check migration history
alembic history --verbose
# Expected: Should show 001_initial_schema

# 4. Verify database models
python -c "from app.core.database import Base, User, SeenJob; print('✓ Models loaded successfully')"
# Expected: ✓ Models loaded successfully

# 5. Check Alembic environment
python -c "import alembic; print(f'✓ Alembic {alembic.__version__} ready')"
# Expected: ✓ Alembic 1.14.0 ready
```

---

## 🐳 Docker Verification

### Build and Test Locally

```bash
# 1. Build the Docker image
docker-compose build

# 2. Start the container
docker-compose up -d

# 3. Check logs for migration success
docker-compose logs careerlens | grep -i "alembic\|migration"
# Expected: Something like "Running database migrations with Alembic..."
#          "Database migrations completed successfully"

# 4. Check if tables were created
docker-compose exec careerlens python << 'EOF'
from sqlalchemy import inspect
from app.core.database import engine
inspector = inspect(engine)
tables = inspector.get_table_names()
print(f"✓ Tables created: {tables}")
EOF
# Expected: ✓ Tables created: ['users', 'seen_jobs']

# 5. Test API is running
curl http://localhost:8000/health
# Expected: Should return a response (check your /health endpoint)

# 6. Stop containers
docker-compose down
```

---

## 🐍 Local Development Verification

### Test Migration Commands

```bash
# Activate virtual environment
# Windows:
.\venv\Scripts\Activate.ps1
# Or Linux/Mac:
source venv/bin/activate

# 1. Check current version
alembic current
# Expected: 001_initial_schema (or similar)

# 2. Show migration history
alembic history
# Expected: Shows 001_initial_schema -> <base>

# 3. Test creating a new migration (don't apply it)
alembic revision -m "test_migration_do_not_apply"
# Expected: New file created in alembic/versions/
# Then delete the test file you just created
```

### Test Database Connection

```bash
python << 'EOF'
from app.core.database import SessionLocal, User, SeenJob
session = SessionLocal()
try:
    # Try to query users
    users = session.query(User).all()
    print(f"✓ Database connected successfully")
    print(f"  Users in database: {len(users)}")
except Exception as e:
    print(f"✗ Database connection failed: {e}")
finally:
    session.close()
EOF
```

---

## 📝 File Verification

Check all required files exist:

```bash
# Unix/Linux/Mac
ls -la alembic/env.py
ls -la alembic/versions/001_initial_schema.py
ls -la alembic.ini
ls -la migrate.sh
ls -la ALEMBIC_QUICK_REF.md

# Windows PowerShell
Test-Path alembic/env.py
Test-Path alembic/versions/001_initial_schema.py
Test-Path alembic.ini
Test-Path migrate.bat
Test-Path ALEMBIC_QUICK_REF.md

# Expected: All should return true/exist
```

---

## 🔍 Quick Test Script

Run this Python script to verify everything:

```python
# test_alembic_setup.py
import sys
from pathlib import Path

print("🔍 Alembic Setup Verification\n")

checks = {
    "alembic directory": Path("alembic").exists(),
    "alembic/env.py": Path("alembic/env.py").exists(),
    "alembic/versions/": Path("alembic/versions").exists(),
    "alembic/versions/001_initial_schema.py": Path("alembic/versions/001_initial_schema.py").exists(),
    "alembic.ini": Path("alembic.ini").exists(),
    "migrate.bat (Windows only)": Path("migrate.bat").exists(),
    "migrate.sh": Path("migrate.sh").exists(),
    "ALEMBIC_QUICK_REF.md": Path("ALEMBIC_QUICK_REF.md").exists(),
    "DATABASE.md": Path("DATABASE.md").exists(),
}

try:
    import alembic
    checks["alembic package"] = True
except ImportError:
    checks["alembic package"] = False

try:
    from app.core.database import Base, User, SeenJob
    checks["database models"] = True
except ImportError as e:
    checks["database models"] = False
    print(f"  Error: {e}")

# Print results
passed = 0
failed = 0
for check, result in checks.items():
    symbol = "✅" if result else "❌"
    print(f"{symbol} {check}")
    if result:
        passed += 1
    else:
        failed += 1

print(f"\n{'='*40}")
print(f"Passed: {passed}/{len(checks)}")
print(f"Failed: {failed}/{len(checks)}")

if failed == 0:
    print("\n🎉 All checks passed! Alembic is ready.")
    sys.exit(0)
else:
    print(f"\n⚠️  {failed} check(s) failed. Review above.")
    sys.exit(1)
```

Save and run:
```bash
python test_alembic_setup.py
```

---

## Common Issues & Fixes

### Issue: "ModuleNotFoundError: No module named 'alembic'"
**Fix**: Install requirements
```bash
pip install -r requirements.txt
```

### Issue: "sqlalchemy.exc.OperationalError: cannot connect to database"
**Fix**: Check DATABASE_URL in `.env`
```bash
# Verify in .env:
# DATABASE_URL=postgresql://user:password@localhost:5432/careerlens
```

### Issue: Migration file is empty
**Fix**: Manually edit `alembic/versions/<file>.py` with your schema changes

### Issue: Docker migrations fail
**Fix**: Check docker logs
```bash
docker-compose logs careerlens
# Look for Alembic error messages
```

---

## Troubleshooting Commands

```bash
# Clear and restart everything (Docker)
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d

# Check migration status
alembic current
alembic history --verbose

# Test rollback (careful!)
alembic downgrade -1
alembic upgrade head

# Verify database schema
psql $DATABASE_URL -c "\dt"  # List tables (requires psql)
```

---

## Success Criteria ✓

Your Alembic setup is successful when:

- [x] Alembic package is installed (`pip list | grep alembic`)
- [x] All files exist (env.py, alembic.ini, 001_initial_schema.py)
- [x] `alembic current` shows the migration version
- [x] `alembic history` shows migration history
- [x] Docker container starts without migration errors
- [x] Tables exist in database after Docker startup
- [x] Can create new migrations with `alembic revision --autogenerate`
- [x] Helper scripts work (migrate.bat or migrate.sh)

---

**Still having issues?** 
Check these docs:
- ALEMBIC_QUICK_REF.md - Command reference
- DATABASE.md - Schema documentation
- ALEMBIC_SETUP.md - Full setup details
