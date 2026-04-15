#!/usr/bin/env bash
set -e

# -------------------------
# Backend (Sphinx)
# -------------------------

# 1. Regenerate API docs (structure step)
sphinx-apidoc -f -o docs/backend/source/api api/model */migrations */__pycache__ --templatedir=docs/backend/templates

# 2. Build HTML documentation
sphinx-build -b html docs/backend/source docs/backend/build/html -E -a -v

# -------------------------
# Guides (Sphinx)
# -------------------------

# 1. Build HTML documentation
sphinx-build -b html docs/guides/source docs/guides/build/html -E -a -v

# -------------------------
# Frontend (TypeDoc)
# -------------------------

# Go to frontend project
cd frontend

# Run TypeDoc
npx typedoc

# Return to root
cd ..
