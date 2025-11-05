"""Application Use Cases

Use cases represent specific application operations that orchestrate domain objects
and services to fulfill user intent.

Each use case:
- Has a single responsibility (one user intent)
- Uses dependency injection for services
- Returns a result object
- Handles errors gracefully
"""

from application.use_cases.collect_github_data import CollectGitHubDataUseCase
from application.use_cases.train_model import TrainModelUseCase
from application.use_cases.build_dataset import BuildDatasetUseCase

__all__ = [
    'CollectGitHubDataUseCase',
    'TrainModelUseCase',
    'BuildDatasetUseCase',
]
