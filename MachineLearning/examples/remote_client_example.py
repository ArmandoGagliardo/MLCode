"""
Example: Using Remote ML Client
================================

Esempi di come usare il client ML dal tuo PC locale
per comunicare con il server su istanza Brev/Nvidia.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from presentation.api.client import MLClient


def example_1_health_check():
    """Esempio 1: Controllare health del server remoto"""
    print("=" * 70)
    print("ESEMPIO 1: Health Check")
    print("=" * 70)

    # Connetti al server (sostituisci con URL della tua istanza Brev)
    client = MLClient("http://localhost:8000")
    # Per Brev: client = MLClient("http://your-brev-instance.com:8000")

    # Check health
    health = client.health_check()

    print(f"\nServer Status: {health['status']}")
    print(f"GPU Available: {health['gpu_available']}")
    if health['gpu_available']:
        print(f"GPU Name: {health['gpu_name']}")
        print(f"CUDA Version: {health['cuda_version']}")
        print(f"Memory Allocated: {health['memory_allocated_gb']} GB")


def example_2_code_generation():
    """Esempio 2: Generare codice"""
    print("\n" + "=" * 70)
    print("ESEMPIO 2: Code Generation")
    print("=" * 70)

    client = MLClient("http://localhost:8000")

    # Genera codice
    prompt = "def calculate_fibonacci(n):"
    print(f"\nPrompt: {prompt}")
    print("\nGenerating...")

    result = client.generate_code(
        prompt=prompt,
        max_length=150,
        temperature=0.7,
        num_sequences=2  # Genera 2 varianti
    )

    print(f"\nInference time: {result.inference_time_ms:.0f}ms")
    print(f"Device: {result.device}")

    for i, code in enumerate(result.generated_code, 1):
        print(f"\nVariant {i}:")
        print(code)


def example_3_security_classification():
    """Esempio 3: Classificare codice per sicurezza"""
    print("\n" + "=" * 70)
    print("ESEMPIO 3: Security Classification")
    print("=" * 70)

    client = MLClient("http://localhost:8000")

    # Codice potenzialmente pericoloso
    dangerous_code = """
import os
os.system('rm -rf /')
"""

    print(f"Analyzing code:\n{dangerous_code}")

    result = client.classify_code(dangerous_code, task="security")

    print(f"\nLabel: {result.label}")
    print(f"Confidence: {result.confidence:.2%}")
    print(f"Inference time: {result.inference_time_ms:.0f}ms")

    # Safe code
    safe_code = """
def add_numbers(a, b):
    return a + b
"""

    print(f"\n\nAnalyzing code:\n{safe_code}")

    result = client.classify_code(safe_code, task="security")

    print(f"\nLabel: {result.label}")
    print(f"Confidence: {result.confidence:.2%}")


def example_4_remote_training():
    """Esempio 4: Avviare training remoto"""
    print("\n" + "=" * 70)
    print("ESEMPIO 4: Remote Training")
    print("=" * 70)

    client = MLClient("http://localhost:8000")

    # Avvia training (dataset deve esistere sul server)
    print("\nStarting training job...")
    print("Dataset: data/dataset.json (on server)")
    print("Epochs: 5 (demo)")

    job_id = client.start_training(
        dataset_path="data/dataset.json",
        model_name="Salesforce/codet5-small",
        epochs=5,
        batch_size=8
    )

    print(f"\nTraining job started: {job_id}")

    # Monitora progress
    print("\nMonitoring progress...")

    def on_progress(status):
        """Callback per progress update"""
        if status.progress:
            print(f"  Epoch {status.current_epoch}/{status.total_epochs} - "
                  f"Progress: {status.progress:.1f}%")

    # Attendi completamento (blocking)
    # result = client.wait_for_training(job_id, poll_interval=5, callback=on_progress)
    # print(f"\nTraining completed! Status: {result.status}")

    # Oppure check status manualmente
    import time
    for _ in range(5):
        time.sleep(2)
        status = client.get_training_status(job_id)
        print(f"  Status: {status.status}")
        if status.progress:
            print(f"  Progress: {status.progress:.1f}%")
        if status.status in ["completed", "failed"]:
            break


def example_5_list_jobs():
    """Esempio 5: Listare tutti i training jobs"""
    print("\n" + "=" * 70)
    print("ESEMPIO 5: List Training Jobs")
    print("=" * 70)

    client = MLClient("http://localhost:8000")

    jobs = client.list_training_jobs()

    print(f"\nTotal jobs: {len(jobs)}")
    for job in jobs:
        print(f"\n  Job ID: {job['job_id']}")
        print(f"  Status: {job['status']}")
        print(f"  Started: {job.get('started_at', 'N/A')}")


def example_6_batch_inference():
    """Esempio 6: Batch inference"""
    print("\n" + "=" * 70)
    print("ESEMPIO 6: Batch Inference")
    print("=" * 70)

    client = MLClient("http://localhost:8000")

    # Lista di prompts
    prompts = [
        "def sort_list(items):",
        "class Calculator:",
        "def read_file(path):",
    ]

    print(f"Processing {len(prompts)} prompts...\n")

    for i, prompt in enumerate(prompts, 1):
        print(f"[{i}/{len(prompts)}] {prompt}")

        result = client.generate_code(prompt, max_length=80)

        print(f"  → {result.generated_code[0][:60]}...")
        print(f"  Time: {result.inference_time_ms:.0f}ms\n")


def main():
    """Run all examples"""
    import argparse

    parser = argparse.ArgumentParser(description="Remote ML Client Examples")
    parser.add_argument("--example", type=int, choices=range(1, 7),
                       help="Run specific example (1-6), or all if not specified")

    args = parser.parse_args()

    examples = {
        1: example_1_health_check,
        2: example_2_code_generation,
        3: example_3_security_classification,
        4: example_4_remote_training,
        5: example_5_list_jobs,
        6: example_6_batch_inference
    }

    try:
        if args.example:
            # Run specific example
            examples[args.example]()
        else:
            # Run all examples
            for example_func in examples.values():
                example_func()
                print("\n")

    except ConnectionError as e:
        print(f"\n❌ Connection Error: {e}")
        print("\nMake sure the server is running:")
        print("  python -m presentation.api.server")
        return 1

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    print("\n" + "=" * 70)
    print("✓ Examples completed successfully!")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    exit(main())
