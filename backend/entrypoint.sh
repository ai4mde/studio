#!/bin/bash
set -e
umask 002

# Activate the Python virtual environment
source /opt/venv/bin/activate

if [ -t 0 ]; then
  echo "🐚 Interactive terminal, not running boot scripts"
else
  # Run boot scripts when not in an interactive terminal
  echo "🗄️ Waiting for the DB to come online"
  python manage.py wait_for_db

  if ! python manage.py migrate --check >/dev/null 2>&1; then
    echo "💾 Applying database migrations"
    python manage.py migrate --no-input
  fi

  if [ -n "${DJANGO_SUPERUSER_USERNAME:-}" ]; then
    echo "👤 Ensuring admin user"
    python manage.py create_admin \
      --noinput \
      --username "$DJANGO_SUPERUSER_USERNAME" \
      --email "$DJANGO_SUPERUSER_EMAIL" \
      --password "$DJANGO_SUPERUSER_PASSWORD"
  fi
fi

exec "$@"