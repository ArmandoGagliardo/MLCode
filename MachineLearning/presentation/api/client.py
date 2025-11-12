"""
API Client for Remote ML Server
=================================

Client Python per comunicare con server ML su istanza Brev/Nvidia.
Usa questo dal tuo PC locale per inviare richieste.

Usage:
    from presentation.api.client import MLClient

    # Connect to remote server
    client = MLClient("http://your-brev-instance.com:8000")

    # Generate code
    code = client.generate_code("def calculate_fibonacci(n):")

    # Classify code
    result = client.classify_code("import os; os.system('rm -rf /')")

    # Start training
    job_id = client.start_training("data/dataset.json", epochs=20)

    # Check training status
    status = client.get_training_status(job_id)
"""

import requests
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import json
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class InferenceResult:
    """Result from inference request"""
    generated_code: List[str]
    prompt: str
    inference_time_ms: float
    model_name: str
    device: str


@dataclass
class ClassificationResult:
    """Result from classification request"""
    label: str
    confidence: float
    all_scores: Dict[str, float]
    code: str
    inference_time_ms: float


@dataclass
class TrainingJob:
    """Training job info"""
    job_id: str
    status: str
    progress: Optional[float] = None
    current_epoch: Optional[int] = None
    total_epochs: Optional[int] = None
    loss: Optional[float] = None
    error: Optional[str] = None


class MLClient:
    """Client for ML API"""

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        timeout: int = 300,  # 5 minutes default
        api_key: Optional[str] = None
    ):
        """
        Initialize client

        Args:
            base_url: Base URL of ML server (e.g., "http://your-brev-instance.com:8000")
            timeout: Request timeout in seconds
            api_key: Optional API key for authentication
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.api_key = api_key
        self.session = requests.Session()

        if api_key:
            self.session.headers.update({"Authorization": f"Bearer {api_key}"})

        logger.info(f"ML Client initialized: {self.base_url}")

    def health_check(self) -> Dict[str, Any]:
        """
        Check server health

        Returns:
            Health status including GPU info

        Example:
            >>> client = MLClient("http://brev-instance.com:8000")
            >>> health = client.health_check()
            >>> print(f"GPU: {health['gpu_name']}")
        """
        try:
            response = self.session.get(
                f"{self.base_url}/health",
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            logger.info(f"Server health: {data['status']}")
            if data.get('gpu_available'):
                logger.info(f"GPU: {data.get('gpu_name')}")

            return data

        except requests.exceptions.RequestException as e:
            logger.error(f"Health check failed: {e}")
            raise ConnectionError(f"Cannot connect to ML server at {self.base_url}: {e}")

    def generate_code(
        self,
        prompt: str,
        max_length: int = 100,
        temperature: float = 0.7,
        top_p: float = 0.9,
        num_sequences: int = 1
    ) -> InferenceResult:
        """
        Generate code from prompt

        Args:
            prompt: Code prompt
            max_length: Maximum length of generated code
            temperature: Sampling temperature (higher = more creative)
            top_p: Nucleus sampling parameter
            num_sequences: Number of sequences to generate

        Returns:
            InferenceResult with generated code

        Example:
            >>> code = client.generate_code(
            ...     "def calculate_fibonacci(n):",
            ...     max_length=150
            ... )
            >>> print(code.generated_code[0])
        """
        logger.info(f"Generating code for prompt: {prompt[:50]}...")

        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/inference/generate",
                json={
                    "prompt": prompt,
                    "max_length": max_length,
                    "temperature": temperature,
                    "top_p": top_p,
                    "num_return_sequences": num_sequences
                },
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()

            result = InferenceResult(
                generated_code=data["generated_code"],
                prompt=data["prompt"],
                inference_time_ms=data["inference_time_ms"],
                model_name=data["model_name"],
                device=data["device"]
            )

            logger.info(f"Code generated in {result.inference_time_ms:.0f}ms")
            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"Code generation failed: {e}")
            raise RuntimeError(f"Code generation failed: {e}")

    def classify_code(
        self,
        code: str,
        task: str = "security"
    ) -> ClassificationResult:
        """
        Classify code

        Args:
            code: Code to classify
            task: Classification task (e.g., "security")

        Returns:
            ClassificationResult with label and confidence

        Example:
            >>> result = client.classify_code(
            ...     "import os; os.system('rm -rf /')",
            ...     task="security"
            ... )
            >>> print(f"Label: {result.label}, Confidence: {result.confidence:.2%}")
        """
        logger.info(f"Classifying code: {code[:50]}...")

        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/inference/classify",
                json={
                    "code": code,
                    "task": task
                },
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()

            result = ClassificationResult(
                label=data["label"],
                confidence=data["confidence"],
                all_scores=data["all_scores"],
                code=data["code"],
                inference_time_ms=data["inference_time_ms"]
            )

            logger.info(f"Classification: {result.label} ({result.confidence:.2%})")
            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"Classification failed: {e}")
            raise RuntimeError(f"Classification failed: {e}")

    def start_training(
        self,
        dataset_path: str,
        model_name: str = "Salesforce/codet5-small",
        epochs: int = 10,
        batch_size: int = 8,
        learning_rate: float = 5e-5,
        output_dir: str = "models/trained_model"
    ) -> str:
        """
        Start training job (async)

        Args:
            dataset_path: Path to dataset on server
            model_name: HuggingFace model name
            epochs: Number of training epochs
            batch_size: Batch size
            learning_rate: Learning rate
            output_dir: Output directory on server

        Returns:
            Job ID for tracking

        Example:
            >>> job_id = client.start_training(
            ...     "data/dataset.json",
            ...     epochs=20,
            ...     batch_size=16
            ... )
            >>> print(f"Training started: {job_id}")
        """
        logger.info(f"Starting training job...")
        logger.info(f"  Dataset: {dataset_path}")
        logger.info(f"  Model: {model_name}")
        logger.info(f"  Epochs: {epochs}")

        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/training/start",
                json={
                    "dataset_path": dataset_path,
                    "model_name": model_name,
                    "num_epochs": epochs,
                    "batch_size": batch_size,
                    "learning_rate": learning_rate,
                    "output_dir": output_dir
                },
                timeout=30  # Training starts async, quick response
            )
            response.raise_for_status()
            data = response.json()

            job_id = data["job_id"]
            logger.info(f"Training job started: {job_id}")

            return job_id

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to start training: {e}")
            raise RuntimeError(f"Failed to start training: {e}")

    def get_training_status(self, job_id: str) -> TrainingJob:
        """
        Get training job status

        Args:
            job_id: Job ID from start_training()

        Returns:
            TrainingJob with current status

        Example:
            >>> status = client.get_training_status(job_id)
            >>> print(f"Progress: {status.progress:.1f}%")
        """
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/training/status/{job_id}",
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            return TrainingJob(
                job_id=data["job_id"],
                status=data["status"],
                progress=data.get("progress"),
                current_epoch=data.get("current_epoch"),
                total_epochs=data.get("total_epochs"),
                loss=data.get("loss"),
                error=data.get("error")
            )

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get training status: {e}")
            raise RuntimeError(f"Failed to get training status: {e}")

    def wait_for_training(
        self,
        job_id: str,
        poll_interval: int = 10,
        callback: Optional[callable] = None
    ) -> TrainingJob:
        """
        Wait for training job to complete (blocking)

        Args:
            job_id: Job ID
            poll_interval: Seconds between status checks
            callback: Optional callback function(status) called each poll

        Returns:
            Final TrainingJob status

        Example:
            >>> def on_progress(status):
            ...     print(f"Epoch {status.current_epoch}/{status.total_epochs}")
            ...
            >>> result = client.wait_for_training(job_id, callback=on_progress)
        """
        logger.info(f"Waiting for training job {job_id}...")

        while True:
            status = self.get_training_status(job_id)

            if callback:
                callback(status)

            if status.status == "completed":
                logger.info(f"Training completed!")
                return status
            elif status.status == "failed":
                logger.error(f"Training failed: {status.error}")
                raise RuntimeError(f"Training failed: {status.error}")

            # Still running
            if status.progress:
                logger.info(f"Progress: {status.progress:.1f}% (Epoch {status.current_epoch}/{status.total_epochs})")

            time.sleep(poll_interval)

    def list_training_jobs(self) -> List[Dict[str, Any]]:
        """
        List all training jobs

        Returns:
            List of training job summaries

        Example:
            >>> jobs = client.list_training_jobs()
            >>> for job in jobs:
            ...     print(f"{job['job_id']}: {job['status']}")
        """
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/training/jobs",
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            return data["jobs"]

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to list jobs: {e}")
            raise RuntimeError(f"Failed to list jobs: {e}")


# ============================================================================
# CLI Utility
# ============================================================================

def main():
    """CLI for testing client"""
    import argparse

    parser = argparse.ArgumentParser(description="ML API Client")
    parser.add_argument("--url", default="http://localhost:8000", help="Server URL")
    parser.add_argument("--action", required=True,
                       choices=["health", "generate", "classify", "train", "status"],
                       help="Action to perform")
    parser.add_argument("--prompt", help="Prompt for generation")
    parser.add_argument("--code", help="Code for classification")
    parser.add_argument("--dataset", help="Dataset path for training")
    parser.add_argument("--job-id", help="Job ID for status check")
    parser.add_argument("--epochs", type=int, default=10, help="Training epochs")

    args = parser.parse_args()

    # Initialize client
    client = MLClient(args.url)

    try:
        if args.action == "health":
            health = client.health_check()
            print(json.dumps(health, indent=2))

        elif args.action == "generate":
            if not args.prompt:
                parser.error("--prompt required for generate action")
            result = client.generate_code(args.prompt)
            print("\nGenerated Code:")
            print(result.generated_code[0])
            print(f"\nInference time: {result.inference_time_ms:.0f}ms")

        elif args.action == "classify":
            if not args.code:
                parser.error("--code required for classify action")
            result = client.classify_code(args.code)
            print(f"Label: {result.label}")
            print(f"Confidence: {result.confidence:.2%}")

        elif args.action == "train":
            if not args.dataset:
                parser.error("--dataset required for train action")
            job_id = client.start_training(args.dataset, epochs=args.epochs)
            print(f"Training started: {job_id}")
            print("Check status with: --action status --job-id", job_id)

        elif args.action == "status":
            if not args.job_id:
                parser.error("--job-id required for status action")
            status = client.get_training_status(args.job_id)
            print(f"Status: {status.status}")
            if status.progress:
                print(f"Progress: {status.progress:.1f}%")
            if status.error:
                print(f"Error: {status.error}")

    except Exception as e:
        print(f"Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
