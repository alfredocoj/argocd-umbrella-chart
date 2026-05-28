#!/usr/bin/env bash
set -euo pipefail

CLUSTER_NAME=argocd-demo
if command -v kind >/dev/null 2>&1; then
  kind delete cluster --name "$CLUSTER_NAME" || true
fi

echo "Cleanup finished."
