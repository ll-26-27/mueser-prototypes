#!/bin/sh
# The Next.js site over the same data and log: http://localhost:3001 (Node 20.9+; .node-version names 26.10.0).
cd "$(dirname "$0")/../site" || exit 1
[ -d node_modules ] || npm install --no-audit --no-fund
TIMELINE_WHO="${1:-ben}" npm run dev
