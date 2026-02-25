#!/usr/bin/env bash
# setup_webhook.sh — Helper script to configure a GitHub webhook for the monitor.
#
# Usage:
#   export GITHUB_TOKEN=your_personal_access_token
#   ./setup_webhook.sh <owner/repo> <webhook_url> <webhook_secret>
#
# Requires: curl, jq

set -euo pipefail

if [ $# -lt 3 ]; then
    echo "Usage: $0 <owner/repo> <webhook_url> <webhook_secret>"
    echo "Example: $0 octocat/hello-world https://example.com/webhook my-secret"
    exit 1
fi

REPO="$1"
WEBHOOK_URL="$2"
WEBHOOK_SECRET="$3"
GITHUB_TOKEN="${GITHUB_TOKEN:?Error: GITHUB_TOKEN environment variable is required}"

echo "Creating webhook for ${REPO}..."
echo "  URL: ${WEBHOOK_URL}"

RESPONSE=$(curl -s -X POST \
    -H "Authorization: token ${GITHUB_TOKEN}" \
    -H "Accept: application/vnd.github.v3+json" \
    "https://api.github.com/repos/${REPO}/hooks" \
    -d @- <<EOF
{
    "name": "web",
    "active": true,
    "events": ["push", "pull_request", "create", "delete", "issues"],
    "config": {
        "url": "${WEBHOOK_URL}",
        "content_type": "json",
        "secret": "${WEBHOOK_SECRET}",
        "insecure_ssl": "0"
    }
}
EOF
)

HOOK_ID=$(echo "$RESPONSE" | jq -r '.id // empty')

if [ -n "$HOOK_ID" ]; then
    echo "✓ Webhook created successfully (ID: ${HOOK_ID})"
    echo "  Events: push, pull_request, create, delete, issues"
else
    echo "✗ Failed to create webhook:"
    echo "$RESPONSE" | jq '.'
    exit 1
fi
