#!/usr/bin/env bash
# Smoke-test a FinSight API deployment (local or production).
# Usage: ./scripts/smoke-test-api.sh [BASE_URL]
# Example: ./scripts/smoke-test-api.sh https://finsight-ai-bse9.onrender.com

set -euo pipefail

BASE_URL="${1:-http://localhost:8000}"
BASE_URL="${BASE_URL%/}"

echo "Testing FinSight API at ${BASE_URL}"
echo

echo "GET /"
curl -sf "${BASE_URL}/" | python3 -m json.tool
echo

echo "GET /health"
curl -sf "${BASE_URL}/health" | python3 -m json.tool
echo

echo "GET /auth/me (expect 401 without token)"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/auth/me")
if [ "$STATUS" = "401" ]; then
  echo "OK — status 401"
else
  echo "Unexpected status: ${STATUS}"
  exit 1
fi
echo

echo "GET /docs (expect 200)"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/docs")
if [ "$STATUS" = "200" ]; then
  echo "OK — Swagger UI reachable"
else
  echo "Unexpected status: ${STATUS}"
  exit 1
fi

echo
echo "All smoke tests passed."
