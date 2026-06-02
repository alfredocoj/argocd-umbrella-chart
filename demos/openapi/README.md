# Demo 1: Specification-Driven Development (SDD) com OpenAPI

Learn how to use OpenAPI specifications to drive API development, testing, and security validation. Build a REST API from a specification, validate implementation against the spec, and run comprehensive test suites with security scanning.

**Duration**: ~15 minutes  
**Difficulty**: Beginner to Intermediate  
**Audience**: Full-stack developers, API developers, QA engineers

---

## 🎯 What You'll Learn

- **Specification-Driven Development (SDD)** — Using specs as the single source of truth
- **OpenAPI 3.0** — Modern API specification format
- **Spec-First Development** — Code generation and validation from specs
- **API Testing** — Automated testing against specifications
- **Security in CI/CD** — Dependency and secret scanning in the pipeline
- **Test Coverage** — Enforcing quality gates (80% coverage minimum)

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────┐
│           Specification-Driven API Development                │
├──────────────────────────────────────────────────────────────┤
│                                                                │
│  1. OpenAPI Spec (Single Source of Truth)                    │
│     ├─ Endpoints: /todos (GET, POST)                         │
│     ├─ /ready (health check)                                 │
│     └─ Schema definitions (Todo, Error)                      │
│                    │                                           │
│                    ▼                                           │
│  2. Implementation (Python Flask)                             │
│     ├─ app.py — API server                                   │
│     ├─ Matches spec exactly                                  │
│     └─ Validates requests/responses                          │
│                    │                                           │
│                    ▼                                           │
│  3. Testing & Validation                                     │
│     ├─ pytest — Unit tests (80% coverage required)          │
│     ├─ openapi-spec-validator — Spec compliance             │
│     └─ jsonschema — Response schema validation               │
│                    │                                           │
│                    ▼                                           │
│  4. Security Scanning (CI/CD Pipeline)                       │
│     ├─ pip-audit — Dependency vulnerabilities               │
│     ├─ detect-secrets — Hardcoded secrets                    │
│     ├─ Semgrep — Static analysis (SAST)                      │
│     └─ Trivy — Container image vulnerabilities               │
│                    │                                           │
│                    ▼                                           │
│  5. Docker Image → Registry                                  │
│     └─ Only if all gates pass                                │
│                                                                │
└──────────────────────────────────────────────────────────────┘
```

---

## ✅ Prerequisites Check

Ensure your environment is ready:

```bash
# Check Python version
python --version        # Should be 3.11+

# Check pip
pip --version

# Verify you can clone and navigate
cd demos/openapi
ls -la                  # See app.py, spec.yaml, requirements.txt, tests/
```

**Expected output:**
```
Python 3.11.x
pip 23.x
app.py
spec.yaml
requirements.txt
requirements-dev.txt
tests/
```

---

## 🚀 Step-by-Step Walkthrough

### Step 1: Set Up Python Environment

Create an isolated Python environment:

```bash
cd demos/openapi/

# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate      # Linux/macOS
# OR
venv\Scripts\activate          # Windows
```

**Expected output:**
```
(venv) $ _
```

You should see `(venv)` in your prompt.

---

### Step 2: Install Dependencies

Install the project dependencies:

```bash
pip install -r requirements.txt -r requirements-dev.txt
```

**Expected output:**
```
Collecting flask==2.0.0
Collecting pytest==7.0.0
Collecting requests==2.28.0
Collecting jsonschema==4.17.0
Collecting openapi-spec-validator==0.3.2
Collecting ruff==0.1.8
Collecting pytest-cov==4.1.0
Collecting detect-secrets==1.4.0
Collecting pip-audit==2.6.1
Successfully installed flask-2.0.0 pytest-7.0.0 requests-2.28.0 ...
```

---

### Step 3: Understand the OpenAPI Specification

Examine the API specification that drives everything:

```bash
cat spec.yaml
```

**Expected output:**
```yaml
openapi: 3.0.3
info:
  title: Todo API
  version: 1.0.0
  description: Simple REST API for managing todos

paths:
  /todos:
    get:
      summary: List all todos
      operationId: listTodos
      responses:
        '200':
          description: Successful response
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/Todo'
    
    post:
      summary: Create a new todo
      operationId: createTodo
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/TodoInput'
      responses:
        '201':
          description: Todo created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Todo'
        '400':
          description: Invalid input
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'

  /ready:
    get:
      summary: Health check endpoint
      operationId: ready
      responses:
        '200':
          description: Server is ready

components:
  schemas:
    Todo:
      type: object
      properties:
        id:
          type: string
        title:
          type: string
        completed:
          type: boolean
      required:
        - id
        - title
        - completed
    
    TodoInput:
      type: object
      properties:
        title:
          type: string
      required:
        - title
    
    Error:
      type: object
      properties:
        error:
          type: string
```

**Key Points:**
- Spec defines 3 endpoints: `GET /todos`, `POST /todos`, `GET /ready`
- Request/response schemas are explicitly defined
- All validation is in the spec, not scattered in code

---

### Step 4: Review the Implementation

See how the Flask app matches the specification:

```bash
cat app.py
```

**Key code sections:**

```python
from flask import Flask, request, jsonify

app = Flask(__name__)
todos = {}
todo_counter = 0

@app.route('/ready', methods=['GET'])
def ready():
    """Health check endpoint"""
    if os.getenv('FAIL_READY'):
        return {'error': 'Not ready'}, 503
    return {'status': 'ok'}, 200

@app.route('/todos', methods=['GET'])
def list_todos():
    """List all todos - matches GET /todos in spec"""
    return jsonify(list(todos.values())), 200

@app.route('/todos', methods=['POST'])
def create_todo():
    """Create a todo - matches POST /todos in spec"""
    data = request.get_json()
    
    # Validate against TodoInput schema
    if not data or 'title' not in data:
        return {'error': 'Missing required field: title'}, 400
    
    global todo_counter
    todo_counter += 1
    
    new_todo = {
        'id': str(todo_counter),
        'title': data['title'],
        'completed': False
    }
    todos[new_todo['id']] = new_todo
    return jsonify(new_todo), 201

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
```

**Implementation matches spec exactly:**
- ✅ GET /todos returns 200 with Todo[] schema
- ✅ POST /todos accepts TodoInput, returns 201 with Todo
- ✅ GET /ready returns 200
- ✅ Error responses match Error schema

---

### Step 5: Run the API Server

Start the Flask development server:

```bash
python app.py
```

**Expected output:**
```
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://0.0.0.0:8080
 * Press CTRL+C to quit
 * Restarting with stat reloader
 * Debugger is active!
```

The server is now listening on http://localhost:8080.

---

### Step 6: Test the API (in another terminal)

Keep the server running and open a new terminal:

```bash
# Activate venv in the new terminal
cd demos/openapi
source venv/bin/activate

# Test health check
curl http://localhost:8080/ready
```

**Expected output:**
```json
{"status": "ok"}
```

---

### Step 7: Test API Endpoints

Create a todo:

```bash
curl -X POST http://localhost:8080/todos \
  -H "Content-Type: application/json" \
  -d '{"title": "Learn OpenAPI"}'
```

**Expected output:**
```json
{
  "id": "1",
  "title": "Learn OpenAPI",
  "completed": false
}
```

List all todos:

```bash
curl http://localhost:8080/todos
```

**Expected output:**
```json
[
  {
    "id": "1",
    "title": "Learn OpenAPI",
    "completed": false
  }
]
```

Test error handling (missing required field):

```bash
curl -X POST http://localhost:8080/todos \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Expected output:**
```json
{
  "error": "Missing required field: title"
}
```

Status code should be 400.

---

### Step 8: Validate API Against Spec

Verify the implementation matches the OpenAPI specification:

```bash
python -m openapi_spec_validator spec.yaml
```

**Expected output:**
```
Spec is valid!
```

This confirms:
- ✅ YAML syntax is correct
- ✅ Schema definitions are valid
- ✅ Path definitions match OpenAPI 3.0.3 standard
- ✅ No conflicts or missing required fields

---

### Step 9: Run Automated Tests

Execute the test suite with coverage reporting:

```bash
pytest tests/test_api.py -v --cov=app --cov-report=term-missing
```

**Expected output:**
```
tests/test_api.py::test_list_todos_empty PASSED
tests/test_api.py::test_create_todo PASSED
tests/test_api.py::test_list_todos_after_create PASSED
tests/test_api.py::test_create_todo_missing_title PASSED
tests/test_api.py::test_ready_endpoint PASSED
tests/test_api.py::test_ready_endpoint_fail PASSED
tests/test_api.py::test_spec_compliance PASSED
tests/test_api.py::test_response_schema_validation PASSED

===== 8 passed in 0.45s =====

Name              Stmts   Miss  Cover   Missing
-----------------------------------------------
app.py               45      2    95%    25-26
```

**Coverage: 95%** ✅ Exceeds 80% minimum requirement

---

### Step 10: Run Security Scanning

The CI/CD pipeline includes multiple security gates. Let's run them locally:

#### 10a: Code Quality (Ruff)

```bash
ruff format . --check
ruff check .
```

**Expected output:**
```
All checks passed!
```

If there were issues, Ruff would show:
```
app.py:42:5: E501 line too long (>88 characters)
```

---

#### 10b: Dependency Vulnerability Scan (pip-audit)

```bash
pip-audit
```

**Expected output:**
```
No known security vulnerabilities found
```

If vulnerabilities exist, it shows:
```
Found 1 vulnerability in Flask 2.0.0:

  CVE-XXXX-XXXX: Vulnerability description

Run `pip list` to see all your installed packages.
```

---

#### 10c: Secret Detection (detect-secrets)

```bash
detect-secrets scan --all-files --baseline .baseline.json
```

**Expected output:**
```
No secrets detected in 45 lines scanned
```

Example of what it detects:
```python
# This would be flagged:
API_KEY = "sk_live_0123456789abcdef"
PASSWORD = "admin123"
TOKEN = "ghp_1234567890abcdefghijk"
```

---

### Step 11: Build Docker Image

Create a containerized version of the API:

```bash
# Build the image locally
docker build -t api-rest-demo:local .

# Verify the image was created
docker images | grep api-rest-demo
```

**Expected output:**
```
REPOSITORY          TAG       IMAGE ID      CREATED       SIZE
api-rest-demo       local     abc123def456  2 minutes ago  156MB
```

---

### Step 12: Test Container Locally (Optional)

```bash
# Run the container
docker run -p 8081:8080 api-rest-demo:local

# In another terminal, test it
curl http://localhost:8081/ready
```

**Expected output:**
```json
{"status": "ok"}
```

---

## 🎓 Key Concepts Demonstrated

### Specification-Driven Development (SDD)
- **Single source of truth**: The OpenAPI spec defines the contract
- **Code generation**: Tools can auto-generate client libraries and stubs
- **Validation**: APIs are validated against specs at runtime
- **Testing**: Tests are derived from the spec

### Benefits
1. **Clarity** — API contract is crystal clear
2. **Consistency** — Implementation always matches spec
3. **Testability** — All spec-defined paths must be tested
4. **Maintainability** — Spec changes drive code updates
5. **Documentation** — Spec IS the documentation

### Security Layers
| Layer | Tool | Purpose |
|-------|------|---------|
| 1 | pip-audit | Find CVEs in dependencies |
| 2 | detect-secrets | Detect hardcoded secrets |
| 3 | Ruff | Code quality and style |
| 4 | Semgrep | Custom security rules |
| 5 | Trivy | Container image vulnerabilities |

Only passing all layers allows the image to be pushed to registry.

---

## 🧪 Test Coverage Breakdown

```
tests/test_api.py:

1. test_list_todos_empty()
   - Verify GET /todos returns empty array initially

2. test_create_todo()
   - Verify POST /todos creates todo
   - Validate response matches Todo schema

3. test_list_todos_after_create()
   - Verify created todos appear in list

4. test_create_todo_missing_title()
   - Verify error handling for bad requests
   - Validate Error schema

5. test_ready_endpoint()
   - Verify GET /ready returns 200 when healthy

6. test_ready_endpoint_fail()
   - Verify GET /ready returns 503 when FAIL_READY=true
   - Tests rollback scenario

7. test_spec_compliance()
   - Verify spec.yaml is valid OpenAPI 3.0.3

8. test_response_schema_validation()
   - Verify all responses match spec schemas
   - Uses jsonschema library
```

**Coverage target: 80% minimum** ✅ Actual: 95%

---

## 🐛 Common Issues & Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `ModuleNotFoundError: No module named 'flask'` | Dependencies not installed | Run `pip install -r requirements.txt -r requirements-dev.txt` |
| `Port 8080 already in use` | Another process using port | Run `lsof -i :8080` to find process, kill with `kill -9 <PID>` |
| Tests fail with `ConnectionRefusedError` | API server not running | Start server: `python app.py` in another terminal |
| `Spec is invalid!` error from openapi-spec-validator | YAML syntax error in spec.yaml | Check YAML indentation and syntax |
| pytest shows `ModuleNotFoundError: No module named 'app'` | Running pytest from wrong directory | Ensure you're in `demos/openapi/` directory |
| `pip-audit` finds vulnerabilities | Outdated dependencies | Update with `pip install --upgrade <package>` |
| `detect-secrets` finds false positives | Legitimate strings flagged as secrets | Add exemptions in `.detectsecretsrc` |

---

## 🔍 Deep Dive: Understanding the Test File

Let's examine the complete test suite:

```bash
cat tests/test_api.py
```

**Key testing patterns:**

```python
import pytest
from app import app
from jsonschema import validate
import json

@pytest.fixture
def client():
    """Fixture providing Flask test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_list_todos_empty(client):
    """Test GET /todos when empty"""
    response = client.get('/todos')
    assert response.status_code == 200
    assert response.json == []

def test_create_todo(client):
    """Test POST /todos"""
    response = client.post('/todos',
        json={'title': 'Test Todo'},
        content_type='application/json'
    )
    assert response.status_code == 201
    
    data = response.json
    # Validate against Todo schema
    validate(instance=data, schema={
        'type': 'object',
        'properties': {
            'id': {'type': 'string'},
            'title': {'type': 'string'},
            'completed': {'type': 'boolean'}
        },
        'required': ['id', 'title', 'completed']
    })

def test_spec_compliance():
    """Verify OpenAPI spec is valid"""
    from openapi_spec_validator import validate_spec
    with open('spec.yaml') as f:
        spec = yaml.safe_load(f)
    validate_spec(spec)  # Raises exception if invalid
```

**Testing best practices shown:**
1. ✅ Fixtures for setup/teardown
2. ✅ Testing both success (201) and error (400) paths
3. ✅ Schema validation using jsonschema
4. ✅ Spec compliance validation
5. ✅ Clear test names and docstrings

---

## 🚀 Next Steps

### Extend the API
1. Add new endpoints (DELETE /todos/{id}, PUT /todos/{id})
2. Update spec.yaml with new schemas
3. Add database persistence (SQLite or PostgreSQL)
4. Add authentication (API keys, JWT)

### Improve Security
1. Add SQL injection rules to Semgrep
2. Add authentication/authorization checks
3. Add rate limiting
4. Add CORS security headers

### Deploy to Kubernetes
1. Push image to registry: `docker push alfredocoj/api-rest-demo:local`
2. Deploy with: `kubectl apply -f ../k8s/deployment.yaml`
3. Proceed to [Demo 2: GitOps](../gitops/README.md)

### Monitor in Production
1. Integrate with Prometheus for metrics
2. Add structured logging
3. Set up alerts for SLOs

---

## 📚 Additional Resources

- **OpenAPI 3.0 Specification**: https://spec.openapis.org/oas/v3.0.3
- **Swagger/OpenAPI Tools**: https://swagger.io/tools
- **Flask Documentation**: https://flask.palletsprojects.com/
- **pytest Documentation**: https://docs.pytest.org/
- **jsonschema Validator**: https://python-jsonschema.readthedocs.io/

---

## ✨ Key Takeaways

| Takeaway | Application |
|----------|-------------|
| **Spec-first development** | Eliminates ambiguity, enables code generation, ensures consistency |
| **Automated testing** | 80% coverage requirement catches regressions |
| **Security scanning** | Multi-layer approach catches different vulnerability types |
| **Specification validation** | Ensures API implementation matches contract |
| **Schema validation** | Guarantees requests/responses conform to spec |

---

**Time to complete**: ~15 minutes  
**Next demo**: [Demo 2: Deploy K8s com GitOps](../gitops/README.md)
