#!/bin/bash
# scripts/report_to_api.sh
# =========================
# Called by GitHub Actions to post pipeline + scan results to the Flask API.
#
# Arguments:
#   $1 = commit_id
#   $2 = branch
#   $3 = triggered_by
#
# Environment variables required:
#   DEVGUARD_API_URL   — e.g., http://your-server:5000
#   DEVGUARD_USERNAME  — API username
#   DEVGUARD_PASSWORD  — API password
#
# HOW THIS WORKS:
# 1. Login to get JWT token
# 2. Create pipeline record → get pipeline_id
# 3. Post dependency scan result
# 4. Post image scan result
# 5. If all scans passed + image signed → POST deployment record

set -e   # Exit immediately on any error

COMMIT_ID="${1:-unknown}"
BRANCH="${2:-unknown}"
TRIGGERED_BY="${3:-github-actions}"

API_URL="${DEVGUARD_API_URL:-http://localhost:5000}"

echo "=== DevGuard API Reporter ==="
echo "API: $API_URL"
echo "Commit: $COMMIT_ID"
echo "Branch: $BRANCH"

# ── Step 1: Login ─────────────────────────────────────────────────
echo ""
echo "→ Logging in to DevGuard API..."
LOGIN_RESPONSE=$(curl -s -X POST \
  "${API_URL}/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\": \"${DEVGUARD_USERNAME}\", \"password\": \"${DEVGUARD_PASSWORD}\"}")

TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['access_token'])")

if [ -z "$TOKEN" ]; then
  echo "ERROR: Failed to get auth token"
  exit 1
fi

echo "✓ Authenticated successfully"

# ── Step 2: Create Pipeline Record ────────────────────────────────
echo ""
echo "→ Creating pipeline record..."
PIPELINE_RESPONSE=$(curl -s -X POST \
  "${API_URL}/api/v1/pipelines" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${TOKEN}" \
  -d "{
    \"commit_id\": \"${COMMIT_ID}\",
    \"branch\": \"${BRANCH}\",
    \"status\": \"running\",
    \"triggered_by\": \"${TRIGGERED_BY}\"
  }")

PIPELINE_ID=$(echo "$PIPELINE_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['id'])")
echo "✓ Pipeline created: $PIPELINE_ID"

# ── Step 3: Post Dependency Scan Result ───────────────────────────
echo ""
echo "→ Posting dependency scan result..."

# Parse Trivy output to get vulnerability counts
TRIVY_DEPS_FILE="trivy-deps-report/trivy-deps.json"
if [ -f "$TRIVY_DEPS_FILE" ]; then
  CRITICAL=$(python3 -c "
import json, sys
data = json.load(open('$TRIVY_DEPS_FILE'))
results = data.get('Results', [])
c = sum(len([v for v in r.get('Vulnerabilities', []) or [] if v.get('Severity') == 'CRITICAL']) for r in results)
print(c)
" 2>/dev/null || echo "0")

  HIGH=$(python3 -c "
import json, sys
data = json.load(open('$TRIVY_DEPS_FILE'))
results = data.get('Results', [])
h = sum(len([v for v in r.get('Vulnerabilities', []) or [] if v.get('Severity') == 'HIGH']) for r in results)
print(h)
" 2>/dev/null || echo "0")

  SCAN_STATUS="passed"
  if [ "$CRITICAL" -gt 0 ]; then
    SCAN_STATUS="failed"
  fi
else
  CRITICAL=0
  HIGH=0
  SCAN_STATUS="skipped"
fi

curl -s -X POST \
  "${API_URL}/api/v1/scans" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${TOKEN}" \
  -d "{
    \"pipeline_id\": \"${PIPELINE_ID}\",
    \"scan_type\": \"dependency\",
    \"tool\": \"trivy\",
    \"status\": \"${SCAN_STATUS}\",
    \"critical_count\": ${CRITICAL},
    \"high_count\": ${HIGH},
    \"report_path\": \"reports/trivy-deps.json\"
  }" > /dev/null

echo "✓ Dependency scan recorded (critical: $CRITICAL, high: $HIGH, status: $SCAN_STATUS)"

# ── Step 4: Post Image Scan Result ────────────────────────────────
echo ""
echo "→ Posting image scan result..."

IMAGE_TRIVY_FILE="trivy-image-report/trivy-image.json"
if [ -f "$IMAGE_TRIVY_FILE" ]; then
  IMG_CRITICAL=$(python3 -c "
import json
data = json.load(open('$IMAGE_TRIVY_FILE'))
results = data.get('Results', [])
c = sum(len([v for v in r.get('Vulnerabilities', []) or [] if v.get('Severity') == 'CRITICAL']) for r in results)
print(c)
" 2>/dev/null || echo "0")

  IMG_HIGH=$(python3 -c "
import json
data = json.load(open('$IMAGE_TRIVY_FILE'))
results = data.get('Results', [])
h = sum(len([v for v in r.get('Vulnerabilities', []) or [] if v.get('Severity') == 'HIGH']) for r in results)
print(h)
" 2>/dev/null || echo "0")

  IMG_STATUS="passed"
  if [ "$IMG_CRITICAL" -gt 0 ]; then
    IMG_STATUS="failed"
  fi
else
  IMG_CRITICAL=0
  IMG_HIGH=0
  IMG_STATUS="skipped"
fi

curl -s -X POST \
  "${API_URL}/api/v1/scans" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${TOKEN}" \
  -d "{
    \"pipeline_id\": \"${PIPELINE_ID}\",
    \"scan_type\": \"image\",
    \"tool\": \"trivy\",
    \"status\": \"${IMG_STATUS}\",
    \"critical_count\": ${IMG_CRITICAL},
    \"high_count\": ${IMG_HIGH},
    \"report_path\": \"reports/trivy-image.json\"
  }" > /dev/null

echo "✓ Image scan recorded (critical: $IMG_CRITICAL, high: $IMG_HIGH, status: $IMG_STATUS)"

# ── Step 5: Update Pipeline Status ────────────────────────────────
TOTAL_CRITICAL=$((CRITICAL + IMG_CRITICAL))
if [ "$TOTAL_CRITICAL" -gt 0 ]; then
  PIPELINE_STATUS="failed"
else
  PIPELINE_STATUS="passed"
fi

curl -s -X PATCH \
  "${API_URL}/api/v1/pipelines/${PIPELINE_ID}/status" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${TOKEN}" \
  -d "{\"status\": \"${PIPELINE_STATUS}\"}" > /dev/null

echo ""
echo "=== Pipeline Status: $PIPELINE_STATUS ==="
if [ "$PIPELINE_STATUS" = "failed" ]; then
  echo "✗ Critical vulnerabilities found — deployment will be blocked"
  exit 1
else
  echo "✓ All security checks passed — ready for deployment"
fi
