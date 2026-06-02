# Presentation Checklists for Live Demos

Use these checklists to prepare for live demonstrations. Each demo should be rehearsed beforehand.

---

## ✅ Pre-Presentation Setup (1 hour before)

### Environment Validation
- [ ] Kubernetes cluster running (`kubectl cluster-info`)
- [ ] All namespaces created (`kubectl get ns`)
- [ ] ArgoCD installed and healthy (`kubectl get pods -n argo-cd`)
- [ ] Prometheus running (`kubectl get pods -n monitor`)
- [ ] Internet connection stable and fast
- [ ] No other processes using demo ports (8080, 9090, etc.)

### Terminal Setup
- [ ] 4-5 terminal windows open in tiled layout
  - T1: Main demo commands
  - T2: kubectl watch (pods, applications, etc.)
  - T3: Logs viewing (kubectl logs -f)
  - T4: Metrics/monitoring (port-forward)
  - T5: Editor for code (optional)
  
- [ ] Font sizes increased for visibility (14pt minimum)
- [ ] Zoom applied if needed (125%)
- [ ] Terminal color theme readable on projector
- [ ] Test projector/screen sharing works

### Pre-flight Checks (Run 30 min before)

**Check all demo prerequisites:**
```bash
# Demo 1: OpenAPI
cd demos/openapi && python --version && pip list | grep -E "flask|pytest"

# Demo 2: GitOps  
kubectl get applications -n argo-cd | wc -l  # Should show 7+ apps

# Demo 3: DevSecOps
cat .semgrep.yml | grep -c "id:"  # Should show 16+ rules

# Demo 4: AI Code Review
# (No tech requirements, but check GitHub is accessible)

# Demo 5: AIOps
cd demos/aiops && python correlate_and_remediate.py --help
```

Expected output: All commands succeed, no errors

---

## Demo 1: SDD com OpenAPI (15 minutes)

### Pre-Demo Checklist
- [ ] Flask API code reviewed (`demos/openapi/app.py`)
- [ ] OpenAPI spec readable (`cat demos/openapi/spec.yaml`)
- [ ] Tests passing locally (`pytest demos/openapi/tests/`)
- [ ] Know the 3 API endpoints: GET /todos, POST /todos, GET /ready
- [ ] Have curl commands copied to clipboard for quick access
- [ ] Understand why SDD matters (spec-first development)

### During Demo Steps
- [ ] **Step 1** (2 min): Explain SDD concept on slides
- [ ] **Step 2** (2 min): Show spec.yaml, highlight endpoints/schemas
- [ ] **Step 3** (1 min): Start Flask server (`python app.py`)
- [ ] **Step 4** (3 min): Test endpoints with curl
  - [ ] `curl http://localhost:8080/ready`
  - [ ] `curl http://localhost:8080/todos`
  - [ ] `curl -X POST http://localhost:8080/todos -H "Content-Type: application/json" -d '{"title": "Demo task"}'`
- [ ] **Step 5** (2 min): Run tests (`pytest -v`)
- [ ] **Step 6** (2 min): Run pip-audit, show no vulns
- [ ] **Q&A** (1 min): Be ready to explain spec-driven benefits

### Backup Plan
If Flask doesn't start:
- [ ] Pre-build Docker image (`docker build -t api-demo:local demos/openapi/`)
- [ ] Run in container instead (`docker run -p 8080:8080 api-demo:local`)

---

## Demo 2: Deploy K8s com GitOps (15 minutes)

### Pre-Demo Checklist
- [ ] Kubernetes context set to correct cluster (`kubectl config current-context`)
- [ ] ArgoCD root-app deployed (`kubectl get application root-app -n argo-cd`)
- [ ] All 7 applications synced and healthy
- [ ] Know ArgoCD UI password (get from: `kubectl get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" -n argo-cd | base64 -d`)
- [ ] Port-forward ArgoCD ready to go
- [ ] todos-app deployment running (`kubectl get deployment todos-demo -n default`)

### During Demo Steps
- [ ] **Step 1** (2 min): Explain App-of-Apps pattern on slides
- [ ] **Step 2** (1 min): Show root-app.yaml structure
- [ ] **Step 3** (1 min): Show todos-app.yaml pointing to demos/k8s
- [ ] **Step 4** (2 min): Watch applications syncing (`kubectl get applications -n argo-cd -w`)
- [ ] **Step 5** (2 min): Show pod running (`kubectl get pods -n default -w`)
- [ ] **Step 6** (3 min): Demonstrate drift/self-healing
  - [ ] Change pod image: `kubectl set image deployment/todos-demo api=alpine:latest -n default`
  - [ ] Show pod crashes
  - [ ] Wait 5 min, show ArgoCD auto-corrects
  - [ ] Image reverts to correct version
- [ ] **Step 7** (2 min): Show ArgoCD UI with app tree
- [ ] **Q&A** (1 min): Explain why GitOps matters (single source of truth)

### Backup Plan
If self-healing takes too long:
- [ ] Pre-record this section (show video of correction happening)
- [ ] Or manually sync: `argocd app sync todos-app`

---

## Demo 3: DevSecOps Pipeline (20 minutes)

### Pre-Demo Checklist
- [ ] Expanded `.semgrep.yml` reviewed (16+ rules)
- [ ] `app_vulnerable.py` created with 5+ intentional issues
- [ ] GitHub Actions workflow examined (`.github/workflows/demo-ci.yml`)
- [ ] Understand the 6 security gates: tests → lint → pip-audit → semgrep → trivy → push
- [ ] Have GitHub repo ready (if demonstrating real CI/CD)
- [ ] Know what each security tool catches

### During Demo Steps
- [ ] **Step 1** (2 min): Explain DevSecOps pipeline architecture
- [ ] **Step 2** (2 min): Show CI/CD workflow file
- [ ] **Step 3** (1 min): Show .semgrep.yml with all rules
- [ ] **Step 4** (2 min): Create/show vulnerable code file
- [ ] **Step 5** (3 min): Run local Semgrep scan
  - [ ] `semgrep --config .semgrep.yml demos/openapi/app_vulnerable.py`
  - [ ] Show 5+ findings (SQL injection, eval, secrets, etc.)
- [ ] **Step 6** (2 min): Run pip-audit to find CVEs
  - [ ] `pip-audit` (or force demo by showing old requirements)
- [ ] **Step 7** (2 min): Show Docker image scan results (Trivy)
  - [ ] Show CRITICAL/HIGH vulnerabilities found
- [ ] **Step 8** (2 min): Show fixed code and re-scan
  - [ ] All issues resolved
  - [ ] Image now safe to push
- [ ] **Step 9** (2 min): Explain how GitHub Actions blocks bad images
- [ ] **Q&A** (1 min): Discuss shift-left security

### Backup Plan
If tools won't run:
- [ ] Pre-record tool output and show video
- [ ] Or prepare images with vulnerabilities already found

---

## Demo 4: AI Code Review (15 minutes)

### Pre-Demo Checklist
- [ ] GitHub account ready with Copilot access
- [ ] Created test PR with vulnerable code (payment_handler.py)
- [ ] Copilot code review triggered on PR (or know how to trigger)
- [ ] Understand 5 vulnerability types: secrets, SQL injection, N+1 queries, error handling, performance
- [ ] Fixed version of code ready to show
- [ ] Screenshots of AI comments saved (backup)

### During Demo Steps
- [ ] **Step 1** (2 min): Explain GitHub Copilot setup
- [ ] **Step 2** (2 min): Show example vulnerable code
  - [ ] Point out hardcoded secret (STRIPE_API_KEY)
  - [ ] Point out SQL injection (f-string query)
  - [ ] Point out missing error handling
- [ ] **Step 3** (3 min): Show AI code review comments on PR
  - [ ] Hardcoded secret detection
  - [ ] SQL injection warning
  - [ ] Missing type hints
  - [ ] N+1 query pattern
- [ ] **Step 4** (2 min): Show how to accept suggestions
  - [ ] Click "Commit suggestion" button
  - [ ] Code auto-applied to PR
- [ ] **Step 5** (2 min): Show fixed code
  - [ ] Environment variables for secrets
  - [ ] Parameterized SQL queries
  - [ ] Type hints added
  - [ ] All issues resolved
- [ ] **Step 6** (2 min): Discuss benefits for team
- [ ] **Q&A** (1 min): Answer questions about AI limitations

### Backup Plan
If Copilot unavailable:
- [ ] Pre-record Copilot review and play video
- [ ] Or show Semgrep findings as alternative (same issues)
- [ ] Manually point out issues and explain fixes

---

## Demo 5: AIOps em Ação (20 minutes)

### Pre-Demo Checklist
- [ ] todos-demo pod running healthily (`kubectl get pods -n default`)
- [ ] Prometheus accessible (`kubectl port-forward svc/prometheus-server 9090:80 -n monitor`)
- [ ] correlate_and_remediate.py installed and tested
- [ ] Know what happens during incident: pod delete → detection → analysis → remediation
- [ ] Understand 3 remediation types: restart, scale, HPA
- [ ] Have backup video of metrics spike (if needed)

### During Demo Steps
- [ ] **Step 1** (2 min): Explain AIOps concept and value (reduce MTTR)
- [ ] **Step 2** (2 min): Show initial pod health (`kubectl get pods -n default`)
- [ ] **Step 3** (2 min): Trigger incident
  - [ ] Run `./simulate_incident.sh default todos-demo`
  - [ ] Watch pod get deleted in terminal 2
- [ ] **Step 4** (1 min): Pod automatically restarts (Kubernetes self-healing)
- [ ] **Step 5** (3 min): Run AIOps analysis
  - [ ] `python correlate_and_remediate.py --namespace default --pod-label todos-demo --verbose`
  - [ ] Show full incident report with root cause analysis
  - [ ] Point out confidence score
  - [ ] Point out recommended actions
- [ ] **Step 6** (2 min): Execute auto-remediation
  - [ ] Option A: `--auto-scale` enables HPA
  - [ ] Show HPA created: `kubectl get hpa`
  - [ ] Explain how HPA prevents future incidents
- [ ] **Step 7** (2 min): Show metrics improvement
  - [ ] Pod now healthy with HPA protecting it
  - [ ] Discuss how this reduces manual SRE work
- [ ] **Step 8** (2 min): Explain production deployment
  - [ ] Integrate with alert webhooks
  - [ ] Multi-cluster management
  - [ ] Escalation to humans for critical issues
- [ ] **Q&A** (1 min): Discuss ML/AI enhancements

### Backup Plan
If pod won't delete or metrics unavailable:
- [ ] Use pre-recorded video of incident happening
- [ ] Or manually simulate with stress testing (memory/CPU)
- [ ] Or show static incident report screenshot

---

## ✅ Post-Demo Checklist

After each demo:
- [ ] Clean up running processes (stop servers, port-forwards)
- [ ] Reset cluster to clean state (delete created resources)
- [ ] Save any important outputs/logs for documentation
- [ ] Note what went well and what to improve
- [ ] Thank audience for attention
- [ ] Collect feedback (verbal or written)

---

## ✅ Handling Common Live Demo Issues

### Pod crashes during demo
```bash
# Quickly restart
kubectl rollout restart deployment/todos-demo -n default

# Check if it comes back up
kubectl get pods -n default -w
```

### Port-forward dies
```bash
# Restart it
kubectl port-forward svc/prometheus-server 9090:80 -n monitor
```

### Network connectivity issues
- [ ] Switch to pre-recorded video of that segment
- [ ] Skip to next demo while troubleshooting
- [ ] Offer to show recording afterwards

### Git/GitHub unavailable
- [ ] Use offline Docker image for devSecOps demo
- [ ] Show pre-downloaded code examples
- [ ] Explain the flow conceptually

### Time running out
- [ ] Skip detailed Q&A, offer to follow up
- [ ] Skip Demo 4 if time critical (least infrastructure-dependent)
- [ ] Focus on Demos 2 & 5 (most impressive visually)

---

## 🎤 Presentation Tips

### Pacing
- **Slow down** when showing live commands (let audience read)
- **Narrate** what you're doing before/after each command
- **Pause** for questions between demos
- **Use visual aids** (slides) to explain concepts before showing live demo

### Audience Engagement
- Start with **problem statement**: Why do we need this?
- Show **real-world impact**: Before/after metrics
- Invite **participation**: Ask "what would you do?" questions
- Keep **demos short**: 15 min per demo, 5 min for setup/transitions

### Technical Credibility
- Know your material deeply (practice 2-3 times)
- Admit what you don't know (builds trust)
- Have backup plans ready (but don't mention them)
- Handle errors gracefully (debugging is normal in live demos)

### Visual Clarity
- [ ] Font size 14pt+ (visible from back of room)
- [ ] Color contrast good on projector
- [ ] No unnecessary terminal noise (clear screen before demo)
- [ ] Use `clear`, `history -c` before starting
- [ ] Set minimal window size to fit projector

---

## 📊 Demo Time Breakdown (Total: ~85 minutes)

```
 0:00 - 5:00  | Welcome + Architecture Overview          (5 min)
 5:00 - 20:00 | Demo 1: OpenAPI + SDD                    (15 min)
20:00 - 25:00 | Transition + questions                   (5 min)
25:00 - 40:00 | Demo 2: GitOps + ArgoCD                  (15 min)
40:00 - 45:00 | Transition + questions                   (5 min)
45:00 - 65:00 | Demo 3: DevSecOps + Scanning             (20 min)
65:00 - 70:00 | Break                                    (5 min)
70:00 - 85:00 | Demo 4: AI Code Review                   (15 min)
85:00 - 100:00| Demo 5: AIOps + Auto-remediation         (20 min)
100:00-115:00 | Final Q&A + Wrap-up                      (15 min)
```

---

## 📝 Recording Checklist (if recording demos)

- [ ] Recording software installed and tested (OBS, ScreenFlow, etc.)
- [ ] Microphone working and volume levels good
- [ ] Screen resolution set for recording (1920x1080 minimum)
- [ ] External camera optional but recommended
- [ ] Backup power supply for all equipment
- [ ] Stable internet for streaming (if live)
- [ ] Chat/Q&A monitored if interactive

---

**Last Updated**: June 2026  
**Maintained By**: Demo Team
