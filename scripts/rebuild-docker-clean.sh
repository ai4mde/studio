#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "Stopping Studio containers and removing project-built images..."
docker compose down --remove-orphans --rmi local

echo "Pruning dangling images and build cache..."
docker image prune -f
docker builder prune -f

echo "Building fresh images without cache..."
docker compose build --no-cache --pull

echo "Starting Studio with the fresh images..."
docker compose up -d --force-recreate

echo "Done. Open http://ai4mde.localhost"
