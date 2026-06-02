# Troubleshooting Guide for All Demos

Common issues and solutions across all 5 demonstrations.

---

## General Kubernetes Issues

### Issue: "kubectl: command not found"

**Cause**: kubectl not installed or not in PATH

**Solution**:
```bash
# macOS with Homebrew
brew install kubectl

# Linux (Ubuntu/Debian)
sudo apt-get install kubectl

# Or download from: https://kubernetes.io/docs/tasks/tools/install-kubectl-linux/

# Verify installation
kubectl version --client
```

---

### Issue: "The connection to the server was refused"

**Cause**: Kubernetes cluster not running or not configured

**Solution**:
```bash
# Check cluster status
kubectl cluster-info

# Check kubeconfig
cat ~/.kube/config

# For Kind clusters, ensure cluster exists
kind get clusters

# If not, create one
kind create cluster --name argocd-demo

# Set context
kubectl config use-context kind-argocd-demo
```

---

### Issue: Pod stuck in "Pending" state

**Cause**: Resource constraints or misconfiguration

**Solution**:
```bash
# Check pod events
kubectl describe pod <pod-name> -n <namespace>

# Look for:
# - "InsufficientMemory" → Scale up node
# - "InsufficientCPU" → More resources needed
# - "ImagePullBackOff" → Check image exists

# Check node resources
kubectl top nodes
kubectl describe nodes

# If local Kind cluster, increase resource limits
kind delete cluster --name argocd-demo
kind create cluster --name argocd-demo --config - << EOF
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  extraPortMappings:
  - containerPort: 80
    hostPort: 80
  - containerPort: 443
    hostPort: 443
EOF
```

---

### Issue: "ImagePullBackOff" error

**Cause**: Container image not found or authentication failed

**Solution**:
```bash
# Check if image exists in registry
docker pull alfredocoj/api-rest-demo:latest

# If not exist, build locally
cd demos/openapi
docker build -t alfredocoj/api-rest-demo:latest .

# For private registries, check credentials
kubectl get secret -n <namespace> | grep docker
kubectl describe secret <docker-secret-name> -n <namespace>

# If using Docker Hub, ensure image is public or credentials exist
```

---

### Issue: "Resource quota exceeded"

**Cause**: Namespace quota limits reached

**Solution**:
```bash
# Check quotas
kubectl describe resourcequota -n default

# View current usage
kubectl get pods -n default -o json | jq '.items[].spec.containers[].resources'

# Increase or delete quota
kubectl delete resourcequota <name> -n default

# Or create larger quota
kubectl apply -f - << EOF
apiVersion: v1
kind: ResourceQuota
metadata:
  name: default-quota
spec:
  hard:
    requests.cpu: "100"
    requests.memory: "200Gi"
    limits.cpu: "200"
    limits.memory: "400Gi"
EOF
```

---

## Demo 1: SDD com OpenAPI Issues

### Issue: "ModuleNotFoundError: No module named 'flask'"

**Cause**: Dependencies not installed

**Solution**:
```bash
cd demos/openapi

# Check Python version
python --version  # Should be 3.11+

# Create virtual environment (if not already done)
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt -r requirements-dev.txt

# Verify
python -c "import flask; print(flask.__version__)"
```

---

### Issue: "Port 8080 already in use"

**Cause**: Another process using the port

**Solution**:
```bash
# Find process using port
lsof -i :8080  # macOS/Linux

# Or use netstat
netstat -tuln | grep 8080  # Linux
netstat -ano | findstr :8080  # Windows

# Kill the process
kill -9 <PID>  # macOS/Linux
taskkill /PID <PID> /F  # Windows

# Or use a different port
python app.py --port 8081
```

---

### Issue: pytest tests fail with "ConnectionRefusedError"

**Cause**: Flask server not running

**Solution**:
```bash
# Terminal 1: Start the server
cd demos/openapi
source venv/bin/activate
python app.py

# Terminal 2: Run tests
cd demos/openapi
source venv/bin/activate
pytest tests/test_api.py -v
```

---

### Issue: "openapi-spec-validator: command not found"

**Cause**: Tool not installed

**Solution**:
```bash
cd demos/openapi
source venv/bin/activate

# Install
pip install openapi-spec-validator

# Verify
python -m openapi_spec_validator spec.yaml
```

---

## Demo 2: GitOps Issues

### Issue: ArgoCD application stuck in "Syncing"

**Cause**: Network issues, large manifests, or controller overload

**Solution**:
```bash
# Check ArgoCD controller logs
kubectl logs -n argo-cd deployment/argo-cd-argocd-application-controller -f

# Force sync from CLI (if installed)
argocd app sync <app-name> --force

# Or from UI: Applications → Click app → Sync button → Force Sync

# Check application status
kubectl get applications <app-name> -n argo-cd -o yaml | grep -A20 status:

# If persistent, restart controller
kubectl rollout restart deployment/argo-cd-argocd-application-controller -n argo-cd
```

---

### Issue: Pod shows "ImagePullBackOff" after GitOps sync

**Cause**: Image not available in registry specified in manifest

**Solution**:
```bash
# Check the deployment manifest
kubectl get deployment <name> -o yaml | grep image:

# Verify image exists
docker pull <image:tag>

# If not, rebuild and push
cd demos/openapi
docker build -t alfredocoj/api-rest-demo:latest .
docker push alfredocoj/api-rest-demo:latest

# Then sync GitOps app
kubectl patch deployment <name> -p \
  '{"spec":{"template":{"metadata":{"annotations":{"update":"'$(date +%s)'"}}}}}' -n default

# Or use ArgoCD UI to sync
```

---

### Issue: "Application shows OutOfSync but nothing changed"

**Cause**: ArgoCD detected drift (manual changes)

**Solution**:
```bash
# View the diff
argocd app diff <app-name>

# Or check via kubectl
kubectl get deployment <name> -o yaml > current.yaml
kubectl apply -f <manifest> --dry-run=client -o yaml > desired.yaml
diff current.yaml desired.yaml

# Fix: Either:
# 1. Sync ArgoCD (overwrites manual changes)
argocd app sync <app-name>

# 2. Or revert manual changes
kubectl delete pod <pod-name>  # Will be recreated correctly

# 3. Or disable auto-prune if manual changes are desired
kubectl patch application <app-name> -n argo-cd --type merge \
  -p '{"spec":{"syncPolicy":{"automated":{"prune":false}}}}'
```

---

## Demo 3: DevSecOps Issues

### Issue: "semgrep: command not found"

**Cause**: Semgrep not installed

**Solution**:
```bash
# Install Semgrep
pip install semgrep

# Or use Docker
docker run -v . --rm returntocorp/semgrep:latest semgrep --config .semgrep.yml

# Verify
semgrep --version
```

---

### Issue: Semgrep finds no issues but there are obvious vulnerabilities

**Cause**: Rules not loaded or rule file syntax error

**Solution**:
```bash
# Validate rule file syntax
semgrep --validate .semgrep.yml

# Check if rules are actually being used
semgrep --config .semgrep.yml --debug . 2>&1 | grep -i "loaded\|rule"

# List available rules
semgrep --show-supported-languages

# Try simpler test
semgrep --config p/python . | head -20

# If using custom rules, check YAML indentation and syntax
cat .semgrep.yml | head -10  # Verify top-level 'rules:' key
```

---

### Issue: pip-audit finds CVEs but pip list shows updated versions

**Cause**: Requirements file not updated or environment not fresh

**Solution**:
```bash
# Check requirements file
cat requirements.txt | grep <vulnerable-package>

# Update requirements
pip install <package>==<newer-version> -U

# Update requirements.txt
pip freeze > requirements.txt

# Create fresh environment
python -m venv venv-new
source venv-new/bin/activate
pip install -r requirements.txt

# Run audit again
pip-audit
```

---

### Issue: "trivy: command not found"

**Cause**: Trivy not installed

**Solution**:
```bash
# Install Trivy (from https://github.com/aquasecurity/trivy)
# macOS
brew install aquasecurity/trivy/trivy

# Linux
sudo apt-get install trivy

# Or via Docker
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasecurity/trivy image <image-name>

# Verify
trivy --version
```

---

### Issue: GitHub Actions pipeline fails but works locally

**Cause**: Environment difference between local and CI/CD

**Solution**:
```bash
# Check workflow file syntax
yamllint .github/workflows/demo-ci.yml

# Run tests in Docker (matches CI environment)
docker run --rm -v $(pwd):/workspace -w /workspace python:3.11 \
  bash -c "pip install -r requirements.txt && pytest tests/"

# Check if secrets are set in GitHub
# Settings → Secrets → Ensure DOCKERHUB_USERNAME and DOCKERHUB_TOKEN exist

# Debug CI job locally (if using act)
act -j build --secret DOCKERHUB_USERNAME=<username> --secret DOCKERHUB_TOKEN=<token>
```

---

## Demo 4: AI Code Review Issues

### Issue: "Code Review AI" button not showing on PR

**Cause**: Copilot not enabled or you lack permissions

**Solution**:
```bash
# 1. Check if Copilot is enabled for your organization
# Visit: GitHub Settings → Code Security → Code Review AI

# 2. Check your subscription
# Visit: GitHub Settings → Billing → Copilot

# 3. Verify you have access (admin/owner role)
# Organization → Settings → Members → Check your role

# 4. If not enabled, ask admin to enable it
# Organization → Settings → Code Security → Enable Code Review AI

# 5. Try commenting on PR
# @copilot review  # Explicit trigger
```

---

### Issue: AI review seems superficial or misses issues

**Cause**: LLM model limitations or insufficient context

**Solution**:
```bash
# 1. Provide better context in PR description
# Include:
# - What changed and why
# - Known limitations or non-obvious decisions
# - Dependencies on other PRs

# 2. Add code comments for complex sections
# Explain "why", not "what" — AI can see what the code does

# 3. Combine with automated tools
# Semgrep + pip-audit + AI review = comprehensive coverage

# 4. Request re-review if needed
# Add PR comment: @copilot review (forces new analysis)
```

---

## Demo 5: AIOps Issues

### Issue: "Failed to query Prometheus"

**Cause**: Prometheus unreachable or misconfigured

**Solution**:
```bash
# Verify Prometheus is running
kubectl get pod -n monitor | grep prometheus

# Ensure port-forward is active
kubectl port-forward svc/prometheus-server 9090:80 -n monitor

# Check connectivity
curl http://localhost:9090/api/v1/query?query=up

# Verify URL passed to script
python correlate_and_remediate.py \
  --prometheus http://localhost:9090 \
  --verbose

# Check Prometheus targets
# Visit: http://localhost:9090/targets
# All targets should show "UP"
```

---

### Issue: "No anomalies detected" when pod is clearly unhealthy

**Cause**: Metrics not available or thresholds too high

**Solution**:
```bash
# 1. Wait for metrics to accumulate
# Prometheus scrape interval is 15s, storage needs 2-3 minutes

# 2. Check if pod actually has metrics
curl 'http://localhost:9090/api/v1/query?query=container_memory_usage_bytes{pod="<pod>"}' | jq

# 3. Lower thresholds in correlate_and_remediate.py
# Edit: detector.detect_pod_memory_anomaly()
# Change: threshold = 500 * 1024 * 1024  # to lower value

# 4. Ensure metrics are being scraped
# Visit: http://localhost:9090/targets
# Look for kubelet endpoints with pod metrics

# 5. Check if pod label is correct
python correlate_and_remediate.py \
  --namespace default \
  --pod-label <actual-label> \
  --verbose
```

---

### Issue: "HPA creation failed"

**Cause**: Metrics server not installed or HPA config invalid

**Solution**:
```bash
# 1. Check if metrics server is installed
kubectl get deployment -n kube-system | grep metrics-server

# 2. If not, install it
kubectl apply -f \
  https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# 3. Wait for metrics server to be ready
kubectl wait --for=condition=ready pod -l k8s-app=metrics-server -n kube-system --timeout=300s

# 4. Verify metrics are available
kubectl get --raw /apis/metrics.k8s.io/v1beta1/namespaces/default/pods

# 5. Check HPA status
kubectl describe hpa <hpa-name> -n default

# 6. If HPA stuck on "unknown", check metrics:
kubectl get hpa <hpa-name> -w  # Watch status
```

---

### Issue: Pod not restarting when script runs `--restart`

**Cause**: Insufficient permissions or deployment not found

**Solution**:
```bash
# 1. Check pod label is correct
kubectl get pods -n default -l app=todos-demo

# 2. Verify deployment exists
kubectl get deployment -n default

# 3. Check if script has kubectl access
which kubectl
kubectl auth can-i list pods

# 4. Try manual restart
kubectl rollout restart deployment/todos-demo -n default

# 5. If that works, debug script:
python correlate_and_remediate.py \
  --restart \
  --verbose  # Shows detailed logs
```

---

## General Python Issues

### Issue: "SyntaxError: invalid syntax"

**Cause**: Python version mismatch or code syntax error

**Solution**:
```bash
# Check Python version
python --version  # Must be 3.11+

# Check for tabs vs spaces
cat -A file.py | grep -E "^I"  # tabs should be spaces

# Validate syntax
python -m py_compile file.py

# Run with verbose error
python -c "import ast; ast.parse(open('file.py').read())"
```

---

### Issue: "requests.ConnectionError"

**Cause**: Can't connect to remote service

**Solution**:
```bash
# Check if endpoint is accessible
curl http://localhost:9090/api/v1/query

# Check firewall
nc -zv localhost 9090

# For remote endpoints, check:
# 1. Network connectivity
ping <host>
traceroute <host>

# 2. DNS resolution
nslookup <host>

# 3. Service is actually running
kubectl port-forward svc/<service> 9090:80 -n <namespace>

# 4. Try with explicit timeout
curl -m 5 http://localhost:9090/
```

---

## Docker Issues

### Issue: "docker: command not found"

**Cause**: Docker not installed

**Solution**:
```bash
# Install Docker
# macOS
brew install docker

# Linux (Ubuntu/Debian)
sudo apt-get install docker.io
sudo usermod -aG docker $USER
newgrp docker

# Windows
# Download from: https://www.docker.com/products/docker-desktop

# Verify
docker --version
docker run hello-world
```

---

### Issue: "permission denied" when running docker

**Cause**: User not in docker group

**Solution**:
```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Apply new group membership
newgrp docker

# Or use sudo
sudo docker build .

# Verify
docker ps
```

---

### Issue: "failed to solve with frontend dockerfile.v0"

**Cause**: Docker build context or Dockerfile issue

**Solution**:
```bash
# Check Dockerfile exists
ls -la Dockerfile

# Check syntax
hadolint Dockerfile

# Verify working directory
pwd  # Should be directory with Dockerfile

# Check base image exists
docker pull <base-image>

# Try rebuilding with verbose output
docker build --progress=plain .

# Check for layer caching issues
docker build --no-cache .
```

---

## Network Issues

### Issue: "Network timeout" or "connection reset"

**Cause**: Network partition, firewall, or service down

**Solution**:
```bash
# Test connectivity
ping <host>
curl -v http://<host>:<port>

# Check DNS
nslookup <host>
dig <host>

# For Kubernetes services
kubectl get svc <service> -n <namespace>
kubectl get endpoints <service> -n <namespace>

# Test from pod
kubectl run -it debug --image=nicolaka/netshoot -- bash
# Inside pod:
curl http://<service>.<namespace>.svc.cluster.local

# Check network policies
kubectl get networkpolicy -n <namespace>
kubectl describe networkpolicy <policy> -n <namespace>
```

---

## Final Troubleshooting Steps

If none of the above solutions work:

1. **Collect Diagnostic Info**
   ```bash
   # Cluster info
   kubectl cluster-info dump > cluster-dump.txt
   
   # All pod logs
   kubectl logs -n default --all-containers=true -f > pod-logs.txt
   
   # Events
   kubectl get events -n default --sort-by='.lastTimestamp' > events.txt
   ```

2. **Check Logs Thoroughly**
   ```bash
   # Pod logs
   kubectl logs <pod> -n <namespace> --previous
   
   # ArgoCD controller logs
   kubectl logs -n argo-cd deployment/argo-cd-argocd-application-controller
   
   # Prometheus logs
   kubectl logs -n monitor deployment/prometheus-server
   ```

3. **Verify Configuration**
   ```bash
   # Check manifests match expectations
   kubectl get <resource> <name> -o yaml | head -30
   
   # Verify environment variables
   kubectl exec <pod> -n <namespace> -- env | grep IMPORTANT_VAR
   ```

4. **Escalate**
   - Check platform team documentation
   - Review GitHub issues for the project
   - Contact support with diagnostic info from step 1

---

**Last Updated**: June 2026
