#!/bin/bash
set -e

# Change ownership of data directory
doas chown -R cfuser:cfuser /chatfront/data

# Start the application
echo "Starting application..."
exec pnpm start