#!/usr/bin/env bash
set -euo pipefail

CLUSTER_NAME=argocd-demo
if ! command -v kind >/dev/null 2>&1; then
  echo "kind is required (https://kind.sigs.k8s.io/)"
  exit 1
fi

echo "Creating kind cluster: $CLUSTER_NAME"
kind create cluster --name "$CLUSTER_NAME"

echo "Waiting for cluster to be ready"
kubectl wait --for=condition=Ready nodes --all --timeout=120s
