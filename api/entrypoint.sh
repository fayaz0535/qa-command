#!/bin/bash
set -e

echo "Applying database migrations..."
attempt=0
until alembic upgrade head; do
  attempt=$((attempt + 1))
  if [ "$attempt" -ge 10 ]; then
    echo "Alembic migration failed after $attempt attempts — giving up."
    exit 1
  fi
  echo "Migration attempt $attempt failed — retrying in 3s..."
  sleep 3
done
echo "Migrations applied."

echo "Starting API..."
exec uvicorn main:app --host 0.0.0.0 --port 5000 --reload
