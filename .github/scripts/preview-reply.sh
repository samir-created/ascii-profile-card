#!/usr/bin/env bash
# Post the preview bot's reply on issue $NUMBER, or update it if it already replied,
# so the issue has one reply that goes from "building" to the card (or the error).
# Usage: preview-reply.sh <file with the reply's markdown>   (needs GH_TOKEN, REPO, NUMBER)
set -euo pipefail
marker="<!-- ascii-profile-card:preview -->"
id=$(gh api "repos/$REPO/issues/$NUMBER/comments" --paginate \
  --jq ".[] | select(.user.login == \"github-actions[bot]\" and (.body | contains(\"$marker\"))) | .id" | tail -n1)
if [ -n "$id" ]; then
  gh api -X PATCH "repos/$REPO/issues/comments/$id" -F body=@"$1" > /dev/null
else
  gh issue comment "$NUMBER" --repo "$REPO" --body-file "$1" > /dev/null
fi
