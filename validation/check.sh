#!/usr/bin/env bash
set -e

echo "=============================="
echo "Running backend checks"
echo "=============================="

cd api

echo "Running Django tests..."
POSTGRES_HOST=localhost \
POSTGRES_PORT=5432 \
POSTGRES_DB=ai4mdestudio \
POSTGRES_USER=ai4mdestudio \
POSTGRES_PASSWORD=ai4mdestudio \
poetry run python model/manage.py test metadata diagram generator prose prompt -v 2

echo ""
echo "Running Ruff..."
poetry run ruff check .

cd ..

echo ""
echo "=============================="
echo "Running frontend checks"
echo "=============================="

cd frontend

echo "Installing dependencies (if needed)..."
npm ci

echo ""
echo "Running frontend tests..."
npm run test:run

echo ""
echo "Building frontend..."
npm run build

cd ..

echo ""
echo "=============================="
echo "All checks passed 🎉"
echo "=============================="