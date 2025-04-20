import os
import requests
import json
import ast
from pathlib import Path
from .parser_manager import get_parser

# ======== CONFIG ========
OUTPUT_DIR = Path("dataset")
OUTPUT_DIR.mkdir(exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / "dataset_github.json"
MAX_FILES_PER_REPO = 20
BRANCH = "main"  # oppure "master"
EXTENSIONS = {
    "python": ".py",
    "javascript": ".js",
    "java": ".java",
    "shell": ".sh",
}

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
def get_files(repo):
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
            "test" not in path and
            "__init__" not in path and
            "setup" not in path
        ):
            if Path(item["path"]).suffix in EXTENSIONS.values():
                files.append(item["path"])

    return files[:MAX_FILES_PER_REPO]


def download_file(repo, path):
    url = f"https://raw.githubusercontent.com/{repo}/{BRANCH}/{path}"
    res = requests.get(url)
    return res.text if res.status_code == 200 else None


def extract_functions(source_code,extension):
    try:

        parser = get_parser(extension)
        if parser is None:
            print(f"⚠️ Parser non trovato per l'estensione {extension}")
            return []
        
        return parser.parse(source_code)
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
        py_files = get_files(repo)
        for path in py_files:
            extension = Path(path).suffix
            code = download_file(repo, path)
            if not code:
                continue
            save_raw_file(repo, path, code)
            funcs = extract_functions(code,extension)
            for func in funcs:
                 if len(func.get("input", "")) > 10 and len(func.get("output", "")) > 10:
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
