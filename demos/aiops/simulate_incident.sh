#!/usr/bin/env bash
set -euo pipefail

NS=${1:-default}
APP_LABEL=${2:-todos-demo}

echo "Simulating incident: deleting one pod with label app=$APP_LABEL in namespace $NS"
POD=$(kubectl get pods -n "$NS" -l app="$APP_LABEL" -o jsonpath='{.items[0].metadata.name}')
if [ -z "$POD" ]; then
  echo "No pod found for label app=$APP_LABEL in ns $NS"
  exit 0
fi

kubectl delete pod "$POD" -n "$NS"
echo "Pod $POD deleted. Observability should detect and (optionally) remediate."
