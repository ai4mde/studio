#!/bin/bash
set -e
umask 002

# shellcheck disable=SC1091
source /usr/src/.venv/bin/activate

if [ -t 0 ] ; then
  echo "🐚 interactive terminal, not running boot scripts"
else
  # run boot scripts if not an interactive terminal (such as /bin/bash)
  if ! /usr/src/model/manage.py migrate --check >/dev/null 2>&1; then
    echo "💾 Applying database migrations"
    /usr/src/model/manage.py migrate --no-input
  fi
fi

exec "$@"