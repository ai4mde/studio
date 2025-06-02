#!/bin/bash
if ! pgrep -x cron > /dev/null; then
    service cron start
fi
exec python -u /usr/src/prototypes/backend/api.py