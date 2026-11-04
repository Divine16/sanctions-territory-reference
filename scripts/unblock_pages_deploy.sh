#!/usr/bin/env bash
# Cancel a stuck GitHub Pages deployment that blocks new deploys.
# Usage: ./scripts/unblock_pages_deploy.sh [deployment_id_or_commit_sha]

set -euo pipefail
REPO="${GITHUB_REPO:-Divine16/sanctions-territory-reference}"
ID="${1:-1d3428500cf37e1736a1b2d8281cdc81ebf0cbfe}"

echo "Cancelling Pages deployment ${ID} on ${REPO}…"
gh api -X POST "repos/${REPO}/pages/deployments/${ID}/cancel"
echo "Status:"
gh api "repos/${REPO}/pages/deployments/${ID}" || true
echo ""
echo "Next:"
echo "  1. Settings → Pages → Source: Deploy from a branch → main → /docs"
echo "  2. Wait 5–15 minutes (GitHub clears the lock slowly)"
echo "  3. Push a NEW commit to main (do not only re-run the old workflow)"
echo "  4. Open https://divine16.github.io/sanctions-territory-reference/"
