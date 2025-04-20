import os
import requests
import json
import ast
from pathlib import Path

# ======== CONFIG ========
OUTPUT_DIR = Path("dataset")
OUTPUT_DIR.mkdir(exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / "dataset_github.json"
MAX_FILES_PER_REPO = 20
BRANCH = "main"  # oppure "master"

REPOS = [
    "psf/requests",
    "pallets/flask",
    "tiangolo/fastapi",
    "numpy/numpy",
    "pandas-dev/pandas",
    "scikit-learn/scikit-learn",
    "encode/httpx",
    "matplotlib/matplotlib",
    "Textualize/rich",
    "sympy/sympy",
    "openai/openai-python",
    "pyca/cryptography",
    "sqlalchemy/sqlalchemy",
    "python/cpython",
    "huggingface/transformers"
]

GITHUB_API = "https://api.github.com/repos"
HEADERS = {"Accept": "application/vnd.github.v3.raw"}

def save_raw_file(repo, path, content):
    safe_repo = repo.replace("/", "_")
    repo_dir = OUTPUT_DIR / "raw" / safe_repo
    repo_dir.mkdir(parents=True, exist_ok=True)

    file_name = path.replace("/", "_")
    file_path = repo_dir / file_name
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

# ======== FUNZIONI ========
def get_py_files(repo):
    files = []
    url = f"{GITHUB_API}/{repo}/git/trees/{BRANCH}?recursive=1"
    res = requests.get(url)
    if res.status_code != 200:
        print(f"⚠️ Impossibile accedere a {repo}")
        return []
    data = res.json()
    for item in data.get("tree", []):
        path = item["path"].lower()
        if (
            path.endswith(".py") and
            "test" not in path and
            "__init__" not in path and
            "setup" not in path
        ):
            files.append(item["path"])
    return files[:MAX_FILES_PER_REPO]


def download_file(repo, path):
    url = f"https://raw.githubusercontent.com/{repo}/{BRANCH}/{path}"
    res = requests.get(url)
    return res.text if res.status_code == 200 else None


def extract_functions(source_code):
    try:
        tree = ast.parse(source_code)
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                name = node.name
                docstring = ast.get_docstring(node) or ""
                start = node.lineno - 1
                end = getattr(node.body[-1], 'end_lineno', node.body[-1].lineno)
                lines = source_code.splitlines()[start:end]
                code = "\n".join(lines)
                functions.append({
                    "func_name": name,
                    "docstring": docstring.strip(),
                    "code": code.strip(),
                    "code_tokens": code.strip().split(),
                    "language": "python",
                    "original_string": code.strip()
                })
        return functions
    except Exception as e:
        return []


def crawl():
    # Carica dataset esistente (se presente)
    if OUTPUT_FILE.exists():
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            dataset = json.load(f)
    else:
        dataset = {}

    count = len(dataset)

    for repo in REPOS:
        print(f"\n🔎 Scansionando {repo}")
        py_files = get_py_files(repo)
        for path in py_files:
            code = download_file(repo, path)
            if not code:
                continue
            save_raw_file(repo, path, code)
            funcs = extract_functions(code)
            for func in funcs:
                if len(func["docstring"]) > 10 and len(func["code"].splitlines()) > 2:
                    key = f"{repo.replace('/', '_')}_{count}"
                    dataset[key] = func
                    count += 1

    # Salva aggiornato
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=4, ensure_ascii=False)

    print(f"\n✅ Salvato: {len(dataset)} funzioni in {OUTPUT_FILE}")


# ======== AVVIO ========
if __name__ == "__main__":
    crawl()
