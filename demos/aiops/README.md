# Demo 5: AIOps em Ação — Incident Detection & Auto-Remediation

Experience AI-driven operations: automatically detect Kubernetes incidents using Prometheus metrics and application logs, perform intelligent root cause analysis, and execute self-healing remediation actions. See how modern SRE practices eliminate manual incident response.

**Duration**: ~20 minutes  
**Difficulty**: Advanced  
**Audience**: SRE, Platform engineers, DevOps architects

---

## 🎯 What You'll Learn

- **Incident Detection** — Identifying anomalies in metrics and logs
- **Metric Correlation** — Using Prometheus to detect resource issues
- **Log Analysis** — Pattern matching to find error signatures
- **Root Cause Analysis** — Intelligent inference of incident causes
- **Auto-Remediation** — Automatic self-healing (HPA, pod restart)
- **Observability Integration** — Combining metrics, logs, and events
- **Reducing MTTR** — Mean Time To Resolution through automation

---

## 🏗️ Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                  Incident Occurs in Pod                         │
│  (e.g., out-of-memory, CPU spike, crashed container)            │
└────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────────────┐
│        📊 Metrics Collection (Prometheus)                       │
│  • container_memory_usage_bytes                                 │
│  • container_cpu_usage_seconds_total                            │
│  • kube_pod_container_status_restarts_total                     │
│  • pod_ready_status (from readiness probes)                     │
└────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────────────┐
│        🔍 Anomaly Detection (AIOps Engine)                      │
│  Compares current metrics vs. baseline/thresholds               │
│  ├─ Memory anomaly? (> 500MB)                                  │
│  ├─ CPU spike? (> 1.5 cores)                                   │
│  ├─ Restart loop? (> 3 restarts)                               │
│  └─ Readiness failure? (not Ready for > 1 min)                 │
└────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────────────┐
│        📝 Log Correlation (Pattern Matching)                    │
│  Analyzes pod logs for error patterns:                          │
│  ├─ "OutOfMemory" / "OOMKilled" → Memory issue                │
│  ├─ "Connection refused" → Connectivity problem                │
│  ├─ "timeout" → Slow/hanging service                           │
│  ├─ "Disk full" → Storage exhaustion                           │
│  └─ "database error" → Dependency failure                      │
└────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────────────┐
│        🤖 Root Cause Analysis (AI-like inference)               │
│  Combines metrics + logs to determine root cause:               │
│  ├─ Memory anomaly + "OOMKilled" logs = OOM issue               │
│  ├─ Readiness failure + "connection refused" = Dependency down  │
│  ├─ High CPU + "database error" = Slow queries                 │
│  └─ Restart count spike + crash logs = Bug introduced          │
│                                                                  │
│  Confidence scoring: 95% = definitive, 60% = investigate        │
└────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────────────┐
│        ✅ Auto-Remediation (Self-Healing Actions)               │
│  Executes appropriate remediation automatically:                │
│  ├─ Enable HPA → Auto-scale to handle load                      │
│  ├─ Restart pod → Clear stuck/crashed state                     │
│  ├─ Scale up → Increase replicas                                │
│  └─ Increase resources → Higher memory/CPU limits               │
│                                                                  │
│  Human approval may be required for critical actions             │
└────────────────────────────────────────────────────────────────┘
                           │
                           ▼
        ✨ System Self-Heals and Returns to Normal
        📊 Incident metrics improve automatically
        📧 Team notified with full incident report
```

---

## ✅ Prerequisites

### Cluster Requirements
- Kubernetes 1.28+
- Prometheus installed in `monitor` namespace
- Application deployed with proper readiness/liveness probes
- kubectl configured and working

### Verify Prerequisites

```bash
# Check Prometheus
kubectl get deployment -n monitor

# Expected output:
# NAME                READY   UP-TO-DATE   AVAILABLE   AGE
# prometheus-server   1/1     1            1           45m

# Check your application
kubectl get deployment -l app=todos-demo

# Check metrics availability
kubectl port-forward svc/prometheus-server 9090:80 -n monitor
# Then visit: http://localhost:9090
# Search for: container_memory_usage_bytes
```

---

## 🚀 Step-by-Step Walkthrough

### Step 1: Understand the Incident Scenario

We'll simulate a real incident where the API pod crashes due to memory exhaustion:

```
Timeline:
  T+0:00  → Pod starts with normal memory (50 MB)
  T+2:30  → Memory usage increases gradually (memory leak)
  T+5:00  → Memory hits limit (512 MB)
  T+5:30  → OOM killer terminates container
  T+6:00  → Kubernetes restarts pod
  T+7:00  → Pod is up but readiness probe failing
  T+8:00  → Anomalies detected + RCA analysis
  T+9:00  → Auto-remediation triggered (HPA enabled)
  T+10:00 → System stabilized, pod running healthy
```

---

### Step 2: Start Monitoring in One Terminal

Keep this running to observe the incident in real-time:

```bash
# Terminal 1: Watch pod status
kubectl get pods -n default -l app=todos-demo -w

# Watch in another window (Terminal 2):
kubectl logs -f deployment/todos-demo -n default

# Or check metrics (Terminal 3):
kubectl port-forward svc/prometheus-server 9090:80 -n monitor

# Then visit: http://localhost:9090/graph
# Query: container_memory_usage_bytes{pod=~"todos-demo.*"}
```

**Expected output (Terminal 1):**
```
NAME                     READY   STATUS    RESTARTS   AGE
todos-demo-abc123-xyz    1/1     Running   0          5m
```

---

### Step 3: Install the AIOps Analysis Tool

The remediation script requires `requests` library:

```bash
cd demos/aiops

# Install dependencies
pip install requests

# Test the script
python correlate_and_remediate.py --help
```

**Expected output:**
```
usage: correlate_and_remediate.py [-h] [--namespace NAMESPACE] 
                                   [--pod-label POD_LABEL] 
                                   [--prometheus PROMETHEUS] 
                                   [--auto-scale] [--restart] 
                                   [--verbose]

AIOps Incident Correlation & Remediation

optional arguments:
  -h, --help               show this help message and exit
  --namespace N            Kubernetes namespace (default: default)
  --pod-label L            Pod label selector (default: todos-demo)
  --prometheus URL         Prometheus URL (default: http://localhost:9090)
  --auto-scale             Enable HPA autoscaling as remediation
  --restart                Restart pods as remediation
  --verbose, -v            Enable verbose logging
```

---

### Step 4: Simulate an Incident

In another terminal, trigger an incident by deleting a pod:

```bash
cd demos/aiops

# Simulate incident: Delete one pod (Kubernetes will auto-restart it)
./simulate_incident.sh default todos-demo
```

**Expected output:**
```
Simulating incident: deleting one pod with label app=todos-demo in namespace default
pod "todos-demo-abc123-xyz" deleted
Pod todos-demo-abc123-xyz deleted. Observability should detect and (optionally) remediate.
```

**In monitoring terminal (Terminal 1), you'll see:**
```
todos-demo-abc123-xyz    1/1  Running   0          5m    # Original pod running
todos-demo-abc123-xyz    0/1  Terminating   0        5m    # Deletion starting
todos-demo-def456-789    0/1  Pending       0        1s    # New pod starting
todos-demo-def456-789    0/1  ContainerCreating 0    3s    # Image pulling
todos-demo-def456-789    1/1  Running       0        8s    # Back to healthy
```

**Recovery time: ~15 seconds** ✅ Auto-healed by Kubernetes

---

### Step 5: Analyze the Incident with AIOps

Now run the root cause analysis:

```bash
cd demos/aiops

# Analyze the incident (detailed analysis)
python correlate_and_remediate.py \
  --namespace default \
  --pod-label todos-demo \
  --prometheus http://localhost:9090 \
  --verbose
```

**Expected output:**
```
2024-06-03 10:30:45 - INFO - Starting AIOps Incident Analysis
2024-06-03 10:30:45 - INFO - Namespace: default, Pod Label: todos-demo
2024-06-03 10:30:45 - INFO - Prometheus: http://localhost:9090
2024-06-03 10:30:45 - INFO - Scanning for anomalies...
2024-06-03 10:30:47 - INFO - Correlating with application logs...
2024-06-03 10:30:48 - INFO - Analyzing root cause...

======================================================================
  INCIDENT ANALYSIS REPORT
======================================================================

📊 DETECTED ANOMALIES:
----------------------------------------------------------------------
  • kube_pod_container_status_restarts_total
    Value: 1.00 (Threshold: 3.00)
    Severity: critical
    Detail: Pod restart count: 1

📝 LOG CORRELATION:
----------------------------------------------------------------------
  Log entries analyzed: 42
  Patterns matched: 1
    • timeout (Connectivity)
      Severity: medium
      Count: 1

🔍 ROOT CAUSE ANALYSIS:
----------------------------------------------------------------------
  Primary Cause: Crash Loop (CrashLoopBackOff)
  Confidence: 92%

  Explanation:
    Pod is repeatedly crashing and restarting. Usually indicates a bug
    introduced in recent code change.

✅ RECOMMENDED ACTIONS:
----------------------------------------------------------------------
  1. Check recent deployments: kubectl rollout history deployment/<name>
  2. Rollback to previous stable version if crash is new
  3. Review pod logs for stack traces: kubectl logs <pod> --previous
  4. Check container startup command and arguments
  5. Increase restart policy delay to prevent rapid restarts

======================================================================
```

**Key insights from the report:**
- 🔴 **Severity**: CRITICAL (pod restarting)
- 🤖 **Confidence**: 92% (high confidence in root cause analysis)
- ✅ **Recommended Actions**: 5 specific steps to investigate and fix

---

### Step 6: Trigger More Complex Incident

Let's create a scenario where you can see HPA recommendations:

```bash
# Create a deployment with memory resource limits
cat > /tmp/test-pod.yaml << 'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: memory-test
  labels:
    app: memory-test
spec:
  containers:
  - name: consumer
    image: polinux/stress
    resources:
      limits:
        memory: "256Mi"
      requests:
        memory: "128Mi"
    command: ["stress"]
    args: ["--vm", "1", "--vm-bytes", "200M", "--vm-hang", "60"]
EOF

# Deploy it
kubectl apply -f /tmp/test-pod.yaml

# Wait 10 seconds for it to request memory
sleep 10

# Analyze the incident
python correlate_and_remediate.py \
  --namespace default \
  --pod-label memory-test \
  --prometheus http://localhost:9090
```

**Expected output (Memory-specific analysis):**
```
📊 DETECTED ANOMALIES:
----------------------------------------------------------------------
  • container_memory_usage_bytes
    Value: 209715200.00 (Threshold: 524288000.00)
    Severity: high
    Detail: Memory usage: 200.0MB

📝 LOG CORRELATION:
----------------------------------------------------------------------
  Patterns matched: 1
    • out_of_memory (Resource Exhaustion)
      Severity: critical
      Count: 1

🔍 ROOT CAUSE ANALYSIS:
----------------------------------------------------------------------
  Primary Cause: Memory Exhaustion (OOM Killer)
  Confidence: 95%

  Explanation:
    Pod exceeded memory limit, triggering OOM killer. Kubernetes 
    automatically terminated the container.

✅ RECOMMENDED ACTIONS:
----------------------------------------------------------------------
  1. Scale up pod resources: increase memory limit in deployment
  2. Analyze code for memory leaks in startup sequence
  3. Enable HPA to auto-scale based on memory pressure
  4. Review application logs for memory-hungry operations

======================================================================
```

---

### Step 7: Enable Auto-Remediation (HPA)

Now execute the remediation actions automatically:

```bash
# For todos-demo: Enable HPA autoscaling
python correlate_and_remediate.py \
  --namespace default \
  --pod-label todos-demo \
  --prometheus http://localhost:9090 \
  --auto-scale
```

**Expected output:**
```
2024-06-03 10:35:22 - INFO - Executing remediation actions...
2024-06-03 10:35:22 - INFO - Enabling HPA for deployment todos-demo...
2024-06-03 10:35:23 - INFO - Created HPA for todos-demo
```

**Verify HPA was created:**

```bash
kubectl get hpa -n default

# Expected output:
# NAME         REFERENCE               TARGETS          MINPODS   MAXPODS   REPLICAS   AGE
# todos-demo   Deployment/todos-demo   23%/70%          2         10        2          30s
```

HPA is now active! The deployment will automatically scale between 2-10 replicas based on CPU/memory usage.

---

### Step 8: Trigger Pod Restart (Remediation)

For simpler incidents, trigger immediate pod restart:

```bash
# Restart the pod
python correlate_and_remediate.py \
  --namespace default \
  --pod-label todos-demo \
  --prometheus http://localhost:9090 \
  --restart
```

**Expected output:**
```
2024-06-03 10:40:15 - INFO - Executing remediation actions...
2024-06-03 10:40:15 - INFO - Restarting pods matching todos-demo...
2024-06-03 10:40:16 - INFO - Restarted deployment todos-demo
```

**Watch the rollout:**

```bash
kubectl rollout status deployment/todos-demo -n default -w

# Expected: Waits for new pods to become ready
```

---

### Step 9: Generate Full Incident Report

Get a detailed analysis with verbose output:

```bash
python correlate_and_remediate.py \
  --namespace default \
  --pod-label todos-demo \
  --prometheus http://localhost:9090 \
  --verbose | tee incident_report.txt

# Report saved to file for documentation
```

---

## 🎓 Key Concepts

### Anomaly Detection Thresholds

| Metric | Threshold | Alert Level | Action |
|--------|-----------|-------------|--------|
| Memory Usage | > 500 MB | HIGH | Consider HPA/scaling |
| CPU Usage | > 1.5 cores | HIGH | Enable HPA |
| Pod Restarts | > 3 in 5 min | CRITICAL | Investigate bug |
| Readiness Failure | > 1 min | HIGH | Check dependencies |

### Root Cause Analysis Confidence

```
95%+  → Take action immediately (auto-remediate)
80-95% → High confidence, execute with caution
60-80% → Medium confidence, recommend human review
<60%  → Low confidence, escalate to human SRE
```

### Remediation Actions

| Incident Type | Remediation | Execution |
|---------------|-------------|-----------|
| Memory OOM | Scale up memory limit, enable HPA | Automated |
| CPU spike | Enable HPA scaling, investigate code | Automated + manual |
| Restart loop | Restart pod, investigate logs | Automated (with approval) |
| Readiness failure | Restart pod, check dependencies | Automated + manual |
| Disk full | Increase PVC, clean logs | Manual (requires approval) |

---

## 🔍 Deep Dive: Log Pattern Examples

The correlation engine recognizes these patterns:

```python
# Memory Issues
"Out of memory"     → Category: Resource Exhaustion
"OOMKilled"         → Severity: CRITICAL
"Memory limit"      → Recommendation: Increase memory request

# Connectivity Issues
"Connection refused"   → Category: Connectivity
"cannot connect"       → Severity: HIGH
"Timeout"              → Recommendation: Check service/network

# Database Issues
"connection timeout"   → Category: Database
"SQL error"           → Severity: HIGH
"query timeout"       → Recommendation: Check DB performance

# Security Issues
"Permission denied"    → Category: Security
"EACCES"              → Severity: HIGH
"Forbidden"           → Recommendation: Review RBAC/credentials
```

---

## 📊 Monitoring Dashboard Integration

For production use, integrate with your monitoring stack:

```yaml
# Example: Alert rule for HPA auto-trigger
groups:
  - name: aiops-auto-remediation
    rules:
    - alert: PodMemoryAnomalyDetected
      expr: |
        container_memory_usage_bytes > 500000000  # 500 MB
      for: 2m
      annotations:
        summary: "Memory anomaly detected on {{ $labels.pod }}"
        action: "Enable HPA auto-scaling"
        dashboard: "http://prometheus:3000/d/aiops-incidents"

    - alert: PodCrashLoop
      expr: |
        increase(kube_pod_container_status_restarts_total[5m]) > 2
      annotations:
        summary: "Pod {{ $labels.pod }} in crash loop"
        action: "Rollback deployment or restart"
```

---

## 🐛 Common Issues & Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| "Failed to query Prometheus" | Prometheus unreachable | Verify port-forward: `kubectl port-forward svc/prometheus-server 9090:80 -n monitor` |
| "No anomalies detected" | Metrics not available | Wait for metrics collection (5 min scrape interval), check targets: http://localhost:9090/targets |
| "Could not retrieve logs" | kubectl not configured | Verify: `kubectl get pods` works, check KUBECONFIG |
| "HPA creation failed" | Metrics server missing | Install: `kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml` |
| "Restart command timed out" | Large deployment | Increase timeout or check for stuck pod |

---

## 🚀 Integration Patterns

### Pattern 1: Alert → Auto-Analysis → Notification

```
Prometheus Alert 🔔
    ↓
Alert webhook triggers script
    ↓
Analysis runs automatically
    ↓
Email sent with full incident report + recommended actions
    ↓
Option: Auto-remediate based on severity
```

### Pattern 2: Scheduled Health Checks

```
CronJob: Run analysis every 5 minutes
    ↓
Detects gradual degradation
    ↓
Triggers HPA before incident occurs
    ↓
Prevents customer-facing outages
```

### Pattern 3: Multi-Cluster Management

```
For each cluster:
  - Run analysis
  - Compare results
  - Identify systemic issues
  - Apply fleet-wide remediation
```

---

## 📊 Metrics Worth Tracking

```
AIOps Effectiveness Metrics:

1. Mean Time To Detection (MTTD)
   - Before: Manual detection (5-30 min)
   - After: Automatic detection (< 1 min)

2. Mean Time To Remediation (MTTR)
   - Before: Manual fix by SRE (30-60 min)
   - After: Automatic remediation (< 2 min)

3. False Positive Rate
   - Percentage of auto-remediations that were incorrect
   - Target: < 5%

4. Incident Prevention Rate
   - % of issues caught before user impact
   - Target: > 80%

5. SRE Toil Reduction
   - % reduction in manual incident response
   - Target: 40-60%
```

---

## 🚀 Next Steps

1. **Deploy to your cluster** — Run AIOps engine in production
2. **Integrate with alerting** — Trigger on Prometheus alerts
3. **Train on patterns** — Add domain-specific log patterns
4. **Measure effectiveness** — Track MTTD, MTTR improvements
5. **Expand remediation** — Add more auto-fix actions over time
6. **Wrap up**: Review [Supporting Docs](../README.md#-supporting-materials)

---

## 📚 Additional Resources

- **Prometheus Querying**: https://prometheus.io/docs/prometheus/latest/querying/basics/
- **Kubernetes Metrics**: https://kubernetes.io/docs/tasks/debug-application-cluster/resource-metrics-pipeline/
- **HPA Configuration**: https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/
- **AIOps Best Practices**: https://www.gartner.com/en/articles/a-practical-approach-to-aiops
- **SRE Book**: https://sre.google/books/

---

**Time to complete**: ~20 minutes  
**Conclusion**: You've seen all 5 demos! 🎉
