#!/bin/bash
set -e
umask 002

# shellcheck disable=SC1091
source /usr/src/.venv/bin/activate

if [ -t 0 ] ; then
  echo "🐚 interactive terminal, not running boot scripts"
else
  # run boot scripts if not an interactive terminal (such as /bin/bash)
  echo "🗄️ Waiting for the DB to come online"
  /usr/src/prototypes/manage.py wait_for_db
  if ! /usr/src/prototypes/manage.py migrate --check >/dev/null 2>&1; then
    echo "💾 Applying database migrations"
    /usr/src/prototypes/manage.py migrate --no-input
  fi
  if [ "$DJANGO_SUPERUSER_USERNAME" ]; then
    echo "👤 Ensuring admin user"
    /usr/src/prototypes/manage.py create_admin \
      --noinput \
      --username $DJANGO_SUPERUSER_USERNAME \
      --email $DJANGO_SUPERUSER_EMAIL \
      --password $DJANGO_SUPERUSER_PASSWORD
  fi
fi

exec "$@"