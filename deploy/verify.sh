#!/usr/bin/env bash
set -euo pipefail

echo "=== Running Deployment Verification ==="

sleep 5

ITEMS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/items)
echo "GET http://localhost/items status: $ITEMS_STATUS (Expected: 200)"

ALIVE_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/health/alive)
echo "GET http://localhost/health/alive status: $ALIVE_STATUS (Expected: 403)"

if [ "$ITEMS_STATUS" -ne 200 ]; then
  echo "ERROR: /items endpoint did not return HTTP 200" >&2
  exit 1
fi

if [ "$ALIVE_STATUS" -ne 403 ]; then
  echo "ERROR: /health/alive security check failed. Expected HTTP 403, got $ALIVE_STATUS" >&2
  exit 1
fi

echo "=== Verification Successful! ==="
exit 0
