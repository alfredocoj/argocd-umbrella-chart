# ArgoCD Umbrella Chart — 5 Technical Demonstrations

A comprehensive suite of hands-on demonstrations covering modern cloud-native development practices: API documentation, GitOps deployment, DevSecOps security scanning, AI-powered code review, and AI-driven operations (AIOps).

**Ideal for**: Technical presentations, engineering workshops, proof-of-concept validation.

---

## 🎯 Overview: The 5 Demos

| # | Demo | Topic | Time | Audience | Status |
|---|------|-------|------|----------|--------|
| 1 | **SDD com OpenAPI** | Specification-Driven Development | 15 min | Developers | ✅ Ready |
| 2 | **Deploy K8s com GitOps** | App-of-Apps Pattern & Self-Healing | 15 min | DevOps/Platform | ✅ Ready |
| 3 | **DevSecOps Pipeline** | Automated Security Scanning | 20 min | Security/DevOps | ⚠️ Partial |
| 4 | **AI Code Review** | GitHub Code Review Automation | 15 min | Developers | 📋 Planned |
| 5 | **AIOps em Ação** | Incident Detection & Auto-Remediation | 20 min | SRE/Ops | ⚠️ Partial |

---

## 📋 Prerequisites

### Minimum Requirements
- **Kubernetes cluster** (v1.28+) — we recommend [Kind](https://kind.sigs.k8s.io/) for local testing
- **kubectl** (v1.28+)
- **Helm** (v3.13+)
- **Docker** (for building images locally)

### Environment Validation Checklist

```bash
# Run this script to validate your environment
kubectl version --short
helm version
docker --version
```

**Expected output:**
```
Client Version: v1.28.x
Helm version: v3.13.x
Docker version x.x.x
```

### For Demo 1 (OpenAPI): Python Prerequisites
- Python 3.11+
- pip/venv
- Tools: `ruff`, `pytest`, `detect-secrets`, `pip-audit`

**Install dependencies:**
```bash
cd demos/openapi/
python -m venv venv
source venv/bin/activate  # or: venv\Scripts\activate (Windows)
pip install -r requirements.txt -r requirements-dev.txt
```

---

## 🚀 Quick Start

### 1️⃣ Prepare Your Cluster

If using Kind, create a fresh cluster:
```bash
cd demos/kind/
./create-cluster.sh  # Creates 'argocd-demo' cluster
```

Then set kubectl context:
```bash
kubectl config use-context kind-argocd-demo
```

### 2️⃣ Install ArgoCD (if not already present)

```bash
# Create namespace
kubectl create namespace argo-cd

# Add Helm repo
helm repo add argo-cd https://argoproj.github.io/argo-helm
helm repo update

# Install via the umbrella chart
helm install argo-cd charts/argo-cd/ --namespace argo-cd

# Wait for ArgoCD to be ready
kubectl wait --for=condition=available --timeout=300s deployment/argo-cd-argocd-server -n argo-cd
```

### 3️⃣ Access ArgoCD Web UI

```bash
# Port-forward to localhost
kubectl port-forward svc/argo-cd-argocd-server 8080:443 -n argo-cd

# Get admin password
ARGOCD_PASSWORD=$(kubectl get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" -n argo-cd | base64 -d)
echo "ArgoCD Admin Password: $ARGOCD_PASSWORD"
```

Visit: **http://localhost:8080**
- Username: `admin`
- Password: [from above command]

---

## 📚 Demo Documentation

Each demo has comprehensive documentation with architecture diagrams, step-by-step walkthroughs, expected output, and troubleshooting.

### Demo 1: SDD com OpenAPI
📖 [Read Full Guide →](./openapi/README.md)

**What you'll learn:**
- Specification-Driven Development (SDD) principles
- OpenAPI 3.0 specification design
- How specs drive code generation and validation
- API testing with pytest
- Security scanning in the CI/CD pipeline

**Quick start:**
```bash
cd demos/openapi/
source venv/bin/activate
python app.py  # Starts Flask server on :8080
```

---

### Demo 2: Deploy K8s com GitOps
📖 [Read Full Guide →](./gitops/README.md)

**What you'll learn:**
- App-of-Apps pattern in ArgoCD
- Declarative vs Imperative deployments
- Automated health checks and self-healing
- Configuration drift detection and correction
- Multi-application orchestration

**Quick start:**
```bash
# Deploy the root-app which manages all sub-applications
helm template charts/root-app/ | kubectl apply -f -

# Watch ArgoCD sync applications
kubectl get applications -n argo-cd -w
```

---

### Demo 3: DevSecOps Pipeline
📖 [Read Full Guide →](./devsecops/README.md)

**What you'll learn:**
- Multi-stage security scanning (SAST, dependency analysis, container scanning)
- Detecting hardcoded secrets and credentials
- Finding CVEs in dependencies (pip-audit, Trivy)
- Container image vulnerability scanning
- Kubernetes misconfiguration detection

**Quick start (review pipeline without triggering):**
```bash
cat .github/workflows/demo-ci.yml  # View pipeline definition
cat .semgrep.yml  # View SAST rules
```

---

### Demo 4: AI Code Review
📖 [Read Full Guide →](./ai-code-review/README.md)

**What you'll learn:**
- GitHub code review automation setup
- AI-powered vulnerability detection (SQLi, secrets, missing type hints)
- Performance issue detection (N+1 queries)
- Automated fix suggestions
- Review workflow integration

**Quick start:**
```bash
# Create example pull request with intentional issues
cd demos/ai-code-review/
./create_example_prs.sh
```

---

### Demo 5: AIOps em Ação
📖 [Read Full Guide →](./aiops/README.md)

**What you'll learn:**
- Automated incident detection and response
- Log and metric correlation with AI
- Root cause analysis automation
- Self-healing mechanisms (HPA, pod restart)
- Observability integration (Prometheus + logs)

**Quick start (simulate incident):**
```bash
cd demos/aiops/
./simulate_incident.sh -n default -l app=todos-demo

# In another terminal, watch logs and metrics
kubectl logs -f deployment/todos-demo -n default
```

---

## 🏗️ Documentation Structure

Each demo includes:

1. **Overview** — What this demo teaches and why it matters
2. **Architecture Diagram** — System components and data flow
3. **Prerequisites Check** — Validation commands
4. **Step-by-Step Walkthrough**
   - Each step numbered and clearly explained
   - Commands to run with expected output
   - Explanation of what's happening
5. **Expected Output** — Full terminal output examples
6. **Common Troubleshooting** — Solutions to typical failures
7. **Next Steps** — How to extend or customize the demo

---

## 🛠️ Tools & Technologies

### API Development & Documentation
- **Framework**: Flask (Python)
- **Spec Format**: OpenAPI 3.0.3
- **Validation**: openapi-spec-validator
- **Testing**: pytest with coverage
- **Security**: pip-audit, detect-secrets

### GitOps & Deployment
- **Container Orchestration**: Kubernetes (v1.28+)
- **Package Manager**: Helm (v3.13+)
- **GitOps Tool**: ArgoCD
- **Local Testing**: Kind (Kubernetes in Docker)

### Security & Scanning
- **SAST**: Semgrep
- **Dependency Scanning**: pip-audit
- **Secret Detection**: detect-secrets
- **Container Scanning**: Trivy
- **Image Registry**: Docker Hub

### Monitoring & Observability
- **Metrics**: Prometheus
- **Visualization**: Grafana (optional, included in Prometheus Helm chart)
- **Log Query**: kubectl logs, Prometheus querying

### AI & Automation
- **Code Review**: GitHub Code Review AI (Copilot integration)
- **AIOps**: Python scripts + Prometheus API + kubectl

---

## 📊 Presentation Flow (Recommended Order)

For a full-day workshop or multi-demo presentation:

| Time | Demo | Activity |
|------|------|----------|
| 09:00–09:20 | **Intro** | Overview of all 5 demos, architecture diagram, prerequisites check |
| 09:20–09:35 | **Demo 1** | SDD & OpenAPI — spec-driven development in practice |
| 09:35–09:50 | **Demo 2** | GitOps — deploy via ArgoCD, show self-healing |
| 09:50–10:10 | **Demo 3** | DevSecOps — trigger pipeline, show security gates |
| 10:10–10:25 | **Q&A + Break** | — |
| 10:25–10:40 | **Demo 4** | AI Code Review — GitHub integration, fix suggestions |
| 10:40–11:00 | **Demo 5** | AIOps — simulate incident, watch auto-remediation |
| 11:00–11:20 | **Wrap-up** | Questions, architecture discussion, deployment strategies |

**Total**: ~2 hours including breaks and Q&A.

---

## 🔍 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     Kubernetes Cluster                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │  ArgoCD      │  │  Prometheus  │  │  Istio       │           │
│  │  (gitops)    │  │  (metrics)   │  │  (networking)│           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
│         │                  │                  │                   │
│         └──────────────────┼──────────────────┘                   │
│                            │                                       │
│  ┌────────────────────────────────────────────────────┐          │
│  │           Application Namespace (default)          │          │
│  ├────────────────────────────────────────────────────┤          │
│  │                                                     │          │
│  │  ┌─────────────────────────────────────┐           │          │
│  │  │  Todos API Demo (Flask)             │           │          │
│  │  │  ├─ Deployment (1 replica)          │           │          │
│  │  │  ├─ Service (ClusterIP :80→:8080)   │           │          │
│  │  │  ├─ Readiness Probe (/ready)        │           │          │
│  │  │  └─ Liveness Probe (/todos)         │           │          │
│  │  └─────────────────────────────────────┘           │          │
│  │                                                     │          │
│  └─────────────────────────────────────────────────────┘          │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    Git Repository                                │
├─────────────────────────────────────────────────────────────────┤
│ ├─ charts/                                                        │
│ │  ├─ argo-cd/     (ArgoCD Helm chart)                           │
│ │  └─ root-app/    (App-of-Apps orchestrator)                   │
│ └─ demos/                                                         │
│    ├─ openapi/     (Flask API + OpenAPI spec)                    │
│    ├─ k8s/         (Deployment + Service manifests)              │
│    └─ aiops/       (Incident simulation + remediation)           │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                  GitHub Repository                               │
├─────────────────────────────────────────────────────────────────┤
│ ├─ .github/workflows/demo-ci.yml                                 │
│ │  └─ Test → Semgrep (SAST) → Trivy (image) → Build & Push      │
│ └─ .semgrep.yml                                                  │
│    └─ Security rules (SQL injection, secrets, K8s misconfig)     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎓 Learning Outcomes

After completing all 5 demos, you will understand:

✅ **Specification-Driven Development** — How specs drive implementation and testing  
✅ **GitOps Patterns** — App-of-Apps, self-healing, drift detection  
✅ **Security Automation** — Multi-layer scanning, policy enforcement  
✅ **AI-Powered Development** — Code review automation, intelligent suggestions  
✅ **AIOps & Observability** — Incident detection, correlation, automated remediation  

---

## 📝 Command Reference

### Quick Commands (Ctrl+C to copy)

**Validate environment:**
```bash
kubectl cluster-info
helm version
docker --version
```

**Check ArgoCD status:**
```bash
kubectl get applications -n argo-cd
kubectl get pods -n argo-cd
argocd app list  # Requires argocd CLI
```

**Watch deployment:**
```bash
kubectl rollout status deployment/todos-demo -n default
kubectl top nodes
kubectl top pods -n default
```

**View logs:**
```bash
kubectl logs -f deployment/todos-demo -n default
kubectl logs -f -n argo-cd deployment/argo-cd-argocd-server
```

**Port-forward services:**
```bash
# ArgoCD Web UI
kubectl port-forward svc/argo-cd-argocd-server 8080:443 -n argo-cd

# Prometheus metrics
kubectl port-forward svc/prometheus-server 9090:80 -n monitor

# API demo
kubectl port-forward svc/todos-demo 8000:80 -n default
```

---

## 🐛 Common Issues

| Issue | Solution |
|-------|----------|
| "Connection refused" on localhost:8080 | Ensure port-forward is running in another terminal: `kubectl port-forward svc/argo-cd-argocd-server 8080:443 -n argo-cd` |
| Pod stuck in "Pending" | Check resource requests: `kubectl describe pod <pod-name>` |
| "ImagePullBackOff" | Ensure docker image exists: `docker pull alfredocoj/api-rest-demo:latest` |
| ArgoCD app shows "Unknown" status | Run manual sync: `argocd app sync <app-name>` or use ArgoCD UI |
| Prometheus metrics missing | Wait 2-3 minutes for scrape intervals, check targets: `http://localhost:9090/targets` |

For more detailed troubleshooting, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

---

## 📞 Next Steps

1. **Pick a demo** from the table above
2. **Check prerequisites** in that demo's README
3. **Follow step-by-step** instructions with expected output
4. **Troubleshoot** using the common issues section
5. **Extend** — modify code, add features, create new scenarios

---

## 📖 Additional Resources

- [ArgoCD Documentation](https://argo-cd.readthedocs.io/)
- [OpenAPI Specification](https://spec.openapis.org/oas/v3.0.3)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Prometheus Querying](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [Semgrep Rules](https://semgrep.dev/r)

---

**Last Updated**: June 2026  
**Maintained By**: Engineering Team  
**License**: See repository LICENSE file
