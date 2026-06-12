#!/bin/bash
set -euo pipefail

BASE_URL=${1:-http://localhost:8000}
BASE_URL=${BASE_URL%/}

check_endpoint() {
  local path=$1
  local expected_status=$2
  local url="${BASE_URL}${path}"
  local status

  status=$(curl -sS -o /tmp/all4health-smoke-response.txt -w "%{http_code}" "$url")
  if [[ "$status" != "$expected_status" ]]; then
    echo "FAIL ${path}: expected ${expected_status}, got ${status}"
    echo "Response:"
    cat /tmp/all4health-smoke-response.txt
    echo ""
    exit 1
  fi

  echo "OK ${path}: ${status}"
}

echo "All4Health smoke test: ${BASE_URL}"
check_endpoint "/api/v1/health" "200"
check_endpoint "/api/v1/readiness" "200"
check_endpoint "/api/docs" "200"
echo "Smoke test passed."
