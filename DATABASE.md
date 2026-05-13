# Database Schema Documentation

## Overview
CareerLens uses PostgreSQL with SQLAlchemy ORM and Alembic for schema management and migrations.

## Tables

### Users Table (`users`)
Stores user profiles and their CV analysis history.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTO-INCREMENT | Unique user identifier |
| `email` | VARCHAR(255) | UNIQUE, NOT NULL, INDEX | User's professional email |
| `job_query` | VARCHAR(255) | NOT NULL | Job search query/title |
| `alert_interval_hours` | INTEGER | DEFAULT: 6 | Hours between job alerts |
| `candidate_summary` | JSONB | NOT NULL | Structured CV analysis result |
| `best_score` | INTEGER | DEFAULT: 0 | Highest matching score achieved |
| `created_at` | TIMESTAMP | DEFAULT: now() | Account creation timestamp |
| `last_triggered_at` | TIMESTAMP | NULLABLE | Last alert trigger time |

**Indexes:**
- `email` (UNIQUE) - For fast user lookup

---

### SeenJobs Table (`seen_jobs`)
Tracks jobs already shown to users to avoid duplicates.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTO-INCREMENT | Unique job record identifier |
| `user_id` | INTEGER | FOREIGN KEY → users.id (CASCADE) | Reference to user |
| `job_link` | TEXT | NOT NULL | Job posting URL |
| `job_score` | INTEGER | DEFAULT: 0 | Matching score for this job |
| `seen_at` | TIMESTAMP | DEFAULT: now() | When job was shown to user |

**Indexes:**
- `user_id` (FOREIGN KEY) - For filtering jobs by user

**Relationships:**
- One User → Many SeenJobs (cascade delete)

---

## Migration System

### Using Alembic

Alembic manages all schema changes in a version-controlled, reversible manner.

**Current Migrations:**
- `001_initial_schema` - Creates users and seen_jobs tables

### Common Workflow

#### View Current Schema Version
```bash
alembic current
```

#### Run All Pending Migrations
```bash
alembic upgrade head
```

#### Create a New Migration

After modifying models in `app/core/database.py`:

```bash
alembic revision --autogenerate -m "Description of your changes"
```

This auto-generates migration based on model differences.

#### Review Generated Migration
- Check `alembic/versions/<revision_id>_<name>.py`
- Review `upgrade()` and `downgrade()` functions
- Modify if needed for complex changes

#### Apply Migration
```bash
alembic upgrade head
```

#### Rollback Changes
```bash
# Rollback last migration
alembic downgrade -1

# Rollback to specific version
alembic downgrade <revision_id>
```

#### View Migration History
```bash
alembic history
```

---

## Adding New Tables

1. **Define Model** in `app/core/database.py`:
```python
class NewTable(Base):
    __tablename__ = "new_table"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    # ... more columns
```

2. **Generate Migration**:
```bash
alembic revision --autogenerate -m "Add new_table"
```

3. **Review Migration** in `alembic/versions/`

4. **Apply Migration**:
```bash
alembic upgrade head
```

---

## Environment Variables

Alembic uses `DATABASE_URL` from `.env`:
```
DATABASE_URL=postgresql://user:password@localhost:5432/careerlens
```

---

## Migration Files Structure

```
alembic/
├── env.py                  # Alembic environment config
├── script.py.mako          # Migration template
├── versions/
│   ├── 001_initial_schema.py
│   ├── 002_example_migration.py
│   └── ...
└── alembic.ini             # Configuration file
```

---

## Best Practices

1. **Always Review Generated Migrations** - Auto-generation isn't perfect
2. **Test Migrations Locally** - Before deploying
3. **Write Clear Descriptions** - Use meaningful migration names
4. **Keep Migrations Small** - One logical change per migration
5. **Test Rollbacks** - Ensure downgrade() functions work
6. **Use Migration Comments** - Document complex changes

---

## Troubleshooting

**Migration fails with "table already exists"**
- Check database state: `alembic current`
- Verify no conflicts between manual schema changes

**Downgrade not working**
- Check downgrade() function in migration file
- May need to manually clean up if downgrade() is incomplete

**Autogenerate missing changes**
- Alembic may not detect all changes
- Manually edit migration if needed
- Check model definitions match database

---

## Docker Deployment

Migrations run automatically on container startup:
```bash
docker-compose up
```

The `docker-entrypoint.sh` runs `alembic upgrade head` before starting the API server.

---

## References
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLAlchemy ORM Tutorial](https://docs.sqlalchemy.org/en/20/orm/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
