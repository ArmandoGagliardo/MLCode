"""
Security Analysis Module

Advanced security analysis system for detecting vulnerabilities,
explaining exploits, and suggesting remediation.

Supports:
- Pattern-based detection (AST + regex)
- ML-based detection (CodeBERT fine-tuned) - Coming in Phase 3
- Hybrid detection (pattern + ML) - Coming in Phase 4
- OWASP Top 10 coverage
- Multi-language support (Python, JavaScript, Java, PHP, C++, Go, Ruby, Shell)
- Taint analysis - Coming in Phase 3
- Vulnerability explanation - Coming in Phase 4
- Fix suggestions

Current Status:
- ✅ Phase 1: Pattern-based detection (COMPLETE)
- ⏳ Phase 2-4: ML, Hybrid, Advanced features (IN PROGRESS)

Usage:
    from module.security import PatternBasedDetector

    detector = PatternBasedDetector()
    vulnerabilities = detector.scan_file('vulnerable_code.py')
    print(detector.format_report(vulnerabilities, verbose=True))

CLI Usage:
    python main.py --security-scan test_vulnerable.py --verbose
"""

__version__ = "1.0.0-alpha"
__author__ = "Security Analysis Team"

# Currently available components
from .pattern_detector import PatternBasedDetector

# Components coming in future phases
# from .hybrid_detector import HybridSecurityDetector  # Phase 4
# from .ast_analyzer import ASTSecurityAnalyzer  # Phase 2
# from .explainer import VulnerabilityExplainer  # Phase 4
# from .remediation import RemediationEngine  # Phase 4

__all__ = [
    'PatternBasedDetector',
    # Future components will be added here
]
