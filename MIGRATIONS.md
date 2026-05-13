"""
Alembic Database Migration Commands Guide
==========================================

This file documents how to use Alembic for database migrations in CareerLens.

### Initial Setup (Already Done)
- Alembic is initialized in the 'alembic' directory
- Initial migration created: 001_initial_schema.py

### Common Commands

# Run all pending migrations
alembic upgrade head

# Create a new migration (auto-generate from model changes)
alembic revision --autogenerate -m "Description of changes"

# Create an empty migration (for custom SQL)
alembic revision -m "Description of changes"

# See current database version
alembic current

# See migration history
alembic history

# Downgrade to previous migration
alembic downgrade -1

# Downgrade to specific version
alembic downgrade <revision_id>

# Upgrade to specific version
alembic upgrade <revision_id>

### Migration Files
- Located in: alembic/versions/
- Naming: <revision_id>_<description>.py
- Each has upgrade() and downgrade() functions

### For Local Development

1. Install Alembic (already in requirements.txt):
   pip install alembic

2. Run migrations before starting the app:
   alembic upgrade head

3. After modifying models, generate migration:
   alembic revision --autogenerate -m "your description"

4. Review the generated migration file carefully

5. Run the migration:
   alembic upgrade head

### For Docker

- Migrations run automatically on container startup
- The docker-entrypoint.sh runs: alembic upgrade head
- No manual intervention needed

### Rollback Procedures

# Rollback last migration
alembic downgrade -1

# Rollback to specific version
alembic downgrade <revision_id>

### Troubleshooting

If migrations fail:
1. Check DATABASE_URL environment variable is set
2. Ensure PostgreSQL is running and accessible
3. Review alembic/env.py configuration
4. Check migration file syntax

For detailed Alembic docs: https://alembic.sqlalchemy.org/
"""
