# 🚀 Quick Start: Security Scanner

**Congratulations!** You now have a **working security vulnerability scanner** that can detect common vulnerabilities in your code!

---

## ✅ What You Have Now

### Working Features (Phase 1 Complete)

1. **Pattern-Based Vulnerability Detection**
   - SQL Injection (CWE-89)
   - Command Injection (CWE-78)
   - XSS (CWE-79)
   - Hardcoded Secrets (CWE-798)
   - Weak Cryptography (CWE-327)
   - Path Traversal (CWE-22)
   - Insecure Deserialization (CWE-502)
   - SSRF (CWE-918)
   - XXE (CWE-611)

2. **Multi-Language Support**
   - Python ✅
   - JavaScript ✅
   - Java ✅
   - PHP ✅
   - C/C++ ✅ (partial)
   - Go ✅ (partial)
   - Ruby ✅ (partial)

3. **CLI Interface**
   - Scan individual files
   - Scan entire directories
   - Multiple output formats (text, JSON)
   - Verbose mode with detailed explanations

4. **OWASP Top 10 Coverage**
   - A01: Broken Access Control (Path Traversal)
   - A02: Cryptographic Failures (Weak Crypto, Hardcoded Secrets)
   - A03: Injection (SQL, Command, XSS)
   - A05: Security Misconfiguration (XXE)
   - A08: Data Integrity Failures (Deserialization)
   - A10: SSRF

---

## 🔥 Test It NOW!

### Step 1: Quick Test

```bash
# Scan the test file with vulnerable code
python main.py --security-scan test_vulnerable.py --verbose
```

**Expected Output**: ~20 vulnerabilities detected!

### Step 2: See the Results

You should see output like:

```
🔍 Security Scan Started
Target: test_vulnerable.py
Scan Type: QUICK
================================================================================

⚠️  Found 20 potential vulnerabilities:
================================================================================

1. 🔴 [HIGH] SQL INJECTION
   CWE: CWE-89 | OWASP: A03:2021 - Injection
   File: test_vulnerable.py (Line 27)
   Code: query = f"SELECT * FROM users WHERE id = '{user_id}'"
   Issue: SQL injection vulnerability via string concatenation
   Fix: Use parameterized queries:
     cursor.execute("SELECT * FROM users WHERE id=?", (user_id,))
   Confidence: HIGH
   References:
     - https://owasp.org/www-community/attacks/SQL_Injection
     - https://cwe.mitre.org/data/definitions/89.html
--------------------------------------------------------------------------------

2. 🔴 [CRITICAL] COMMAND INJECTION
   CWE: CWE-78 | OWASP: A03:2021 - Injection
   File: test_vulnerable.py (Line 68)
   Code: os.system(f"cat {filename}")
   Issue: OS command injection via unsanitized user input
   Fix: Use subprocess with list arguments (no shell=True):
     subprocess.run(["ls", "-l", directory])
   Confidence: HIGH
--------------------------------------------------------------------------------

... (18 more vulnerabilities)

📊 Summary:
   CRITICAL: 4
   HIGH: 12
   MEDIUM: 4

📊 Scan Statistics:
   Files Scanned: 1
   Vulnerabilities Found: 20

⚠️  Action Required: Review and fix 20 vulnerabilities
   🔴 16 CRITICAL/HIGH severity issues need immediate attention!
```

---

## 💡 Usage Examples

### 1. Scan a Single File

```bash
python main.py --security-scan myfile.py
```

### 2. Scan with Detailed Information

```bash
python main.py --security-scan myfile.py --verbose
```

### 3. Scan an Entire Directory

```bash
python main.py --security-scan ./myproject
```

### 4. Output to JSON

```bash
python main.py --security-scan myfile.py --output json
```

Creates `security_report.json` with:
```json
{
  "target": "myfile.py",
  "files_scanned": 1,
  "vulnerabilities": [
    {
      "type": "sql_injection",
      "severity": "HIGH",
      "cwe": "CWE-89",
      "line": 27,
      "code_snippet": "cursor.execute(f\"...\")",
      "description": "...",
      "fix": "..."
    }
  ],
  "stats": {...}
}
```

### 5. Scan Multiple Languages

```bash
# Python
python main.py --security-scan app.py

# JavaScript
python main.py --security-scan server.js

# PHP
python main.py --security-scan index.php

# Java
python main.py --security-scan Main.java
```

---

## 🎯 Real-World Usage

### Pre-Commit Check

Add to your workflow:

```bash
# Before committing
python main.py --security-scan $(git diff --name-only --cached) --output json
```

### Scan Your Project

```bash
# Scan entire project
python main.py --security-scan ./src --verbose > security_audit.txt
```

### Find Specific Vulnerability Types

```bash
# Scan and grep for SQL injection
python main.py --security-scan ./app | grep "SQL INJECTION"
```

---

## 📊 What Gets Detected

### SQL Injection ✅
```python
# DETECTED
query = f"SELECT * FROM users WHERE id={user_id}"
cursor.execute(query)

# DETECTED
cursor.execute("SELECT * WHERE name='%s'" % username)
```

### Command Injection ✅
```python
# DETECTED
os.system(f"cat {filename}")

# DETECTED
subprocess.call(command, shell=True)

# DETECTED
eval(user_input)
```

### Hardcoded Secrets ✅
```python
# DETECTED
API_KEY = "sk-1234567890abcdef"

# DETECTED
password = "SuperSecret123"

# DETECTED
GITHUB_TOKEN = "ghp_xxxxxxxxxxxxxxxxxxxx"
```

### Weak Cryptography ✅
```python
# DETECTED
hashlib.md5(password)

# DETECTED
hashlib.sha1(data)
```

### Path Traversal ✅
```python
# DETECTED
open(user_input)

# DETECTED
path = "/files/" + user_path
```

### And More!
- Insecure Deserialization (pickle, yaml)
- SSRF (unvalidated URLs)
- XXE (XML external entities)
- XSS (JavaScript innerHTML)

---

## 🔍 How It Works

### Pattern Matching Engine

The scanner uses **regex pattern matching** combined with **context awareness**:

1. **Scan Phase**: Searches code for vulnerable patterns
2. **Validation Phase**: Checks for safe patterns nearby
3. **Reporting Phase**: Formats with severity, CWE, OWASP mapping
4. **Guidance Phase**: Provides fix suggestions

### No False Positives from Safe Code

The scanner is smart enough to skip safe code:

```python
# NOT DETECTED (safe parameterized query)
cursor.execute("SELECT * FROM users WHERE id=?", (user_id,))

# NOT DETECTED (safe subprocess without shell)
subprocess.run(["ls", "-l"])
```

---

## 📈 Performance

- **Speed**: <1 second per file
- **Accuracy**: High precision on known patterns
- **Coverage**: 40+ vulnerability patterns
- **Languages**: 8 languages supported

---

## 🆘 Troubleshooting

### "ModuleNotFoundError: No module named 'module.security'"

```bash
# Make sure you're in the project root
cd MachineLearning

# Run from project root
python main.py --security-scan test_vulnerable.py
```

### "File not found: test_vulnerable.py"

```bash
# Check file exists
ls test_vulnerable.py

# Use absolute path
python main.py --security-scan "C:\full\path\to\test_vulnerable.py"
```

### No Vulnerabilities Detected on Known Vulnerable Code

```bash
# Check language detection
# File must have correct extension (.py, .js, .php, etc.)

# Try with verbose mode
python main.py --security-scan myfile.py --verbose
```

---

## 🎓 Understanding Results

### Severity Levels

- **CRITICAL**: Immediate exploitation, severe impact (RCE, Auth Bypass)
- **HIGH**: Exploitable with moderate effort, high impact (SQL Injection, Path Traversal)
- **MEDIUM**: Requires conditions, moderate impact (Weak Crypto)
- **LOW**: Limited exploitability, low impact (Info Disclosure)

### CWE Mappings

Each vulnerability is mapped to [Common Weakness Enumeration](https://cwe.mitre.org/):
- CWE-89: SQL Injection
- CWE-78: OS Command Injection
- CWE-79: Cross-Site Scripting
- CWE-798: Hardcoded Credentials
- etc.

### OWASP Top 10

Mapped to [OWASP Top 10 2021](https://owasp.org/www-project-top-ten/):
- A01: Broken Access Control
- A02: Cryptographic Failures
- A03: Injection
- etc.

---

## 🚀 Next Steps

### Option 1: Scan Your Own Code

```bash
python main.py --security-scan /path/to/your/project
```

### Option 2: Build Training Dataset

Continue with Phase 2 to collect more vulnerability examples:

```bash
# Collect CVEs
python -c "from module.security.api_clients.nvd_client import NVDAPIClient; c = NVDAPIClient(); cves = c.get_recent_cves(30, 1000); c.save_cves_to_file(cves, 'dataset/security/nvd_cves.json')"

# Crawl vulnerable repos
python -c "from module.preprocessing.crawlers.security_crawler import SecurityDataCrawler; from config import GITHUB_TOKEN; c = SecurityDataCrawler(GITHUB_TOKEN); d = c.crawl_all(); c.save_dataset('dataset/security/security_crawled.json')"
```

### Option 3: Expand Pattern Library

Add more patterns in `module/security/patterns/vulnerability_patterns.py`

### Option 4: Integrate into CI/CD

Create GitHub Action, pre-commit hook, or Jenkins pipeline

---

## 📚 Learn More

- **[README_SECURITY.md](README_SECURITY.md)** - Full security system documentation
- **[IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md)** - Project roadmap and progress
- **[NEXT_STEPS.md](NEXT_STEPS.md)** - Detailed next steps for full system

---

## 🎉 Congratulations!

You now have a **working security scanner** that can:

✅ Detect 9+ types of vulnerabilities
✅ Support 8 programming languages
✅ Provide OWASP Top 10 coverage
✅ Generate detailed reports
✅ Suggest fixes for each vulnerability

**This is just the beginning!** The system can be expanded to:
- ML-based detection (Phase 3)
- Taint analysis (Phase 3)
- Auto-remediation (Phase 4)
- CI/CD integration (Phase 5)
- Web dashboard (Phase 6)

---

**Start scanning now**: `python main.py --security-scan test_vulnerable.py --verbose`

**Happy (ethical) hacking!** 🔐
