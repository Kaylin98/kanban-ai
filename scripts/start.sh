#!/usr/bin/env sh
set -e
cd "$(dirname "$0")/.."

docker build -t pm-app .
docker rm -f pm-app >/dev/null 2>&1 || true
docker run -d --name pm-app --env-file .env -p 8000:8000 -v pm-data:/app/data pm-app

echo "Running at http://localhost:8000"
