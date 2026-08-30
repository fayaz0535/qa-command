#!/bin/bash
set -e

APP_DIR="/home/qa-command"
BRANCH="main"

echo ""
echo "╔══════════════════════════════════════╗"
echo "║       QA Command Deploy Script       ║"
echo "║       ZAIMAH TECHNOLOGIES            ║"
echo "╚══════════════════════════════════════╝"
echo ""

cd $APP_DIR

echo "▶ [1/4] Pulling latest from origin/$BRANCH..."
git fetch origin
git checkout $BRANCH
git pull origin $BRANCH
echo "   ✓ Code updated"

echo "▶ [2/4] Checking environment..."
if [ ! -f "$APP_DIR/.env" ]; then
  echo "   ✗ ERROR: .env file not found at $APP_DIR/.env"
  exit 1
fi
echo "   ✓ .env found"

echo "▶ [3/4] Building services (no cache)..."
docker compose build --no-cache api web
echo "   ✓ Build complete"

echo "▶ [4/4] Restarting services (api's entrypoint runs 'alembic upgrade head' before uvicorn starts)..."
docker compose up -d --force-recreate api web
echo "   ✓ Services restarted"

echo "Waiting for services to stabilise..."
sleep 8

echo ""
echo "── Service status ─────────────────────"
docker compose ps

echo ""
echo "── API health ─────────────────────────"
curl -sf http://localhost:5001/health && echo "   ✓ API healthy" || echo "   ✗ API not responding"

echo ""
echo "── Web health ─────────────────────────"
curl -sf http://localhost:3004 > /dev/null && echo "   ✓ Web healthy" || echo "   ✗ Web not responding"

echo ""
echo "══════════════════════════════════════"
echo "  Deploy complete — qa.zaimahtech.ae"
echo "══════════════════════════════════════"
echo ""
