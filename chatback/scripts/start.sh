#!/bin/bash
set -e

# Change ownership of data directory
doas chown -R cbuser:cbuser /chatback/data

# Wait for postgres
echo "Waiting for postgres..."
while ! pg_isready -h postgres -p 5432 -U postgres; do
    sleep 1
done

# Run migrations
echo "Running database migrations..."
alembic upgrade head

# Start the application
echo "Starting application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload 