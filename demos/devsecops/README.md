# Demo 3: DevSecOps Pipeline — Multi-Layer Security Scanning

Discover how to embed security checks throughout the CI/CD pipeline. Run automated scans for hardcoded secrets, vulnerable dependencies, code vulnerabilities, and container image flaws. See how security gates prevent insecure code from reaching production.

**Duration**: ~20 minutes  
**Difficulty**: Intermediate  
**Audience**: DevOps engineers, Security engineers, Platform engineers

---

## 🎯 What You'll Learn

- **Security in CI/CD** — Automated gates at each stage
- **SAST (Static Application Security Testing)** — Code analysis with Semgrep
- **Dependency Scanning** — Finding CVEs in library dependencies
- **Secret Detection** — Preventing hardcoded credentials in code
- **Container Scanning** — Image vulnerability scanning with Trivy
- **Security Policy Enforcement** — Blocking deployments that fail security checks

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     GitHub Push Event                            │
└─────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│          GitHub Actions Workflow: demo-ci.yml                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐                                               │
│  │ Stage 1      │     - Python setup (3.11)                     │
│  │ Tests Job    │     - Run pytest with 80% coverage            │
│  │              │     - Run pip-audit (dependency vulns)        │
│  │              │     - Run detect-secrets (hardcoded creds)    │
│  │              │     - Run ruff format/lint check              │
│  └──────────────┘                                               │
│         │                                                        │
│         └─────► ✅ All pass? Continue : ❌ FAIL                 │
│                                                                  │
│  ┌──────────────┐                                               │
│  │ Stage 2      │     - Run Semgrep SAST rules                  │
│  │ Semgrep Job  │     - Check: SQL injection, command inject.   │
│  │              │     - Check: hardcoded secrets, RCE patterns  │
│  │              │     - Check: K8s misconfigs                   │
│  └──────────────┘                                               │
│         │                                                        │
│         └─────► ✅ All rules pass? Continue : ❌ FAIL           │
│                                                                  │
│  ┌──────────────┐                                               │
│  │ Stage 3      │     - Build Docker image                      │
│  │ Build & Push │     - Scan with Trivy (CRITICAL/HIGH → fail) │
│  │              │     - Push to Docker Hub                      │
│  │              │     - Upload SARIF to GitHub Security         │
│  └──────────────┘                                               │
│         │                                                        │
│         └─────► ✅ Image safe? Push : ❌ Block push             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                           │
                           ▼
            🔓 Only safe images reach registry
            🔐 Vulnerabilities blocked at build time
```

---

## ✅ Prerequisites

Ensure your environment has:

```bash
# Navigate to project root
cd /path/to/argocd-umbrella-chart

# Verify CI/CD pipeline exists
ls -la .github/workflows/

# Check Semgrep rules
cat .semgrep.yml | head -20

# View the pipeline definition
cat .github/workflows/demo-ci.yml
```

**Expected output:**
```
demo-ci.yml  <- GitHub Actions workflow
.semgrep.yml <- Security rules (16+ rules)
```

---

## 🚀 Step-by-Step Walkthrough

### Step 1: Review the CI/CD Pipeline

Examine the GitHub Actions workflow that enforces all security gates:

```bash
cat .github/workflows/demo-ci.yml
```

**Expected output (simplified 3-stage pipeline):**

```yaml
name: Demo CI/CD Pipeline

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  # ============ STAGE 1: Tests & Security ============
  tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r demos/openapi/requirements.txt
          pip install -r demos/openapi/requirements-dev.txt
      
      - name: Run pytest with coverage
        run: |
          cd demos/openapi
          pytest tests/test_api.py -v --cov=app --cov-fail-under=80
      
      - name: Dependency vulnerability scan (pip-audit)
        run: |
          cd demos/openapi
          pip-audit --desc --skip-editable
      
      - name: Secret detection (detect-secrets)
        run: |
          cd demos/openapi
          detect-secrets scan --all-files --baseline .baseline.json
      
      - name: Code quality (ruff)
        run: |
          cd demos/openapi
          ruff format . --check
          ruff check .

  # ============ STAGE 2: Static Analysis (SAST) ============
  semgrep:
    runs-on: ubuntu-latest
    needs: tests
    steps:
      - uses: actions/checkout@v3
      
      - name: Run Semgrep SAST
        uses: returntocorp/semgrep-action@v1
        with:
          config: .semgrep.yml
          generateSarif: true
      
      - name: Upload SARIF report
        uses: github/codeql-action/upload-sarif@v2
        if: always()
        with:
          sarif_file: semgrep.sarif
          category: 'semgrep'

  # ============ STAGE 3: Build & Container Scan ============
  build:
    runs-on: ubuntu-latest
    needs: semgrep
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Docker
        uses: docker/setup-buildx-action@v2
      
      - name: Build image
        run: |
          cd demos/openapi
          docker build -t ${{ secrets.DOCKERHUB_USERNAME }}/api-rest-demo:latest .
      
      - name: Scan image with Trivy
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: ${{ secrets.DOCKERHUB_USERNAME }}/api-rest-demo:latest
          format: 'sarif'
          output: 'trivy-results.sarif'
          severity: 'CRITICAL,HIGH'
      
      - name: Upload Trivy SARIF
        uses: github/codeql-action/upload-sarif@v2
        if: always()
        with:
          sarif_file: trivy-results.sarif
          category: 'trivy'
      
      - name: Login to Docker Hub
        if: github.event_name == 'push'
        uses: docker/login-action@v2
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}
      
      - name: Push image
        if: github.event_name == 'push'
        run: |
          docker push ${{ secrets.DOCKERHUB_USERNAME }}/api-rest-demo:latest
```

**Key points:**
- 🔗 **Dependencies**: Stage 2 depends on Stage 1, Stage 3 depends on Stage 2
- ❌ **Failure blocks progress**: Any failure prevents next stage
- 📋 **SARIF reports**: Security findings uploaded to GitHub Security tab
- 🚀 **Only successful images pushed**: Bad images never reach registry

---

### Step 2: Review the Semgrep Security Rules

View the comprehensive SAST rule set:

```bash
cat .semgrep.yml
```

**Key security rule categories:**

| Category | Rules | Severity |
|----------|-------|----------|
| **RCE Prevention** | eval(), exec() detection | ERROR |
| **SQL Injection** | String concat in queries, f-strings in SQL | ERROR |
| **Command Injection** | os.system(), shell=True usage | ERROR |
| **Secret Management** | Hardcoded passwords, API keys, DB URLs | ERROR/WARNING |
| **Crypto** | Insecure random for security context | ERROR |
| **K8s Security** | Missing resource limits, readiness probes, privileged containers | WARNING/ERROR |
| **Code Quality** | Empty except blocks, bad patterns | WARNING |

---

### Step 3: Create a Vulnerable Code Example

Let's intentionally create vulnerable code to demonstrate the security gates:

```bash
# Create a vulnerable version of the API
cat > demos/openapi/app_vulnerable.py << 'EOF'
from flask import Flask, request, jsonify
import sqlite3
import os

app = Flask(__name__)

# ❌ VULNERABILITY 1: Hardcoded API key
API_KEY = "sk_live_####"

# ❌ VULNERABILITY 2: SQL injection via string concatenation
@app.route('/user/<user_id>', methods=['GET'])
def get_user(user_id):
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    
    # Vulnerable: Direct string concat in SQL
    query = f"SELECT * FROM users WHERE id = {user_id}"
    cursor.execute(query)  # ← SQL INJECTION vulnerability
    
    return jsonify(cursor.fetchall())

# ❌ VULNERABILITY 3: Command injection
@app.route('/run/<command>', methods=['POST'])
def run_command(command):
    import os
    result = os.system(command)  # ← COMMAND INJECTION vulnerability
    return jsonify({'result': result})

# ❌ VULNERABILITY 4: Using eval() for dynamic execution
@app.route('/eval', methods=['POST'])
def eval_expr():
    expr = request.json.get('expression')
    result = eval(expr)  # ← RCE vulnerability
    return jsonify({'result': result})

# ❌ VULNERABILITY 5: Insecure random for token generation
@app.route('/token', methods=['GET'])
def gen_token():
    import random
    token = ''.join([str(random.random()) for _ in range(32)])  # ← Weak randomness
    return jsonify({'token': token})

if __name__ == '__main__':
    app.run(debug=True)
EOF

cat demos/openapi/app_vulnerable.py
```

**Expected output:**
```python
API_KEY = "sk_live_####"
query = f"SELECT * FROM users WHERE id = {user_id}"
os.system(command)
eval(expr)
random.random()
```

---

### Step 4: Run Semgrep Against Vulnerable Code

Test Semgrep locally without GitHub Actions:

```bash
# Install Semgrep (if not already installed)
pip install semgrep

# Run Semgrep against vulnerable code
cd demos/openapi
semgrep --config ../../.semgrep.yml app_vulnerable.py --json
```

**Expected output:**
```json
{
  "results": [
    {
      "check_id": "hardcoded-api-key",
      "path": "app_vulnerable.py",
      "start": {"line": 7, "col": 11},
      "message": "Hardcoded API key detected — use environment variables or secret management",
      "severity": "ERROR"
    },
    {
      "check_id": "sql-injection-f-string",
      "path": "app_vulnerable.py",
      "start": {"line": 16, "col": 18},
      "message": "SQL with f-strings is vulnerable to injection — use parameterized queries",
      "severity": "ERROR"
    },
    {
      "check_id": "command-injection-os-system",
      "path": "app_vulnerable.py",
      "start": {"line": 25, "col": 16},
      "message": "Use of os.system() is vulnerable to command injection",
      "severity": "ERROR"
    },
    {
      "check_id": "python-eval-detected",
      "path": "app_vulnerable.py",
      "start": {"line": 31, "col": 20},
      "message": "Avoid use of eval() — can lead to remote code execution",
      "severity": "ERROR"
    },
    {
      "check_id": "insecure-random-for-security",
      "path": "app_vulnerable.py",
      "start": {"line": 36, "col": 41},
      "message": "random.random() is not cryptographically secure — use secrets module",
      "severity": "ERROR"
    }
  ],
  "errors": []
}
```

✅ **Semgrep caught 5 vulnerabilities!** Each would block the build.

---

### Step 5: Demonstrate Hardcoded Secret Detection

Create a file with embedded secrets:

```bash
cat > demos/openapi/config_bad.py << 'EOF'
# Database configuration
DATABASE_URL = "postgresql://admin:####@db.prod.aws.com/myapp"
DB_PASS = "####"
API_KEY = "sk_live_####"
SECRET_TOKEN = "ghp_####"

# These would all be detected
STRIPE_KEY = "sk_live_..."
GITHUB_TOKEN = "ghp_..."
PASSWORD = "####"
EOF

# Run detect-secrets
cd demos/openapi
detect-secrets scan config_bad.py --json
```

**Expected output:**
```json
{
  "results": {
    "config_bad.py": [
      {
        "type": "Basic Auth Credentials",
        "line_number": 2,
        "hashed_secret": "...",
        "is_verified": false,
        "is_secret": true
      },
      {
        "type": "Artifactory Credentials",
        "line_number": 4,
        "is_secret": true
      },
      {
        "type": "Private Key",
        "line_number": 7,
        "is_secret": true
      }
    ]
  }
}
```

✅ **detect-secrets found embedded credentials!**

---

### Step 6: Run pip-audit for Dependency Vulnerabilities

Check for vulnerable Python packages:

```bash
cd demos/openapi

# List current dependencies
cat requirements.txt

# Run pip-audit
pip-audit --desc
```

**Example output (if vulnerable versions exist):**
```
Found 2 vulnerabilities in Flask 2.0.0:

  CVE-2023-30861: Werkzeug before 2.2.2 and Flask before 2.2.2 do not properly 
  validate the path prefix in werkzeug.middleware.proxy_fix.ProxyFix, which allows 
  attackers to bypass authentication by spoofing headers.

  Introduced by: Flask [2.0.0]
  Fixed in: Flask [2.2.2]
  Affected versions:
    - Flask [2.0.0]

Found 1 vulnerability in requests 2.28.0:

  CVE-2023-32681: Requests through 2.31.0 allows attackers to cause a regular 
  expression denial of service (ReDoS) via a malformed URL.

  Introduced by: requests [2.28.0]
  Fixed in: requests [2.31.1]
```

✅ **pip-audit found 2 CVEs in dependencies!** Build would be blocked.

---

### Step 7: Scan a Docker Image with Trivy

Scan the API container image for vulnerabilities:

```bash
# First, ensure the image is built
cd demos/openapi
docker build -t api-rest-demo:local .

# Scan with Trivy (if installed)
trivy image api-rest-demo:local --severity HIGH,CRITICAL
```

**Example output:**
```
2024-06-03T10:15:42.567Z    INFO    Vulnerability scanning...
2024-06-03T10:15:45.123Z    WARN    [HIGH] python/flask: CVE-2023-30861 in Flask [2.0.0]
2024-06-03T10:15:45.234Z    WARN    [HIGH] python/requests: CVE-2023-32681 in requests [2.28.0]
2024-06-03T10:15:45.345Z    ERROR   [CRITICAL] libc: CVE-2021-12345 in glibc [2.31-1]

Total: 3 vulnerabilities [CRITICAL:1, HIGH:2]
```

✅ **Trivy identified vulnerabilities in the base image and dependencies!**

---

### Step 8: Review the Pipeline in GitHub

If you've pushed to GitHub, view the security gates:

1. **Navigate to GitHub repo** → Actions tab
2. **Find latest workflow run**
3. **View security findings**:
   - Click "Security" tab → Code scanning alerts
   - Shows SARIF reports from Semgrep and Trivy
   - Lists specific vulnerabilities with line numbers

**What you'd see:**
- ✅ Tests: PASSED (80% coverage)
- ✅ Linting: PASSED (ruff format + check)
- ❌ Semgrep: 5 violations (hardcoded secrets, SQL injection, eval, etc.)
- ❌ pip-audit: 2 CVEs found (Flask, requests)
- ❌ Trivy: 3 vulnerabilities in image (CRITICAL + HIGH)
- 🚫 **Build blocked** — Cannot push image to registry

---

### Step 9: Fix Vulnerabilities One by One

Let's fix the hardcoded secret first:

**BEFORE (vulnerable):**
```python
API_KEY = "sk_live_####"
```

**AFTER (fixed):**
```python
import os

API_KEY = os.getenv('API_KEY', '')
if not API_KEY:
    raise ValueError("API_KEY environment variable required")
```

Fix SQL injection:

**BEFORE (vulnerable):**
```python
query = f"SELECT * FROM users WHERE id = {user_id}"
cursor.execute(query)
```

**AFTER (fixed - parameterized query):**
```python
query = "SELECT * FROM users WHERE id = ?"
cursor.execute(query, (user_id,))
```

Fix command injection:

**BEFORE (vulnerable):**
```python
result = os.system(command)
```

**AFTER (fixed - safe subprocess):**
```python
import subprocess

result = subprocess.run(['echo', command], capture_output=True, check=False)
return jsonify({'result': result.stdout.decode()})
```

Fix eval():

**BEFORE (vulnerable):**
```python
result = eval(expr)
```

**AFTER (fixed - use safer alternative):**
```python
import ast
import operator

# Only allow safe operations
result = ast.literal_eval(expr)  # Only for literals, not expressions
```

Fix insecure random:

**BEFORE (vulnerable):**
```python
import random
token = ''.join([str(random.random()) for _ in range(32)])
```

**AFTER (fixed - cryptographically secure):**
```python
import secrets
token = secrets.token_urlsafe(32)
```

---

### Step 10: Update Dependencies to Fix CVEs

Upgrade vulnerable packages:

```bash
# Check current versions causing issues
pip list | grep -E "Flask|requests"

# Update to patched versions
pip install Flask==2.2.2 requests==2.31.1 --upgrade

# Verify updates
pip-audit  # Should show 0 vulnerabilities now
```

**Expected output:**
```
No known security vulnerabilities found
```

---

### Step 11: Rebuild and Rescan Image

After fixing code and dependencies, rebuild the image:

```bash
# Rebuild
docker build -t api-rest-demo:fixed .

# Scan again
trivy image api-rest-demo:fixed --severity HIGH,CRITICAL
```

**Expected output:**
```
2024-06-03T10:30:15.567Z    INFO    Vulnerability scanning...
Total: 0 vulnerabilities
```

✅ **Image now passes security scan!**

---

### Step 12: Verify All Gates Pass

Run the complete security pipeline locally:

```bash
cd demos/openapi

# 1. Run tests with coverage
pytest tests/test_api.py --cov=app --cov-fail-under=80
# Expected: PASSED, coverage >= 80%

# 2. Code quality
ruff format . --check && ruff check .
# Expected: All checks passed

# 3. Dependency scan
pip-audit --desc
# Expected: No known security vulnerabilities found

# 4. Secret detection
detect-secrets scan --all-files
# Expected: No secrets detected

# 5. SAST scan (with fixed code)
semgrep --config ../../.semgrep.yml . --json
# Expected: 0 findings

# 6. Build and scan image
docker build -t api-rest-demo:secure .
trivy image api-rest-demo:secure --severity HIGH,CRITICAL
# Expected: 0 vulnerabilities
```

✅ **All 6 security gates passed!** Image is safe to push to production.

---

## 🎓 Security Scanning Layers Explained

```
┌─────────────────────────────────────────────────────────┐
│ Layer 1: Unit Testing + Code Coverage (pytest)          │
│ Purpose: Ensure code works as intended                  │
│ Catches: Logic errors, missing edge cases               │
│ Requirement: 80% coverage minimum                       │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│ Layer 2: Code Quality + Linting (ruff)                  │
│ Purpose: Enforce style, catch obvious bugs              │
│ Catches: Unused imports, naming violations, formatting  │
│ Requirement: All checks pass                            │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│ Layer 3: Dependency Scanning (pip-audit)                │
│ Purpose: Find CVEs in third-party libraries             │
│ Catches: Known vulnerabilities in Flask, requests, etc. │
│ Requirement: 0 vulnerabilities                          │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│ Layer 4: Secret Detection (detect-secrets)              │
│ Purpose: Prevent credentials in code                    │
│ Catches: API keys, passwords, tokens in plaintext       │
│ Requirement: 0 secrets detected                         │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│ Layer 5: Static Analysis / SAST (Semgrep)               │
│ Purpose: Find custom security rules violations          │
│ Catches: SQL injection, command injection, RCE, etc.    │
│ Requirement: 0 HIGH/CRITICAL findings                   │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│ Layer 6: Container Scanning (Trivy)                     │
│ Purpose: Find vulns in OS + application layers          │
│ Catches: Vulnerable base image, OS packages             │
│ Requirement: 0 CRITICAL, 0 HIGH (strict)               │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
                    ✅ Safe to Deploy
```

---

## 🐛 Common Issues & Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `Semgrep not found` | Not installed | `pip install semgrep` |
| `detect-secrets: command not found` | Not installed | `pip install detect-secrets` |
| `pip-audit: command not found` | Not installed | `pip install pip-audit` |
| `trivy: command not found` | Not installed | Install from https://github.com/aquasecurity/trivy#installation |
| Semgrep finding false positives | Overly broad rules | Review rule patterns, adjust as needed |
| `Coverage: 70%, Required: 80%` | Insufficient test coverage | Add tests to cover missed lines: `pytest --cov-report=html` |
| `Trivy finds OLD CVEs` | DB not updated | `trivy image --download-db-only`, then retry |
| GitHub Actions secrets undefined | Secrets not configured | Set in GitHub → Settings → Secrets → New repository secret |

---

## 📊 Real-World DevSecOps Strategy

### Development Workflow

```
1. Developer writes code
   ↓
2. Creates pull request
   ↓
3. GitHub Actions triggers:
   • Tests pass? ❌ → PR blocked, cannot merge
   • Tests pass? ✅ → Continue
   ↓
4. Semgrep runs on code:
   • Vulnerabilities found? ❌ → PR blocked
   • Clean? ✅ → Continue
   ↓
5. pip-audit checks dependencies:
   • CVEs found? ❌ → PR blocked
   • Clean? ✅ → Continue
   ↓
6. detect-secrets scans for hardcoded creds:
   • Secrets found? ❌ → PR blocked
   • Clean? ✅ → Continue
   ↓
7. Trivy scans built image:
   • Critical/High vulns? ❌ → Image not pushed
   • Clean? ✅ → Image pushed to registry
   ↓
8. Image now available for deployment via GitOps
```

### Deployment Security

```
• Only images that passed ALL gates can be deployed
• Git as source of truth (GitOps)
• Cluster only runs signed images (optional: image signing)
• Runtime security monitoring (optional: Falco, OPA)
```

---

## 🚀 Next Steps

1. **Integrate with GitHub**: Push changes and watch CI/CD run
2. **Fix Findings**: Practice fixing vulnerabilities
3. **Customize Rules**: Add domain-specific rules to Semgrep
4. **Gradual Enforcement**: Start with warnings, progress to blocking
5. **Metrics**: Track vulnerability trends over time
6. **Proceed to Demo 4**: [AI Code Review](../ai-code-review/README.md)

---

## 📚 Additional Resources

- **Semgrep Rules**: https://semgrep.dev/r
- **Trivy Documentation**: https://aquasecurity.github.io/trivy/
- **OWASP Top 10**: https://owasp.org/www-project-top-ten/
- **pip-audit**: https://github.com/pypa/pip-audit
- **detect-secrets**: https://github.com/Yelp/detect-secrets

---

**Time to complete**: ~20 minutes  
**Next demo**: [Demo 4: AI Code Review](../ai-code-review/README.md)
