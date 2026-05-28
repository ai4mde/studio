#!/bin/sh
set -e
npm run build
cp -r /usr/src/app/dist/* /usr/share/nginx/html/
exec nginx -g 'daemon off;'
