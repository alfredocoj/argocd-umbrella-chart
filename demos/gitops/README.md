# Demo 2: Deploy K8s com GitOps — App-of-Apps Pattern

Learn how to manage Kubernetes deployments declaratively using the App-of-Apps pattern in ArgoCD. Understand configuration drift detection, self-healing capabilities, and how to orchestrate multiple applications as a single unit.

**Duration**: ~15 minutes  
**Difficulty**: Intermediate  
**Audience**: DevOps engineers, Platform engineers, SRE

---

## 🎯 What You'll Learn

- **GitOps Principles** — Git as the single source of truth for infrastructure
- **App-of-Apps Pattern** — Orchestrating multiple applications from a single root app
- **Declarative Deployment** — kubectl apply instead of helm install for reproducibility
- **Configuration Drift** — Detecting when actual state diverges from desired state
- **Self-Healing** — Automatic correction of manual changes
- **Health Checks** — Readiness and liveness probes for zero-downtime deployments

---

## 🏗️ Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                  Git Repository                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ charts/root-app/ (root application)                        │ │
│  │  └─ templates/                                              │ │
│  │     ├─ root-app.yaml      (bootstraps itself)               │ │
│  │     ├─ argo-cd.yaml       (manages ArgoCD)                  │ │
│  │     ├─ todos-app.yaml     (our API demo)                    │ │
│  │     ├─ prometheus.yaml    (monitoring)                      │ │
│  │     ├─ istio.yaml         (service mesh)                    │ │
│  │     ├─ kubecost.yaml      (cost tracking)                   │ │
│  │     └─ external-secrets.yaml (secret management)            │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ demos/k8s/ (application manifests)                         │ │
│  │  ├─ deployment.yaml      (todos pod)                       │ │
│  │  └─ service.yaml         (expose on port 80)               │ │
│  └───────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────┘
           │
           │ (git push triggers sync)
           ▼
┌────────────────────────────────────────────────────────────────┐
│             Kubernetes Cluster                                  │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ argocd-cd namespace (system)                              │ │
│  │  ├─ argo-cd-server (UI + API)                             │ │
│  │  ├─ argo-cd-controller-manager                            │ │
│  │  ├─ argo-cd-redis                                         │ │
│  │  └─ [7 Application CRDs] (one per app)                    │ │
│  │     ├─ Application: root-app                              │ │
│  │     ├─ Application: argo-cd (self-managed)                │ │
│  │     ├─ Application: todos-app ◄─── FOCUS OF THIS DEMO     │ │
│  │     ├─ Application: prometheus                            │ │
│  │     ├─ Application: istio                                 │ │
│  │     └─ ...                                                │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ default namespace (applications)                          │ │
│  │  ├─ Deployment: todos-demo                                │ │
│  │  │  └─ Pod: todos-demo-xxxxx (Flask API)                 │ │
│  │  └─ Service: todos-demo (ClusterIP)                       │ │
│  │     └─ Port: 80 → 8080 (pod)                              │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ monitor namespace (optional: Prometheus)                  │ │
│  │  └─ Deployment: prometheus-server                         │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ istio-system namespace (optional: Istio)                  │ │
│  │  └─ Various Istio control plane components                │ │
│  └───────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────┘
```

---

## ✅ Prerequisites

Ensure your environment has:

```bash
# Kubernetes cluster running and configured
kubectl cluster-info
kubectl get nodes

# ArgoCD installed (from main README.md)
kubectl get namespace argo-cd
kubectl get deployment -n argo-cd

# Helm available
helm version
```

**Expected output:**
```
Kubernetes control plane is running at https://...
kubectl version: v1.28+
argocd-argocd-server deployment exists
Helm version: 3.13+
```

---

## 🚀 Step-by-Step Walkthrough

### Step 1: Understand the Root Application Structure

The root-app is a Helm chart that defines all applications in the umbrella:

```bash
cd /path/to/argocd-umbrella-chart

# View the structure
tree charts/root-app/ -L 2
```

**Expected output:**
```
charts/root-app/
├── Chart.yaml
├── values.yaml
└── templates/
    ├── argo-cd.yaml
    ├── root-app.yaml
    ├── todos-app.yaml
    ├── prometheus.yaml
    ├── istio.yaml
    ├── kubecost.yaml
    ├── external-secrets.yaml
    ├── selead-secrets.yaml
    └── _helpers.tpl
```

Each template file is an ArgoCD `Application` CRD (Custom Resource Definition).

---

### Step 2: Examine the Root Application Definition

Let's look at the root-app itself — the bootstrap application:

```bash
cat charts/root-app/templates/root-app.yaml
```

**Expected output (simplified):**
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: root-app
  namespace: argo-cd
spec:
  project: default
  source:
    repoURL: https://github.com/your-repo/argocd-umbrella-chart
    targetRevision: HEAD
    path: charts/root-app
  destination:
    server: https://kubernetes.default.svc
    namespace: argo-cd
  syncPolicy:
    automated:
      prune: true      # Delete resources not in Git
      selfHeal: true   # Correct drift automatically
    syncOptions:
      - CreateNamespace=true
```

**Key Points:**
- 🔄 **Syncs**: Continuously compares Git vs cluster
- 🏥 **Self-heal**: If you kubectl edit a resource, ArgoCD corrects it within 3-5 minutes
- 🗑️ **Prune**: If you delete from Git, ArgoCD removes from cluster
- 📦 **Source**: Git is the single source of truth

---

### Step 3: Examine the Todos Application

This is the application that deploys our Flask API demo from Demo 1:

```bash
cat charts/root-app/templates/todos-app.yaml
```

**Expected output:**
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: todos-app
  namespace: argo-cd
spec:
  project: default
  source:
    repoURL: https://github.com/your-repo/argocd-umbrella-chart
    targetRevision: HEAD
    path: demos/k8s          # Points to deployment + service
  destination:
    server: https://kubernetes.default.svc
    namespace: default       # Deploy to 'default' namespace
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
```

**What this does:**
- 📍 **Source**: Watch `demos/k8s/` directory for manifests
- 🎯 **Destination**: Deploy to `default` namespace in THIS cluster
- 🔄 **Auto-sync**: Whenever `demos/k8s/` changes in Git, automatically sync to cluster

---

### Step 4: View the Kubernetes Manifests

These are the actual resources that will be deployed:

```bash
cat demos/k8s/deployment.yaml
```

**Expected output:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: todos-demo
  namespace: default
spec:
  replicas: 1
  selector:
    matchLabels:
      app: todos-demo
  template:
    metadata:
      labels:
        app: todos-demo
    spec:
      containers:
      - name: api
        image: alfredocoj/api-rest-demo:latest
        ports:
        - containerPort: 8080
        readinessProbe:          # ← Key for zero-downtime deployments
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
        livenessProbe:           # ← Restart if unhealthy
          httpGet:
            path: /todos
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 10
        imagePullPolicy: Always  # Always pull latest
```

```bash
cat demos/k8s/service.yaml
```

**Expected output:**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: todos-demo
  namespace: default
spec:
  type: ClusterIP
  ports:
  - port: 80          # External port
    targetPort: 8080  # Pod port
  selector:
    app: todos-demo   # Routes to deployment
```

---

### Step 5: Deploy the Root Application

Deploy the entire umbrella via the root-app:

```bash
# Option A: Using helm template + kubectl apply (declarative)
helm template charts/root-app/ | kubectl apply -f -

# Option B: Using Helm directly
# helm install root-app charts/root-app/ -n argo-cd
```

**Expected output:**
```
namespace/argo-cd configured
application.argoproj.io/root-app created
application.argoproj.io/argo-cd created
application.argoproj.io/todos-app created
application.argoproj.io/prometheus created
application.argoproj.io/istio created
application.argoproj.io/kubecost created
application.argoproj.io/external-secrets created
application.argoproj.io/selead-secrets created
```

---

### Step 6: Watch Applications Synchronize

Monitor the sync process in real-time:

```bash
# Watch all applications
kubectl get applications -n argo-cd -w
```

**Expected output (updating live):**
```
NAME              SYNC STATUS   HEALTH STATUS
root-app          Syncing       Progressing
root-app          Synced        Healthy          ✅
argo-cd           Syncing       Progressing
argo-cd           Synced        Healthy          ✅
todos-app         Syncing       Progressing
todos-app         Synced        Healthy          ✅
prometheus        Syncing       Progressing
prometheus        Synced        Healthy          ✅
istio             Syncing       Progressing
istio             Synced        Healthy          ✅
...
```

Let this run for 1-2 minutes for all apps to become "Healthy".

---

### Step 7: Verify Todos Deployment

Check that the Flask API pod is running:

```bash
# List pods
kubectl get pods -n default

# Describe the deployment
kubectl describe deployment todos-demo -n default

# View logs
kubectl logs -f deployment/todos-demo -n default
```

**Expected output:**
```
NAME                          READY   STATUS    RESTARTS   AGE
todos-demo-74fb7d4b5-abc123   1/1     Running   0          2m

Deployment: todos-demo
  Replicas: 1 desired | 1 updated | 1 total | 1 available
  Pod Template:
    Labels: app=todos-demo
    Containers:
      api:
        Image: alfredocoj/api-rest-demo:latest
        Ports: 8080/TCP
        Readiness: http-get /ready delay=5s timeout=1s period=5s
        Liveness: http-get /todos delay=10s timeout=1s period=10s

Logs:
 * Running on http://0.0.0.0:8080
 * Debug mode: on
```

---

### Step 8: Test the API via Service

The Service exposes the pod on port 80. Port-forward to test:

```bash
# Port-forward the service
kubectl port-forward svc/todos-demo 8000:80 -n default &

# Test the API
curl http://localhost:8000/ready
curl http://localhost:8000/todos
```

**Expected output:**
```
{"status": "ok"}
[]
```

---

### Step 9: Show Configuration Drift Detection

Now let's demonstrate self-healing. Make a manual change to the deployment:

```bash
# Edit the deployment directly (imperative change)
kubectl set image deployment/todos-demo api=alpine:latest -n default --record
```

**This violates GitOps principles** — the cluster state now differs from Git.

Check the status:

```bash
kubectl get pods -n default
kubectl get deployment todos-demo -n default -o yaml | grep image
```

**Expected output:**
```
todos-demo-99999-abc123  0/1  CrashLoopBackOff

image: alpine:latest   # ← Wrong! Should be alfredocoj/api-rest-demo:latest
```

The pod crashes because `alpine:latest` isn't a Flask server.

---

### Step 10: Watch Self-Healing in Action

Now ArgoCD detects the drift:

```bash
# Check application status
kubectl get applications todos-app -n argo-cd -o yaml | grep -A5 status:

# Or use ArgoCD CLI (if installed)
argocd app get todos-app
```

**Expected output:**
```
status:
  operationState:
    syncResult:
      resources:
      - kind: Deployment
        name: todos-demo
        namespace: default
        syncPhase: Sync
  syncStatus: OutOfSync    # ← DRIFT DETECTED!
```

Within 3-5 minutes (default ArgoCD sync interval), the application will auto-sync:

```bash
# Wait and check again
sleep 5
kubectl get pods -n default
```

**Expected output:**
```
todos-demo-74fb7d4b5-abc123   1/1  Running    0   3m
```

✅ **Back to the correct image!** Self-healing worked.

The deployment is now:
```bash
kubectl get deployment todos-demo -n default -o yaml | grep image
```

**Expected output:**
```
image: alfredocoj/api-rest-demo:latest  # ✅ Restored to Git state
```

---

### Step 11: Access ArgoCD Web UI

Get a visual overview of all applications:

```bash
# Port-forward ArgoCD
kubectl port-forward svc/argo-cd-argocd-server 8080:443 -n argo-cd &

# Get admin password
ARGOCD_PASSWORD=$(kubectl get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" -n argo-cd | base64 -d)
echo "Password: $ARGOCD_PASSWORD"
```

Visit: **https://localhost:8080** (ignore SSL warning for local testing)

- **Username**: `admin`
- **Password**: [from above command]

**In the UI, you'll see:**
- 🌳 Root app tree showing all sub-applications
- 🟢 Green checkmarks for synced apps
- 📊 Resource graph (pods, services, deployments)
- 📝 Diff view (what changed in Git)
- 🔄 Sync/refresh buttons

---

### Step 12: Demonstrate Git-Driven Updates

Make a change to the manifests in Git:

```bash
# Example: Scale replicas from 1 to 2
cat > demos/k8s/deployment.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: todos-demo
  namespace: default
spec:
  replicas: 2    # ← Changed from 1 to 2
  selector:
    matchLabels:
      app: todos-demo
  template:
    metadata:
      labels:
        app: todos-demo
    spec:
      containers:
      - name: api
        image: alfredocoj/api-rest-demo:latest
        ports:
        - containerPort: 8080
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
        livenessProbe:
          httpGet:
            path: /todos
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 10
        imagePullPolicy: Always
EOF
```

Then commit and push to Git:

```bash
git add demos/k8s/deployment.yaml
git commit -m "Scale todos-demo to 2 replicas"
git push origin main
```

Watch ArgoCD detect and sync the change:

```bash
# Watch pods scale up
kubectl get pods -n default -w

# Should see 2 pods running within 30 seconds
```

**Expected output:**
```
NAME                          READY   STATUS    RESTARTS   AGE
todos-demo-74fb7d4b5-abc123   1/1     Running   0          5m
todos-demo-74fb7d4b5-def456   1/1     Running   0          30s
```

✅ **GitOps in action**: Git is the source of truth, cluster converges to match it automatically.

---

## 🎓 Key Concepts

### GitOps Principles

| Principle | Implementation |
|-----------|-----------------|
| **Declarative** | Manifests describe desired state (YAML) |
| **Version Controlled** | All changes tracked in Git |
| **Pull-Based** | ArgoCD pulls from Git, doesn't push |
| **Automatic Reconciliation** | Cluster drifts → ArgoCD corrects it |

### App-of-Apps Pattern Benefits

1. **Modularity** — Each app is independently managed
2. **Orchestration** — Root-app coordinates all sub-apps
3. **Scalability** — Easy to add new apps
4. **Consistency** — All apps follow same sync policy
5. **Self-Bootstrapping** — Root-app manages itself

### Health Checks in Kubernetes

```yaml
readinessProbe:
  # Tells load balancer: ready to receive traffic?
  # Pod removed from Service endpoints if fails
  httpGet:
    path: /ready
    port: 8080
  initialDelaySeconds: 5   # Wait for startup
  periodSeconds: 5         # Check every 5 seconds

livenessProbe:
  # Tells kubelet: is container still alive?
  # Container restarted if fails
  httpGet:
    path: /todos
    port: 8080
  initialDelaySeconds: 10
  periodSeconds: 10
```

This enables **zero-downtime deployments**:
1. New pod starts
2. Liveness probe succeeds
3. Readiness probe succeeds
4. Traffic shifted to new pod
5. Old pod drained

---

## 🐛 Common Issues & Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Application stuck in "Syncing" | Network issue or controller overloaded | Wait 5 min, check: `kubectl logs -n argo-cd deployment/argo-cd-argocd-application-controller` |
| Pod in "Pending" state | Resource quota or node capacity | Check: `kubectl describe pod <pod-name>`, check nodes: `kubectl top nodes` |
| "ImagePullBackOff" | Image doesn't exist or authentication issue | Verify image: `docker pull alfredocoj/api-rest-demo:latest` |
| Application shows "Unknown" | ArgoCD can't reach cluster | Ensure ArgoCD server is running: `kubectl get pods -n argo-cd` |
| Readiness probe keeps failing | /ready endpoint returning error | Check logs: `kubectl logs -f deployment/todos-demo`, verify app is healthy |
| ArgoCD UI shows "Red X" (out of sync) | Manual changes detected (drift) | Sync manually or wait for auto-sync: `argocd app sync todos-app` |

---

## 🔍 Deep Dive: ArgoCD Application CRD

The Application Custom Resource is the heart of GitOps:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: todos-app              # Name of the application
  namespace: argo-cd           # Must be in argo-cd namespace
spec:
  # Which Git repo and path to watch
  source:
    repoURL: https://github.com/your-repo/argocd-umbrella-chart
    targetRevision: HEAD        # Watch main/master branch
    path: demos/k8s             # Path within repo
    
    # Optional: Helm-specific settings
    helm:
      values: |
        replicas: 1
        
    # Optional: Kustomize settings
    # kustomize:
    #   namePrefix: prod-
  
  # Where to deploy
  destination:
    server: https://kubernetes.default.svc  # Current cluster
    namespace: default          # Target namespace
  
  # Project for RBAC
  project: default            # Project ACLs
  
  # Sync strategy
  syncPolicy:
    # Automatic synchronization
    automated:
      prune: true             # Delete if removed from Git
      selfHeal: true          # Correct drift automatically
      allowEmpty: false       # Prevent accidental deletes
    
    # Sync options
    syncOptions:
      - CreateNamespace=true  # Auto-create namespace
      - RespectIgnoreDifferences=true
    
    # Retry policy
    retry:
      limit: 5
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 5m
```

---

## 🚀 Next Steps

1. **Monitor Changes**: Use `kubectl get applications -n argo-cd -w` to watch all apps
2. **Customize Apps**: Edit `charts/root-app/templates/*.yaml` to add new applications
3. **GitOps Workflow**: Any change to Git automatically syncs (no manual kubectl)
4. **Progressive Delivery**: Explore ArgoCD Rollouts for canary deployments
5. **Proceed to Demo 3**: [DevSecOps Pipeline](../devsecops/README.md)

---

## 📚 Additional Resources

- **ArgoCD Documentation**: https://argo-cd.readthedocs.io/
- **App-of-Apps Pattern**: https://argo-cd.readthedocs.io/en/stable/operator-manual/declarative-setup/#app-of-apps
- **Kubernetes Health Checks**: https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/
- **GitOps Guide**: https://www.weave.works/technologies/gitops/

---

**Time to complete**: ~15 minutes  
**Next demo**: [Demo 3: DevSecOps Pipeline](../devsecops/README.md)
