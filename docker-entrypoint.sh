#!/bin/bash

# Docker entrypoint script for CareerLens
# This script runs database migrations and starts the FastAPI application

set -e

echo "================================"
echo "🚀 CareerLens Startup Sequence"
echo "================================"
echo ""
echo "📌 Python version:"
python --version
echo ""

echo "🗄️  Running database migrations with Alembic..."
alembic upgrade head

echo ""
echo "✅ Database migrations completed successfully"
echo "⏳ Starting CareerLens API server..."
echo ""

# Run the FastAPI application with Uvicorn
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 "$@"
