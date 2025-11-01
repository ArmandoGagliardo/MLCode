# 🔐 Security & Hacking Analysis System

Advanced security analysis system with capabilities for learning and detecting hacking techniques.

---

## 🎯 System Overview

This system transforms your ML project into a comprehensive security analysis platform capable of:

### Offensive Security (Red Team)
- ✅ Identify exploitable vulnerabilities in code
- ✅ Understand common attack vectors
- ✅ Analyze exploit patterns from CVE database
- ✅ Learn hacking techniques from vulnerable applications

### Defensive Security (Blue Team)
- ✅ Detect vulnerabilities before attackers
- ✅ Apply security hardening best practices
- ✅ Monitor code security posture
- ✅ Automated remediation suggestions

### Educational
- ✅ Detailed explanations of each vulnerability
- ✅ How exploits work (theoretical)
- ✅ How to prevent attacks
- ✅ References to CVE, CWE, OWASP resources

---

## 🏗️ Architecture

### Multi-Stage Detection System

```
┌─────────────────────────────────────────────────────────────┐
│                    INPUT: Source Code                        │
└────────────────────┬────────────────────────────────────────┘
                     │
         ┌───────────┴──────────┐
         │   Language Detection  │
         └───────────┬───────────┘
                     │
    ┌────────────────┴─────────────────┐
    │                                  │
┌───▼────────────────┐    ┌───────────▼───────────┐
│  Pattern Detector  │    │   ML Classifier       │
│  (AST + Regex)     │    │   (CodeBERT)          │
│                    │    │                       │
│  - OWASP Top 10    │    │  - 10 Categories      │
│  - 200+ Rules      │    │  - Multi-label        │
│  - Fast (<1s)      │    │  - Confidence Score   │
└────────┬───────────┘    └───────────┬───────────┘
         │                            │
         └──────────┬─────────────────┘
                    │
         ┌──────────▼──────────┐
         │  Taint Analyzer     │
         │  (Data Flow Track)  │
         └──────────┬──────────┘
                    │
         ┌──────────▼──────────┐
         │  False Positive     │
         │  Reduction          │
         └──────────┬──────────┘
                    │
         ┌──────────▼──────────┐
         │  Vulnerability      │
         │  Explainer          │
         └──────────┬──────────┘
                    │
         ┌──────────▼──────────┐
         │  Remediation        │
         │  Engine             │
         └──────────┬──────────┘
                    │
┌───────────────────▼────────────────────┐
│          Report Generator               │
│  - HTML/PDF/JSON                       │
│  - Risk Scoring                        │
│  - Fix Suggestions                     │
└────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Ensure .env file exists with GitHub token
cp .env.example .env
# Edit .env and add your GitHub token

# Install dependencies
pip install -r requirements.txt
```

### 2. Collect Security Data

```bash
# Fetch recent CVEs from NVD
python -c "from module.security.api_clients.nvd_client import NVDAPIClient; c = NVDAPIClient(); cves = c.get_recent_cves(30, 1000); c.save_cves_to_file(cves, 'dataset/security/nvd_cves.json'); print(f'Collected {len(cves)} CVEs')"

# Crawl vulnerable repositories
python -c "from module.preprocessing.crawlers.security_crawler import SecurityDataCrawler; from config import GITHUB_TOKEN; c = SecurityDataCrawler(GITHUB_TOKEN); d = c.crawl_all(); c.save_dataset('dataset/security/security_crawled.json')"

# Crawl GitHub (includes security repos)
python main.py --crawl_git
```

### 3. Future: Scan Code (After Full Implementation)

```bash
# Scan a single file
python main.py --security-scan vulnerable_code.py

# Scan entire directory
python main.py --security-scan ./myproject --output report.html

# Scan with explanations
python main.py --security-scan code.py --explain --fix
```

---

## 📚 Data Sources

### 1. NVD (National Vulnerability Database)
- **Source**: NIST's official CVE database
- **API**: https://nvd.nist.gov/developers/vulnerabilities
- **Coverage**: 200,000+ CVEs
- **Data**: CVE descriptions, CVSS scores, CWE mappings
- **Client**: `module/security/api_clients/nvd_client.py`

**Get API Key**: https://nvd.nist.gov/developers/request-an-api-key

### 2. Vulnerable Applications

Intentionally vulnerable apps for training:

| Application | Language | Purpose |
|------------|----------|---------|
| OWASP PyGoat | Python | Web vulnerabilities |
| Juice Shop | JavaScript | OWASP Top 10 |
| NodeGoat | Node.js | Node.js specific |
| DVWA | PHP | Classic web vulns |
| Mutillidae | PHP | Training platform |
| WebGoat | Java | Enterprise vulns |
| RailsGoat | Ruby | Rails specific |

### 3. Security Tools

Learning detection patterns from:
- **Bandit**: Python security linter
- **Semgrep**: Multi-language scanner
- **Safety-DB**: Known vulnerabilities

### 4. OWASP Resources
- CheatSheet Series
- ASVS (Application Security Verification Standard)

---

## 🎓 Supported Vulnerabilities

### OWASP Top 10 (2021)

| ID | Category | CWE | Detection |
|----|----------|-----|-----------|
| A01 | Broken Access Control | CWE-862, CWE-285 | ⏳ Phase 2 |
| A02 | Cryptographic Failures | CWE-327, CWE-326 | ⏳ Phase 2 |
| A03 | Injection | CWE-89, CWE-78, CWE-79 | ⏳ Phase 2 |
| A04 | Insecure Design | CWE-209, CWE-256 | ⏳ Phase 3 |
| A05 | Security Misconfiguration | CWE-16, CWE-611 | ⏳ Phase 2 |
| A06 | Vulnerable Components | CWE-1035, CWE-937 | ⏳ Phase 3 |
| A07 | Auth Failures | CWE-287, CWE-384 | ⏳ Phase 2 |
| A08 | Data Integrity Failures | CWE-502, CWE-829 | ⏳ Phase 2 |
| A09 | Logging Failures | CWE-778, CWE-117 | ⏳ Phase 3 |
| A10 | SSRF | CWE-918 | ⏳ Phase 2 |

### Additional Vulnerabilities

- **Remote Code Execution** (CWE-94)
- **Path Traversal** (CWE-22)
- **XXE** (CWE-611)
- **Buffer Overflow** (CWE-120) - C/C++
- **Hardcoded Secrets** (CWE-798)
- **Weak Cryptography** (CWE-327)
- **Deserialization** (CWE-502)

---

## 🔍 Detection Methods

### 1. Pattern-Based Detection (Phase 2)
**Speed**: <1 second per file
**Precision**: 90%+
**Coverage**: Known vulnerabilities

**Techniques**:
- AST (Abstract Syntax Tree) analysis via Tree-sitter
- Regex pattern matching
- Language-specific rules
- Context-aware checks

**Example Patterns**:
```yaml
# SQL Injection
pattern: cursor.execute(... + $USER_INPUT + ...)
severity: HIGH
cwe: CWE-89

# Command Injection
pattern: subprocess.call(..., shell=True)
severity: CRITICAL
cwe: CWE-78
```

### 2. ML-Based Detection (Phase 3)
**Speed**: ~2 seconds per file
**Recall**: 85%+
**Coverage**: Complex patterns, zero-days

**Model**: CodeBERT fine-tuned on 50k+ examples
**Capabilities**:
- Multi-class classification (10 categories)
- Multi-label (multiple vulns per code)
- Confidence scoring
- Learns from new patterns

### 3. Taint Analysis (Phase 3)
**Purpose**: Track data flow from sources to sinks

**Example**:
```python
# SOURCE: User input
username = request.args.get('user')

# PROPAGATION
query = f"SELECT * FROM users WHERE name='{username}'"

# SINK: Dangerous function (no sanitization)
cursor.execute(query)  # ⚠️ VULNERABLE!
```

### 4. Hybrid Approach (Phase 4)
Combines all methods for best results:
1. Fast pattern screening
2. ML classification for coverage
3. Taint analysis for verification
4. False positive reduction

---

## 📊 Implementation Status

### ✅ Phase 1: Data Collection (80% Complete)
- ✅ NVD API client
- ✅ Security crawler
- ✅ GitHub crawler enhancement
- ⏳ Dataset manager (pending)

### ⏳ Phase 2: Pattern Detection (0% Complete)
- ❌ Vulnerability patterns library
- ❌ AST analyzers
- ❌ Security rules
- ❌ Pattern detector engine

### ⏳ Phase 3: ML Detection (0% Complete)
- ❌ Enhanced security classifier
- ❌ Security trainer
- ❌ Taint analyzer

### ⏳ Phase 4-7: Integration (0% Complete)
- ❌ Hybrid detector
- ❌ Explainer & remediation
- ❌ CLI & dashboard
- ❌ Reports

**Full details**: See [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md)

---

## 🎯 Use Cases

### 1. Pre-Commit Security Check
```bash
# Check before committing
python main.py --security-scan $(git diff --name-only --cached)
```

### 2. CI/CD Integration (Future)
```yaml
# GitHub Action
- name: Security Scan
  run: |
    python main.py --security-scan . --output json
    # Fail if HIGH or CRITICAL vulnerabilities found
```

### 3. Security Audit
```bash
# Full project audit
python main.py --security-scan ./entire-project --scan-type deep --output audit-report.pdf
```

### 4. Learning Platform
```bash
# Scan with explanations
python main.py --security-scan vulnerable.py --explain

# Output includes:
# - What the vulnerability is
# - How it can be exploited
# - How to fix it
# - References (CVE, CWE, OWASP)
```

### 5. Security Training
```bash
# Train on your own codebase
python main.py --train security_classification --dataset custom_dataset.json
```

---

## 🛠️ API Usage

### NVD Client

```python
from module.security.api_clients.nvd_client import NVDAPIClient

# Initialize
client = NVDAPIClient(api_key='your_key')

# Get recent CVEs
cves = client.get_recent_cves(days=30, max_results=1000)

# Search by keyword
sql_cves = client.get_cves(keyword='sql injection', max_results=100)

# Get specific CVE
cve = client.get_cves(cve_id='CVE-2023-12345')

# Save to file
client.save_cves_to_file(cves, 'output.json')
```

### Security Crawler

```python
from module.preprocessing.crawlers.security_crawler import SecurityDataCrawler

# Initialize
crawler = SecurityDataCrawler(github_token='your_token')

# Crawl all configured sources
dataset = crawler.crawl_all()

# Get statistics
stats = crawler.get_statistics()
print(f"Total examples: {stats['total_examples']}")
print(f"By language: {stats['by_language']}")

# Save dataset
crawler.save_dataset('security_data.json')
```

### Future: Hybrid Detector

```python
from module.security import HybridSecurityDetector

# Initialize
detector = HybridSecurityDetector(
    rules_path='module/security/rules/security_rules.yaml',
    model_path='models/security_classification'
)

# Scan code
code = open('myfile.py').read()
vulnerabilities = detector.detect(code, language='python')

# Process results
for vuln in vulnerabilities:
    print(f"{vuln['type']}: {vuln['severity']}")
    print(f"Line {vuln['line']}: {vuln['description']}")
    print(f"Fix: {vuln['fix_suggestion']}")
```

---

## 📖 Learning Resources

### Understanding Vulnerabilities

**SQL Injection (CWE-89)**:
- **What**: Injecting malicious SQL into queries
- **How**: `' OR '1'='1` bypasses authentication
- **Fix**: Use parameterized queries
- **Example**: See `dataset/security/examples/sql_injection.md`

**Command Injection (CWE-78)**:
- **What**: Executing system commands via user input
- **How**: `; rm -rf /` appended to input
- **Fix**: Avoid shell=True, use allowlists
- **Example**: See `dataset/security/examples/command_injection.md`

**XSS (CWE-79)**:
- **What**: Injecting JavaScript into web pages
- **How**: `<script>alert('XSS')</script>`
- **Fix**: Escape output, use CSP
- **Example**: See `dataset/security/examples/xss.md`

[More examples in development]

### External Resources

- **OWASP**: https://owasp.org/www-project-top-ten/
- **CWE**: https://cwe.mitre.org/
- **NVD**: https://nvd.nist.gov/
- **Exploit-DB**: https://www.exploit-db.com/

---

## ⚖️ Ethical Usage

### ✅ Permitted Uses
- Educational purposes
- Security research
- Defensive security (protecting your code)
- Penetration testing (authorized)
- CTF competitions
- Bug bounty programs

### ❌ Prohibited Uses
- Unauthorized access to systems
- Malicious exploitation
- Distribution of exploits for harm
- Automated exploitation tools
- Attacks on infrastructure

### 📜 Responsible Disclosure
If you discover vulnerabilities using this tool:
1. Report privately to affected party
2. Allow time for patch (90 days standard)
3. Do not exploit for personal gain
4. Follow responsible disclosure guidelines

---

## 🤝 Contributing

### Adding New Vulnerability Patterns

1. Add pattern to `module/security/patterns/vulnerability_patterns.py`
2. Add rule to `module/security/rules/security_rules.yaml`
3. Add test cases
4. Update documentation

### Adding New Language Support

1. Ensure Tree-sitter grammar available
2. Create language-specific detector
3. Add vulnerability patterns
4. Test on vulnerable code samples

---

## 📝 Changelog

### v1.0.0-alpha (2025-10-30)
- ✅ Initial security module structure
- ✅ NVD API client implementation
- ✅ Security data crawler
- ✅ GitHub crawler enhancement
- 📋 Dataset manager (in progress)

### Future Releases
- v1.1.0: Pattern-based detection
- v1.2.0: ML-based detection
- v1.3.0: Hybrid system
- v2.0.0: Full CLI & dashboard

---

## 🐛 Known Issues

1. **Dataset Size**: Currently only 5 examples, needs expansion to 50k+
2. **Pattern Detection**: Not yet implemented
3. **ML Model**: Needs training on larger dataset
4. **False Positives**: Reduction logic pending
5. **Performance**: Not yet optimized for large codebases

See [GitHub Issues](https://github.com/yourrepo/issues) for full list.

---

## 📞 Support

- **Documentation**: [README.md](README.md)
- **Implementation Status**: [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md)
- **Security Guide**: This file
- **Issues**: [GitHub Issues](https://github.com/yourrepo/issues)

---

## 🎓 Training Roadmap

### Week 1-2: Data Collection
- Collect 50k+ vulnerability examples
- Balance dataset
- Validate quality

### Week 3-4: Pattern Detection
- Implement OWASP Top 10 patterns
- Create 200+ rules
- Test on vulnerable code

### Week 5-6: ML Training
- Fine-tune CodeBERT
- Validate performance
- Optimize hyperparameters

### Week 7-8: Integration
- Build hybrid detector
- Create CLI interface
- Develop dashboard

### Beyond: Advanced Features
- Taint analysis
- Auto-remediation
- CI/CD integration
- API service

---

**Status**: 🚧 Active Development (Phase 1)
**Progress**: 25% Complete
**Next Milestone**: Dataset Manager
**Target**: Production-ready system in 8-10 weeks

**Last Updated**: 2025-10-30
