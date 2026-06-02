# Demo 4: AI Code Review — GitHub Copilot Integration

Enable GitHub Copilot's AI-powered code review to automatically detect security vulnerabilities, performance issues, and code quality problems. See how AI suggestions improve code without manual review overhead.

**Duration**: ~15 minutes  
**Difficulty**: Intermediate  
**Audience**: Developers, Code reviewers, Architecture leads

---

## 🎯 What You'll Learn

- **GitHub Code Review AI Setup** — Configuration and enablement
- **Security Detection** — Automatic identification of SQL injection, hardcoded secrets, OWASP vulnerabilities
- **Performance Issues** — Finding N+1 queries, memory leaks, inefficient patterns
- **Code Quality** — Missing type hints, naming conventions, error handling
- **AI Suggestions** — Auto-generated fix recommendations
- **Review Workflow** — Integrating AI review into development process

---

## 🏗️ Architecture

```
┌────────────────────────────────────────────────────────┐
│ Developer Creates Pull Request (with issues)            │
└────────────────────────────────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│ GitHub Copilot Code Review (AI Analysis)                │
├────────────────────────────────────────────────────────┤
│                                                         │
│ 1. Security Analysis                                   │
│    ├─ SQL Injection patterns                           │
│    ├─ Hardcoded secrets/credentials                    │
│    ├─ Authentication bypasses                          │
│    └─ Unsafe API usage                                 │
│                                                         │
│ 2. Performance Analysis                                │
│    ├─ N+1 query patterns                               │
│    ├─ Memory leaks in loops                            │
│    ├─ Inefficient algorithms                           │
│    └─ Resource exhaustion risks                        │
│                                                         │
│ 3. Code Quality Analysis                               │
│    ├─ Missing type hints (Python 3.9+)                 │
│    ├─ Inconsistent naming conventions                  │
│    ├─ Missing error handling                           │
│    ├─ Unused imports/variables                         │
│    └─ Documentation gaps                               │
│                                                         │
│ 4. Testing Coverage                                    │
│    ├─ Edge cases not tested                            │
│    ├─ Missing null checks                              │
│    └─ Incomplete test scenarios                        │
│                                                         │
└────────────────────────────────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│ AI Reviews Pull Request with Suggestions                │
├────────────────────────────────────────────────────────┤
│                                                         │
│ 📌 Comment on specific lines with:                     │
│    • Issue description                                 │
│    • Risk assessment (CRITICAL/HIGH/MEDIUM/LOW)       │
│    • Code snippet with the problem                     │
│    • Suggested fix (when available)                    │
│    • Link to best practices documentation              │
│                                                         │
└────────────────────────────────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│ Developer Reviews AI Comments                           │
├────────────────────────────────────────────────────────┤
│                                                         │
│ Option A: Accept AI suggestion                         │
│          ↓ Apply fix via "Commit Suggestion"           │
│          ↓ AI suggestion becomes committed code        │
│                                                         │
│ Option B: Modify AI suggestion                         │
│          ↓ Improve the proposed fix                    │
│          ↓ Commit modified version                     │
│                                                         │
│ Option C: Dismiss AI suggestion                        │
│          ↓ Add explanation in reply                    │
│          ↓ Document why issue is not a problem         │
│                                                         │
│ Option D: Create related issue                         │
│          ↓ Track fix in backlog                        │
│          ↓ Plan for future sprint                      │
│                                                         │
└────────────────────────────────────────────────────────┘
                           │
                           ▼
        ✅ Code is cleaner and more secure
        📚 Team learns from AI suggestions
        🚀 Faster code review cycle
```

---

## ✅ Prerequisites

### GitHub Account Setup
- GitHub Enterprise or GitHub Pro (required for Copilot)
- Access to a repository you can create PRs in
- Admin/maintainer permissions (to configure)

### Copilot Configuration Steps

#### 1. Enable Copilot in Organization

Visit: **https://github.com/settings/copilot/overview** (for personal) or:
```
GitHub → Settings → Code Security → Code Review AI
```

Expected: "Code Review AI is enabled for this organization"

#### 2. Check Copilot Subscription

Visit: **https://github.com/settings/billing/summary**

Verify:
- ✅ Copilot for Individuals is active (or)
- ✅ Organization has Copilot business license

---

## 🚀 Step-by-Step Walkthrough

### Step 1: Create Example Code with Issues

Create a feature branch with intentional vulnerabilities:

```bash
cd /path/to/argocd-umbrella-chart

# Create a new file with multiple code issues
cat > demos/openapi/payment_handler.py << 'EOF'
"""Payment processing module with intentional issues for AI code review demo."""
import sqlite3
from flask import request

# ❌ ISSUE 1: Hardcoded secret
STRIPE_API_KEY = "sk_live_abc123def456xyz789"

def process_payment(user_id, amount):
    """
    Process payment for a user.
    
    ❌ ISSUE 2: SQL Injection vulnerability
    ❌ ISSUE 3: Missing type hints
    ❌ ISSUE 4: No error handling
    ❌ ISSUE 5: Security vulnerability (hardcoded secret above)
    """
    conn = sqlite3.connect('payments.db')
    cursor = conn.cursor()
    
    # SQL Injection: user input directly in query
    query = f"SELECT balance FROM accounts WHERE user_id = {user_id}"
    cursor.execute(query)
    
    balance = cursor.fetchone()[0]
    
    if balance >= amount:
        # Hardcoded secret vulnerability
        charge_stripe(STRIPE_API_KEY, amount)
        
        # ❌ ISSUE 6: N+1 query pattern (inefficient database access)
        update_query = f"UPDATE accounts SET balance = {balance - amount} WHERE user_id = {user_id}"
        cursor.execute(update_query)
        
        # ❌ ISSUE 7: No logging of financial transactions
        print(f"Charged {amount}")
        
    conn.close()
    return True

def charge_stripe(api_key, amount):
    """
    ❌ ISSUE 8: Missing error handling
    ❌ ISSUE 9: No timeout on network request
    ❌ ISSUE 10: No rate limiting
    """
    import urllib.request
    
    url = f"https://api.stripe.com/v1/charges?key={api_key}&amount={amount}"
    response = urllib.request.urlopen(url)  # Can hang indefinitely
    return response

def validate_payment(data):
    """
    ❌ ISSUE 11: Insufficient validation
    ❌ ISSUE 12: No type hints
    ❌ ISSUE 13: Silent failure
    """
    try:
        amount = data['amount']
        user = data['user']
    except:
        pass  # Silent failure — attacker can bypass validation
    
    return amount, user

class PaymentProcessor:
    """
    ❌ ISSUE 14: No docstring
    ❌ ISSUE 15: No __init__ method
    """
    
    def process(self, user_id, card_number, cvv, amount):
        """
        ❌ ISSUE 16: Sensitive data (card, CVV) in logs and memory
        ❌ ISSUE 17: No encryption of sensitive data
        """
        print(f"Processing payment for {user_id} with card {card_number}")
        
        # Store sensitive data without encryption
        log_transaction(card_number, cvv, amount)
        
        # ❌ ISSUE 18: Hardcoded path
        with open('/tmp/transactions.txt', 'a') as f:
            f.write(f"{user_id},{card_number},{cvv},{amount}\n")

def log_transaction(card, cvv, amount):
    """
    ❌ ISSUE 19: Logging sensitive data
    ❌ ISSUE 20: No structured logging
    """
    print(f"Card: {card}, CVV: {cvv}, Amount: {amount}")

# ❌ ISSUE 21: Unused import at top
import os
EOF

cat demos/openapi/payment_handler.py
```

**Expected output:**
```python
STRIPE_API_KEY = "sk_live_abc123def456xyz789"  # Hardcoded secret
query = f"SELECT ... WHERE user_id = {user_id}"  # SQL injection
process_payment(user_id, amount):  # No type hints, no error handling
...
```

---

### Step 2: Create Feature Branch and Commit Code

```bash
# Create feature branch
git checkout -b feature/payment-processing

# Add the file
git add demos/openapi/payment_handler.py

# Commit
git commit -m "feat: add payment processing module

This module handles Stripe payments for user accounts.
"

# Push to GitHub
git push origin feature/payment-processing
```

---

### Step 3: Create Pull Request on GitHub

1. Visit your GitHub repository
2. Click "New Pull Request"
3. Select:
   - **Base**: `main`
   - **Compare**: `feature/payment-processing`
4. Click "Create Pull Request"
5. Add PR description:

```markdown
## Payment Processing Feature

This PR adds payment processing capabilities to the API.

- Implements Stripe integration
- Processes payments for user accounts
- Stores transaction history

## Changes
- Added `demos/openapi/payment_handler.py`

## Related Issues
- Closes #123

## Testing
- [ ] Unit tests added
- [ ] Manual testing done
- [ ] Load tested with concurrent payments
```

6. Click "Create pull request"

---

### Step 4: Trigger Copilot Code Review

In the PR, look for the **Code Review AI** option:

1. On the PR page, find the "Copilot" or "Code Review" button
2. Click "Ask Copilot to review" or similar
3. Wait 30-60 seconds for AI analysis

**Alternative (if button not visible):**
- Comment: `@copilot review`

---

### Step 5: Review AI Comments on PR

Copilot will post comments on specific lines. Example reviews:

#### Comment 1: Security - Hardcoded Secret
```
🔴 SECURITY: Hardcoded API Key
Location: Line 7

```python
STRIPE_API_KEY = "sk_live_abc123def456xyz789"
```

Risk Level: CRITICAL
Category: Secrets Management

Description:
API keys should never be hardcoded in source code. They will be 
exposed in git history, build logs, and backups.

Suggested Fix:
```python
import os

STRIPE_API_KEY = os.getenv('STRIPE_API_KEY')
if not STRIPE_API_KEY:
    raise ValueError('STRIPE_API_KEY environment variable is required')
```

Learn More:
- GitHub Secrets: https://docs.github.com/en/actions/security-guides/encrypted-secrets
- Environment Variables: https://12factor.net/config
```

#### Comment 2: Security - SQL Injection
```
🔴 SECURITY: SQL Injection Vulnerability
Location: Line 18

```python
query = f"SELECT balance FROM accounts WHERE user_id = {user_id}"
cursor.execute(query)
```

Risk Level: CRITICAL
Category: SQL Injection (CWE-89)

Description:
String interpolation in SQL queries allows attackers to inject SQL code.
Always use parameterized queries.

Suggested Fix:
```python
query = "SELECT balance FROM accounts WHERE user_id = ?"
cursor.execute(query, (user_id,))
```

Why This Matters:
Attackers can modify the WHERE clause: `user_id = 1 OR 1=1` would 
return all users' balances.
```

#### Comment 3: Code Quality - Missing Type Hints
```
🟡 CODE QUALITY: Missing Type Hints
Location: Line 11

```python
def process_payment(user_id, amount):
```

Risk Level: LOW
Category: Python Type Hints

Description:
Python 3.9+ supports type hints. They improve IDE support, catch type 
errors early, and serve as self-documenting code.

Suggested Fix:
```python
def process_payment(user_id: int, amount: float) -> bool:
```

Benefits:
- IDE autocomplete improvements
- Static type checker support (mypy, pyright)
- Self-documenting code
```

#### Comment 4: Performance - N+1 Query Pattern
```
🟡 PERFORMANCE: N+1 Query Pattern
Location: Line 23

```python
cursor.execute(query)
balance = cursor.fetchone()[0]
if balance >= amount:
    update_query = f"UPDATE accounts..."
    cursor.execute(update_query)
```

Risk Level: MEDIUM
Category: Database Query Optimization

Description:
This code makes 2 database round-trips (SELECT then UPDATE) when it could 
be done in 1 query. At scale, this causes latency issues.

Suggested Fix:
```python
# Use a single atomic UPDATE with CASE
query = """
UPDATE accounts 
SET balance = CASE 
    WHEN balance >= ? THEN balance - ?
    ELSE balance
END
WHERE user_id = ? AND balance >= ?
"""
cursor.execute(query, (amount, amount, user_id, amount))
```

Performance Impact:
For 1,000 users processing payments, this saves 1,000 database 
round-trips per second.
```

#### Comment 5: Error Handling
```
🟡 RELIABILITY: Missing Error Handling
Location: Line 45

```python
def validate_payment(data):
    try:
        amount = data['amount']
        user = data['user']
    except:
        pass  # Silent failure
    
    return amount, user
```

Risk Level: HIGH
Category: Error Handling (CWE-390)

Description:
Bare except clause silently swallows all exceptions. This makes debugging 
difficult and allows invalid data to pass validation.

Suggested Fix:
```python
def validate_payment(data: dict) -> tuple[float, str]:
    """Validate payment data."""
    if not isinstance(data, dict):
        raise ValueError("payment data must be a dict")
    
    if 'amount' not in data:
        raise ValueError("amount is required")
    
    if 'user' not in data:
        raise ValueError("user is required")
    
    return float(data['amount']), str(data['user'])
```

Benefits:
- Clear error messages for debugging
- Proper exception handling
- Type hints for clarity
```

---

### Step 6: Accept AI Suggestions

For each AI comment, GitHub provides "Commit suggestion" button:

1. Scroll to AI comment
2. Click "Commit suggestion" button
3. GitHub adds a commit to the PR
4. Reviewer can approve after seeing fixes

**Example workflow:**

```
💬 AI: SQL Injection detected on Line 18
    [Commit suggestion button]
    ↓
Developer clicks "Commit suggestion"
    ↓
✅ Suggestion committed to PR branch
    ↓
Review shows: "Line 18: SQL Injection - FIXED ✅"
    ↓
Developer can now push branch or create more fixes
```

---

### Step 7: Review AI Suggestions Dashboard

GitHub shows summary view of all AI findings:

```
📊 Code Review Summary

🔴 CRITICAL Issues (must fix):
   1. Hardcoded API Key (Line 7)
   2. SQL Injection (Line 18)
   3. Hardcoded Secret (Line 29)

🟡 MEDIUM Issues (should fix):
   1. N+1 Query Pattern (Line 23)
   2. Weak Error Handling (Line 45)

🟢 LOW Issues (nice to have):
   1. Missing Type Hints (Line 11)
   2. Unused Import (Line 1)

Total Issues Found: 7
Issues Fixed: 0
Issues Acknowledged: 0
```

---

### Step 8: Create Issues for Backlog Items

For issues that take longer to fix, create GitHub Issues:

1. On the PR, click "+ Create issue"
2. Title: "Refactor: Remove hardcoded Stripe key"
3. Description: Include AI comment + context
4. Label: `security`, `technical-debt`
5. Priority: High
6. Assign to team member

**Tracking in backlog:**
```
Issue: Remove hardcoded API keys
Status: Backlog
Priority: P0 (Critical)
Effort: 2 points
Description:
Multiple hardcoded API keys found in:
- demos/openapi/payment_handler.py (Line 7)
- demos/openapi/config.py (Line 42)

Suggested approach:
1. Use environment variables
2. Update CI/CD to inject secrets
3. Audit git history for exposed keys
4. Rotate affected keys
```

---

### Step 9: Update Code Based on Feedback

Fix the issues and commit changes:

**Fix 1: Use environment variables for secrets**

```bash
cat > demos/openapi/payment_handler_fixed.py << 'EOF'
"""Fixed payment processing module."""
import os
import sqlite3
from typing import Tuple, Dict, Any
from flask import request


def get_stripe_api_key() -> str:
    """Get Stripe API key from environment."""
    api_key = os.getenv('STRIPE_API_KEY')
    if not api_key:
        raise ValueError('STRIPE_API_KEY environment variable is required')
    return api_key


def process_payment(user_id: int, amount: float) -> bool:
    """
    Process payment for a user.
    
    Args:
        user_id: Numeric user ID
        amount: Payment amount in cents
        
    Returns:
        True if payment successful, False otherwise
        
    Raises:
        ValueError: If user_id or amount invalid
        sqlite3.Error: If database error occurs
    """
    if user_id <= 0 or amount <= 0:
        raise ValueError("user_id and amount must be positive")
    
    conn = sqlite3.connect('payments.db')
    cursor = conn.cursor()
    
    try:
        # ✅ FIXED: Parameterized query (prevents SQL injection)
        query = "SELECT balance FROM accounts WHERE user_id = ?"
        cursor.execute(query, (user_id,))
        
        result = cursor.fetchone()
        if not result:
            raise ValueError(f"User {user_id} not found")
        
        balance = result[0]
        
        if balance >= amount:
            # ✅ FIXED: Get secret from environment
            stripe_key = get_stripe_api_key()
            
            # ✅ FIXED: Atomic operation (prevents N+1 queries)
            update_query = """
                UPDATE accounts 
                SET balance = balance - ? 
                WHERE user_id = ? AND balance >= ?
            """
            cursor.execute(update_query, (amount, user_id, amount))
            conn.commit()
            
            # ✅ FIXED: Secure logging (no sensitive data)
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Payment processed for user {user_id}")
            
            return True
        else:
            raise ValueError(f"Insufficient balance for user {user_id}")
            
    except Exception as e:
        # ✅ FIXED: Proper error handling
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Payment processing failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


def validate_payment(data: Dict[str, Any]) -> Tuple[float, str]:
    """
    Validate payment data.
    
    ✅ FIXED: Type hints and proper error handling
    """
    if not isinstance(data, dict):
        raise TypeError("payment data must be a dictionary")
    
    if 'amount' not in data:
        raise ValueError("'amount' field is required")
    
    if 'user_id' not in data:
        raise ValueError("'user_id' field is required")
    
    try:
        amount = float(data['amount'])
        user_id = int(data['user_id'])
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid payment data: {e}")
    
    return amount, user_id
EOF

# Compare old vs. new
echo "=== BEFORE (Vulnerable) ==="
head -20 demos/openapi/payment_handler.py

echo ""
echo "=== AFTER (Fixed) ==="
head -25 demos/openapi/payment_handler_fixed.py
```

**Key improvements:**
- ✅ Secrets from environment variables
- ✅ Parameterized SQL queries (no injection)
- ✅ Type hints on all functions
- ✅ Proper error handling (no silent failures)
- ✅ Secure logging (no sensitive data)
- ✅ Atomic database operations (no N+1 queries)
- ✅ Input validation with clear errors

---

### Step 10: Commit Fixes and Re-request Review

```bash
# Stage and commit fixes
git add demos/openapi/payment_handler_fixed.py
git commit -m "fix: address AI code review findings

- Use environment variables for API keys
- Use parameterized queries (prevent SQL injection)
- Add type hints to all functions
- Implement proper error handling
- Add structured logging
- Optimize database queries (atomic operations)
"

git push origin feature/payment-processing
```

GitHub PR automatically updates. You can re-request review:

1. Click "Re-request review" button (or similar)
2. Copilot runs new analysis on updated code

**Expected result:**
```
✅ SQL Injection - FIXED
✅ Hardcoded Secret - FIXED  
✅ Missing Type Hints - FIXED
✅ N+1 Query Pattern - FIXED
✅ Error Handling - FIXED

1 Issue Remaining:
⚠️  [MEDIUM] Insufficient logging for audit trail
```

---

## 🎓 Key Concepts

### AI Code Review Benefits

| Benefit | Impact | Example |
|---------|--------|---------|
| **24/7 Availability** | Faster feedback, no waiting for humans | Junior dev gets immediate security feedback |
| **Consistency** | Same standards across team | All SQL queries checked for injection |
| **Knowledge Transfer** | Team learns best practices | New devs see fix suggestions + explanations |
| **Reduced Cognitive Load** | Reviewers focus on architecture | AI handles style, pattern matching |
| **Catches Oversights** | Human eyes miss details | Complex SQL injection patterns detected |

### Common AI Review Categories

```
🔴 CRITICAL (blocks merge)
  • Security vulnerabilities (SQL injection, XSS, auth bypass)
  • Hardcoded secrets (API keys, passwords, tokens)
  • Remote code execution risks

🟡 MEDIUM (should fix)
  • Performance issues (N+1 queries, memory leaks)
  • Error handling gaps
  • Insufficient logging

🟢 LOW (nice to have)
  • Missing type hints
  • Code style improvements
  • Documentation gaps
  • Naming conventions
```

---

## 🐛 Common Issues & Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Copilot review button not showing | Copilot not enabled for org | Enable in GitHub Settings → Code Security → Code Review AI |
| AI review seems to miss obvious issues | Model limitations | Add Semgrep + custom rules for organization-specific patterns |
| Too many false positives | Over-aggressive rules | Configure PR description to indicate context/exceptions |
| Review takes >2 minutes | High load or timeout | Wait longer or try again; some models are slower |
| Suggestions conflict with team standards | Configuration issue | Document standards in CONTRIBUTING.md, mention in PR |

---

## 🚀 Integration with Workflow

### Before Merge Checklist
```
[ ] All tests passing (GitHub Actions)
[ ] Semgrep SAST passed (zero HIGH violations)
[ ] Copilot code review done
[ ] AI suggestions addressed (committed or documented)
[ ] At least 1 human code review approval
[ ] No merge conflicts
[ ] Branch up-to-date with main
```

### Automation Opportunities
```
# In .github/workflows/pr-review.yml
- Automatically request Copilot review on PR creation
- Post AI summary as PR comment
- Fail CI if CRITICAL issues found
- Track AI feedback metrics over time
```

---

## 📊 Tracking Code Review Metrics

Monitor AI review effectiveness:

```
Weekly Code Review Metrics:

Security Issues Found (by AI):
  - SQL Injection: 2
  - Hardcoded Secrets: 1
  - Missing Auth: 0
  
Performance Issues Found:
  - N+1 Queries: 3
  - Memory Leaks: 1
  
Code Quality Issues:
  - Missing Type Hints: 12
  - Unused Imports: 8

Acceptance Rate:
  - Accepted Suggestions: 85%
  - Modified Suggestions: 10%
  - Rejected Suggestions: 5%

Time to Merge:
  - Before AI Review: 4.2 hours avg
  - After AI Review: 2.8 hours avg
  - Improvement: 33% faster
```

---

## 🚀 Next Steps

1. **Enable Copilot** in your organization
2. **Create test PR** with intentional issues
3. **Review AI suggestions** and evaluate
4. **Document team standards** for AI to reference
5. **Integrate with CI/CD** for automated review
6. **Track metrics** to measure effectiveness
7. **Proceed to Demo 5**: [AIOps em Ação](../aiops/README.md)

---

## 📚 Additional Resources

- **GitHub Copilot Docs**: https://docs.github.com/en/copilot
- **Code Review Best Practices**: https://google.github.io/eng-practices/review/
- **OWASP Code Review Guide**: https://owasp.org/www-project-code-review-guide/
- **Python Type Hints**: https://peps.python.org/pep-0484/

---

**Time to complete**: ~15 minutes  
**Next demo**: [Demo 5: AIOps em Ação](../aiops/README.md)
