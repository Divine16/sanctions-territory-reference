#!/usr/bin/env bash
# Cancel a stuck GitHub Pages deployment that blocks new deploys.
# Usage: ./scripts/unblock_pages_deploy.sh [deployment_id_or_commit_sha]

set -euo pipefail
REPO="${GITHUB_REPO:-Divine16/sanctions-territory-reference}"
IDS=(
  "${1:-1d3428500cf37e1736a1b2d8281cdc81ebf0cbfe}"
  "93189fee8e4a933d9c1f5fc69743902d61b7a859"
)

for ID in "${IDS[@]}"; do
  echo "Cancelling Pages deployment ${ID} on ${REPO}…"
  gh api -X POST "repos/${REPO}/pages/deployments/${ID}/cancel" 2>/dev/null || true
  gh api "repos/${REPO}/pages/deployments/${ID}" 2>/dev/null || true
  echo
done
echo ""
echo "Next:"
echo "  1. Settings → Pages → Source: Deploy from a branch → main → /docs"
echo "  2. Wait 5–15 minutes (GitHub clears the lock slowly)"
echo "  3. Push a NEW commit to main (do not only re-run the old workflow)"
echo "  4. Open https://divine16.github.io/sanctions-territory-reference/"
