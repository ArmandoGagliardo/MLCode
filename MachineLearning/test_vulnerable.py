"""
Test file with intentionally vulnerable code

This file contains examples of common security vulnerabilities
for testing the security scanner.

⚠️ WARNING: This code contains INTENTIONAL vulnerabilities.
   DO NOT use this code in production!
   FOR EDUCATIONAL PURPOSES ONLY!
"""

import os
import subprocess
import sqlite3
import pickle
import hashlib
import yaml
import requests


# ============================================
# SQL INJECTION VULNERABILITIES (CWE-89)
# ============================================

def get_user_by_id_vulnerable(user_id):
    """
    VULNERABLE: SQL Injection via string concatenation
    Severity: HIGH
    """
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    # VULNERABLE: Direct string concatenation
    query = f"SELECT * FROM users WHERE id = '{user_id}'"
    cursor.execute(query)

    return cursor.fetchone()


def get_user_by_name_vulnerable(username):
    """
    VULNERABLE: SQL Injection via % formatting
    Severity: HIGH
    """
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    # VULNERABLE: Using % formatting
    query = "SELECT * FROM users WHERE username = '%s'" % username
    cursor.execute(query)

    return cursor.fetchone()


def search_users_vulnerable(search_term):
    """
    VULNERABLE: SQL Injection via .format()
    Severity: HIGH
    """
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    # VULNERABLE: Using .format()
    query = "SELECT * FROM users WHERE name LIKE '%{}%'".format(search_term)
    cursor.execute(query)

    return cursor.fetchall()


# ============================================
# COMMAND INJECTION VULNERABILITIES (CWE-78)
# ============================================

def run_command_vulnerable(filename):
    """
    VULNERABLE: Command Injection via os.system()
    Severity: CRITICAL
    """
    # VULNERABLE: Using os.system with user input
    os.system(f"cat {filename}")


def execute_shell_vulnerable(command):
    """
    VULNERABLE: Command Injection via subprocess with shell=True
    Severity: CRITICAL
    """
    # VULNERABLE: subprocess with shell=True
    subprocess.call(command, shell=True)


def compile_code_vulnerable(code):
    """
    VULNERABLE: Code Injection via eval()
    Severity: CRITICAL
    """
    # VULNERABLE: Using eval() on user input
    result = eval(code)
    return result


def execute_dynamic_code(code):
    """
    VULNERABLE: Code Injection via exec()
    Severity: CRITICAL
    """
    # VULNERABLE: Using exec() on user input
    exec(code)


# ============================================
# HARDCODED SECRETS (CWE-798)
# ============================================

# VULNERABLE: Hardcoded API key
API_KEY = "sk-1234567890abcdefghijklmnopqrstuvwxyz"

# VULNERABLE: Hardcoded password
DATABASE_PASSWORD = "SuperSecret123!"

# VULNERABLE: Hardcoded AWS credentials
AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"
AWS_SECRET_ACCESS_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"

# VULNERABLE: Hardcoded GitHub token
GITHUB_TOKEN = "ghp_1234567890abcdefghijklmnopqrstuv"


# ============================================
# WEAK CRYPTOGRAPHY (CWE-327)
# ============================================

def hash_password_vulnerable(password):
    """
    VULNERABLE: Using weak MD5 hash
    Severity: MEDIUM
    """
    # VULNERABLE: MD5 is broken
    return hashlib.md5(password.encode()).hexdigest()


def hash_data_vulnerable(data):
    """
    VULNERABLE: Using weak SHA1 hash
    Severity: MEDIUM
    """
    # VULNERABLE: SHA1 is deprecated
    return hashlib.sha1(data.encode()).hexdigest()


# ============================================
# PATH TRAVERSAL (CWE-22)
# ============================================

def read_file_vulnerable(filename):
    """
    VULNERABLE: Path Traversal via unvalidated filename
    Severity: HIGH
    """
    # VULNERABLE: No path validation
    with open(filename, 'r') as f:
        return f.read()


def serve_file_vulnerable(user_path):
    """
    VULNERABLE: Path Traversal via concatenation
    Severity: HIGH
    """
    # VULNERABLE: Direct concatenation without validation
    full_path = "/var/www/files/" + user_path
    with open(full_path, 'r') as f:
        return f.read()


# ============================================
# INSECURE DESERIALIZATION (CWE-502)
# ============================================

def load_user_data_vulnerable(serialized_data):
    """
    VULNERABLE: Insecure deserialization via pickle
    Severity: CRITICAL
    """
    # VULNERABLE: pickle.loads on untrusted data
    return pickle.loads(serialized_data)


def load_config_vulnerable(yaml_data):
    """
    VULNERABLE: Insecure YAML deserialization
    Severity: CRITICAL
    """
    # VULNERABLE: yaml.load without safe_load
    return yaml.load(yaml_data)


# ============================================
# SSRF (Server-Side Request Forgery) (CWE-918)
# ============================================

def fetch_url_vulnerable(url):
    """
    VULNERABLE: SSRF via unvalidated URL
    Severity: HIGH
    """
    # VULNERABLE: No URL validation
    response = requests.get(url)
    return response.text


def fetch_data_vulnerable(endpoint):
    """
    VULNERABLE: SSRF via string concatenation
    Severity: HIGH
    """
    # VULNERABLE: URL from user input
    url = "https://api.example.com/" + endpoint
    response = requests.get(url)
    return response.json()


# ============================================
# XSS EXAMPLE (for JavaScript - commented)
# ============================================

"""
JavaScript XSS vulnerabilities (for reference):

// VULNERABLE: XSS via innerHTML
function displayUserInput(userInput) {
    document.getElementById('output').innerHTML = userInput;  // VULNERABLE!
}

// VULNERABLE: XSS via document.write
function showMessage(message) {
    document.write("<div>" + message + "</div>");  // VULNERABLE!
}

// VULNERABLE: XSS in React
function DisplayData({userInput}) {
    return <div dangerouslySetInnerHTML={{__html: userInput}} />;  // VULNERABLE!
}
"""


# ============================================
# SAFE ALTERNATIVES (for comparison)
# ============================================

def get_user_by_id_safe(user_id):
    """
    SAFE: Using parameterized query
    """
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    # SAFE: Parameterized query
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))

    return cursor.fetchone()


def run_command_safe(filename):
    """
    SAFE: Using subprocess with list arguments
    """
    # SAFE: subprocess with list (no shell)
    result = subprocess.run(["cat", filename], capture_output=True, check=True)
    return result.stdout


def hash_password_safe(password):
    """
    SAFE: Using strong hash algorithm
    """
    import bcrypt

    # SAFE: Using bcrypt for passwords
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt())


def read_file_safe(filename, base_dir="/var/www/files"):
    """
    SAFE: Path validation and sanitization
    """
    import os.path

    # SAFE: Validate path
    safe_path = os.path.abspath(os.path.join(base_dir, os.path.basename(filename)))

    if not safe_path.startswith(base_dir):
        raise ValueError("Invalid path")

    with open(safe_path, 'r') as f:
        return f.read()


# ============================================
# Main (for testing)
# ============================================

if __name__ == "__main__":
    print("This file contains INTENTIONAL vulnerabilities for testing.")
    print("Run: python main.py --security-scan test_vulnerable.py --verbose")
    print("\nExpected findings:")
    print("  - SQL Injection: 3 instances")
    print("  - Command Injection: 4 instances")
    print("  - Hardcoded Secrets: 5 instances")
    print("  - Weak Cryptography: 2 instances")
    print("  - Path Traversal: 2 instances")
    print("  - Insecure Deserialization: 2 instances")
    print("  - SSRF: 2 instances")
    print("\nTotal: ~20 vulnerabilities")
