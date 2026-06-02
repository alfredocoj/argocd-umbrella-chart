# Quick Reference — Copy-Paste Commands for All Demos

Fast commands for running each demo without reading full documentation.

---

## Demo 1: SDD com OpenAPI

### Setup
```bash
cd demos/openapi
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
```

### Run
```bash
# Terminal 1: Start API server
python app.py

# Terminal 2: Test endpoints
curl http://localhost:8080/ready
curl http://localhost:8080/todos
curl -X POST http://localhost:8080/todos \
  -H "Content-Type: application/json" \
  -d '{"title":"Demo task"}'

# Terminal 3: Run tests
pytest tests/test_api.py -v --cov=app

# Security scans
pip-audit
detect-secrets scan --all-files
ruff check .
semgrep --config ../../.semgrep.yml .
```

### Validate Spec
```bash
python -m openapi_spec_validator spec.yaml
```

---

## Demo 2: Deploy K8s com GitOps

### Verify ArgoCD
```bash
kubectl cluster-info
kubectl get namespace argo-cd
kubectl get deployment -n argo-cd
```

### Deploy via GitOps
```bash
# Deploy root-app (manages all others)
helm template charts/root-app/ | kubectl apply -f -

# Watch applications sync
kubectl get applications -n argo-cd -w

# Check todos-app specifically
kubectl get application todos-app -n argo-cd
kubectl describe application todos-app -n argo-cd
```

### Access ArgoCD UI
```bash
# Port-forward
kubectl port-forward svc/argo-cd-argocd-server 8080:443 -n argo-cd &

# Get password
kubectl get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" -n argo-cd | base64 -d

# Visit: https://localhost:8080
# Username: admin
# Password: [from above]
```

### Demo Drift Detection
```bash
# Cause drift (change image)
kubectl set image deployment/todos-demo \
  api=alpine:latest -n default --record

# Verify drift detected
kubectl get application todos-app -n argo-cd -o yaml | grep -i sync

# Watch auto-correction (within 3-5 min)
kubectl get pods -n default -w

# Verify it reverted
kubectl get deployment todos-demo -o yaml | grep image:
```

### Check Deployment Status
```bash
kubectl get pods -n default
kubectl logs -f deployment/todos-demo -n default
kubectl port-forward svc/todos-demo 8000:80 -n default
# Test: curl http://localhost:8000/ready
```

---

## Demo 3: DevSecOps Pipeline

### Review Pipeline & Rules
```bash
cat .github/workflows/demo-ci.yml
cat .semgrep.yml | grep -E "id:|severity:" | head -20
```

### Create Vulnerable Code
```bash
# Create file with intentional issues
cp demos/openapi/app.py demos/openapi/app_vulnerable.py

# Edit and add:
# - Hardcoded secret: API_KEY = "sk_live_abc123"
# - SQL injection: f"SELECT * FROM users WHERE id = {user_id}"
# - eval(): eval(expr)
# - os.system(): os.system(command)
# - insecure random: random.random()
```

### Scan with Semgrep
```bash
pip install semgrep

cd demos/openapi
semgrep --config ../../.semgrep.yml app_vulnerable.py --json
# Should find 5+ issues
```

### Scan with pip-audit
```bash
cd demos/openapi
pip-audit --desc
# Shows CVEs in dependencies
```

### Secret Detection
```bash
cd demos/openapi
detect-secrets scan . --all-files --json | jq '.results'
# Shows hardcoded secrets
```

### Container Image Scanning
```bash
# Install Trivy (if needed)
# brew install aquasecurity/trivy/trivy

cd demos/openapi
docker build -t api-demo:test .

trivy image api-demo:test --severity HIGH,CRITICAL
```

### Fix Code & Re-scan
```bash
# Fix vulnerabilities in code
# - Use os.getenv() for secrets
# - Use parameterized SQL queries
# - Remove eval(), use ast.literal_eval()
# - Use subprocess.run() instead of os.system()
# - Use secrets module for crypto

# Re-scan
semgrep --config ../../.semgrep.yml . --json
# Should show 0 findings
```

---

## Demo 4: AI Code Review

### Create Example PRs
```bash
# Create branch with vulnerable code
git checkout -b feature/payment-processing

# Create payment_handler.py with issues:
# - Hardcoded STRIPE_API_KEY
# - SQL injection in queries
# - Missing error handling
# - Storing card numbers in logs
# - Missing type hints

git add demos/openapi/payment_handler.py
git commit -m "feat: add payment processing"
git push origin feature/payment-processing
```

### Trigger Copilot Review
```
# On GitHub PR:
1. Click "Code Review AI" button (or comment "@copilot review")
2. Wait 30-60 seconds for analysis
3. Review AI comments on specific lines
4. Click "Commit suggestion" to apply fixes
```

### Show Fixed Version
```bash
# Create payment_handler_fixed.py with:
# - Environment variables for secrets
# - Parameterized SQL queries
# - Proper type hints
# - Secure logging (no sensitive data)
# - Error handling with try/except

git add demos/openapi/payment_handler_fixed.py
git commit -m "fix: address AI code review findings"
git push origin feature/payment-processing
```

### View in GitHub
```
Visit: github.com/<repo>/pull/<PR-number>
- Review AI comments
- See before/after
- Accept suggestions
- Track as issue if needed
```

---

## Demo 5: AIOps em Ação

### Verify Prerequisites
```bash
kubectl get pods -n monitor | grep prometheus
kubectl get deployment -n default | grep todos-demo

# Port-forward Prometheus
kubectl port-forward svc/prometheus-server 9090:80 -n monitor &

# Check metrics available
curl 'http://localhost:9090/api/v1/query?query=up' | jq
```

### Install AIOps Tool
```bash
cd demos/aiops
pip install requests

# Verify
python correlate_and_remediate.py --help
```

### Simulate Incident
```bash
# Terminal 1: Watch pods
kubectl get pods -n default -w

# Terminal 2: Watch logs
kubectl logs -f deployment/todos-demo -n default

# Terminal 3: Trigger incident
cd demos/aiops
./simulate_incident.sh default todos-demo

# Pod will delete and restart (watched in Terminal 1)
```

### Analyze Incident
```bash
cd demos/aiops

# Basic analysis
python correlate_and_remediate.py \
  --namespace default \
  --pod-label todos-demo \
  --prometheus http://localhost:9090

# With verbose output
python correlate_and_remediate.py \
  --namespace default \
  --pod-label todos-demo \
  --prometheus http://localhost:9090 \
  --verbose
```

### Enable Auto-Remediation
```bash
# Option 1: Enable HPA auto-scaling
python correlate_and_remediate.py \
  --namespace default \
  --pod-label todos-demo \
  --prometheus http://localhost:9090 \
  --auto-scale

# Verify HPA created
kubectl get hpa -n default

# Option 2: Restart pods
python correlate_and_remediate.py \
  --namespace default \
  --pod-label todos-demo \
  --prometheus http://localhost:9090 \
  --restart
```

### Monitor Recovery
```bash
# Check HPA status
kubectl get hpa -n default -w

# Check metrics
kubectl port-forward svc/prometheus-server 9090:80 -n monitor
# Visit: http://localhost:9090/graph
# Query: container_memory_usage_bytes{pod=~"todos-demo.*"}
```

---

## Environment Setup & Teardown

### Full Setup (from scratch)
```bash
# Create Kind cluster
cd demos/kind
./create-cluster.sh

# Set context
kubectl config use-context kind-argocd-demo

# Create namespaces
kubectl create namespace argo-cd
kubectl create namespace monitor

# Install ArgoCD
helm repo add argo-cd https://argoproj.github.io/argo-helm
helm repo update
helm install argo-cd charts/argo-cd/ --namespace argo-cd

# Deploy root-app
helm template charts/root-app/ | kubectl apply -f -

# Wait for sync
kubectl get applications -n argo-cd -w
```

### Full Cleanup
```bash
# Delete Kind cluster
cd demos/kind
./cleanup.sh

# Or if manual:
kind delete cluster --name argocd-demo
```

### Reset to Clean State (keep cluster)
```bash
# Delete all applications
kubectl delete applications --all -n argo-cd

# Delete namespaces
kubectl delete namespace default monitor argo-cd

# Recreate from scratch
helm template charts/root-app/ | kubectl apply -f -
```

---

## Port-Forwarding (All Services)

```bash
# Terminal T1: ArgoCD UI
kubectl port-forward svc/argo-cd-argocd-server 8080:443 -n argo-cd

# Terminal T2: Prometheus metrics
kubectl port-forward svc/prometheus-server 9090:80 -n monitor

# Terminal T3: API demo
kubectl port-forward svc/todos-demo 8000:80 -n default

# Terminal T4: Local Flask dev
python demos/openapi/app.py  # Runs on 8080
```

---

## Useful kubectl Commands

```bash
# Monitoring
kubectl get pods -n <ns> -w              # Watch pods
kubectl get applications -n argo-cd -w   # Watch ArgoCD apps
kubectl top nodes                        # Node resource usage
kubectl top pods -n <ns>                 # Pod resource usage

# Debugging
kubectl logs -f <pod> -n <ns>            # Live logs
kubectl logs <pod> --previous -n <ns>    # Previous run logs
kubectl describe pod <pod> -n <ns>       # Detailed info
kubectl events -n <ns>                   # Recent events

# Deployment
kubectl rollout status deployment/<name> # Monitor rollout
kubectl rollout history deployment/<name> # Version history
kubectl rollout undo deployment/<name>   # Rollback
kubectl rollout restart deployment/<name> # Restart pods

# Scaling
kubectl scale deployment <name> --replicas=3 # Manual scale
kubectl autoscale deployment <name> --min=1 --max=10 # Enable HPA

# Secrets & Config
kubectl get secret -n <ns>                # List secrets
kubectl get configmap -n <ns>             # List configs
kubectl create secret generic <name> --from-literal=key=value # Create secret

# Cleanup
kubectl delete pod <pod> -n <ns>          # Delete pod
kubectl delete deployment <name> -n <ns>  # Delete deployment
kubectl delete namespace <ns>             # Delete namespace
```

---

## GitHub Commands

```bash
# Clone repo
git clone <repo-url>

# Create feature branch
git checkout -b feature/<name>

# Stage and commit
git add .
git commit -m "feat: description"

# Push branch
git push origin feature/<name>

# Create PR
# (On GitHub: https://github.com/<repo>/pull/new/<branch>)

# Rollback to previous
git revert <commit-hash>
git push origin <branch>
```

---

## Python / Virtual Environment

```bash
# Create venv
python -m venv venv

# Activate
source venv/bin/activate      # Linux/macOS
venv\Scripts\activate          # Windows

# Install packages
pip install -r requirements.txt

# Generate requirements file
pip freeze > requirements.txt

# Upgrade package
pip install <package> --upgrade
```

---

## Docker Commands

```bash
# Build image
docker build -t <name>:<tag> .

# Run container
docker run -p 8080:8080 <name>:<tag>

# Push to registry
docker push <registry>/<name>:<tag>

# View images
docker images

# Remove image
docker rmi <image-id>
```

---

## Useful URLs

```
ArgoCD UI:       https://localhost:8080
Prometheus:      http://localhost:9090
API Demo:        http://localhost:8000
Flask (local):   http://localhost:8080
GitHub Repo:     https://github.com/<owner>/<repo>
GitHub Actions:  https://github.com/<owner>/<repo>/actions
GitHub Security: https://github.com/<owner>/<repo>/security
```

---

## Emergency Commands

```bash
# Kill hung port-forward
pkill -f "kubectl port-forward"

# Force delete stuck pod
kubectl delete pod <pod> --grace-period=0 --force -n <ns>

# Clear kubectl cache
kubectl cache clear

# Debug access to pod
kubectl exec -it <pod> -n <ns> -- /bin/bash

# Check what changed
kubectl diff -f deployment.yaml

# Apply without validation (dangerous!)
kubectl apply -f deployment.yaml --validate=false
```

---

**Last Updated**: June 2026  
**For Full Documentation**: See [README.md](README.md)
