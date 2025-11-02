"""
DEMO: Estrazione da singolo repository
"""
from github_repo_processor import GitHubRepoProcessor

# Crea il processor
processor = GitHubRepoProcessor(
    cloud_save=False,  # False = salva solo in locale
    batch_size=100     # Numero di funzioni per batch
)

# Processa un repository
repo_url = "https://github.com/psf/requests"
print(f"Processando: {repo_url}")

result = processor.process_repository(repo_url)

# Mostra risultati
print(f"\nRisultati:")
print(f"  Files processati: {result.get('files_processed', 0)}")
print(f"  Funzioni estratte: {result.get('functions_extracted', 0)}")
print(f"  Status: {result.get('status', 'unknown')}")

# I file JSON sono salvati in:
# datasets/local_backup/code_generation/
