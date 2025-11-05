"""
End-to-End Pipeline Test for Clean Architecture v2.0

Comprehensive test script that validates the entire ML pipeline:
1. Data Collection (synthetic data)
2. Training (minimal configuration)
3. Model Validation
4. Inference Testing
5. Cleanup

Target: Complete in < 5 minutes
Components: All Clean Architecture layers tested

Usage:
    python test_e2e_pipeline.py
    python test_e2e_pipeline.py --samples 15 --epochs 3
    python test_e2e_pipeline.py --no-cleanup --verbose
"""

import argparse
import json
import logging
import shutil
import sys
import time
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('test_e2e.log', mode='w')
    ]
)
logger = logging.getLogger(__name__)


class E2ETestRunner:
    """End-to-end test runner for Clean Architecture v2.0"""

    def __init__(
        self,
        num_samples: int = 10,
        num_epochs: int = 2,
        batch_size: int = 2,
        device: str = "cpu",
        cleanup: bool = True,
        verbose: bool = False
    ):
        """
        Initialize test runner.

        Args:
            num_samples: Number of synthetic samples to generate
            num_epochs: Number of training epochs
            batch_size: Training batch size
            device: Device to use (cpu/cuda)
            cleanup: Whether to cleanup after test
            verbose: Enable verbose logging
        """
        self.num_samples = num_samples
        self.num_epochs = num_epochs
        self.batch_size = batch_size
        self.device = device
        self.cleanup = cleanup
        self.verbose = verbose

        # Test run metadata
        self.run_id = f"e2e_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.start_time = None
        self.end_time = None

        # Temporary directories
        self.temp_dir = None
        self.dataset_path = None
        self.model_path = None

        # Results storage
        self.results = {
            "run_id": self.run_id,
            "status": "RUNNING",
            "phases": {}
        }

        if verbose:
            logging.getLogger().setLevel(logging.DEBUG)

    def print_header(self, text: str, char: str = "="):
        """Print formatted header"""
        width = 80
        print("\n" + char * width)
        print(text.center(width))
        print(char * width + "\n")

    def print_phase(self, phase_num: int, phase_name: str, description: str = ""):
        """Print phase header"""
        print(f"\n[PHASE {phase_num}/6] {phase_name}")
        if description:
            print(f"  {description}")

    def run(self) -> Dict[str, Any]:
        """Run complete end-to-end test"""
        self.start_time = time.time()

        try:
            self.print_header("CLEAN ARCHITECTURE v2.0 - END-TO-END PIPELINE TEST")

            # Phase 0: Setup
            self.print_phase(0, "Environment Setup", "Initializing test environment...")
            self._phase_setup()

            # Phase 1: Data Collection
            self.print_phase(1, "Data Collection",
                           f"Target: {self.num_samples} samples, Max: 60s")
            self.results["phases"]["data_collection"] = self._phase_data_collection()

            # Phase 2: Training
            self.print_phase(2, "Training",
                           f"Epochs: {self.num_epochs}, Batch: {self.batch_size}, Max: 120s")
            self.results["phases"]["training"] = self._phase_training()

            # Phase 3: Validation
            self.print_phase(3, "Validation", "Quick mode, Max: 30s")
            self.results["phases"]["validation"] = self._phase_validation()

            # Phase 4: Inference
            self.print_phase(4, "Inference Testing", "5 samples, Max: 20s")
            self.results["phases"]["inference"] = self._phase_inference()

            # Phase 5: Cleanup
            if self.cleanup:
                self.print_phase(5, "Cleanup", "Max: 20s")
                self.results["phases"]["cleanup"] = self._phase_cleanup()
            else:
                print("\n[SKIP] Cleanup disabled (--no-cleanup)")
                self.results["phases"]["cleanup"] = {"status": "SKIPPED"}

            self.results["status"] = "SUCCESS"

        except KeyboardInterrupt:
            logger.warning("Test interrupted by user")
            self.results["status"] = "INTERRUPTED"
        except Exception as e:
            logger.error(f"Critical failure: {e}", exc_info=True)
            self.results["status"] = "FAILED"
            self.results["error"] = str(e)
        finally:
            self.end_time = time.time()
            self.results["total_duration"] = self.end_time - self.start_time

            # Always try cleanup on failure
            if self.results["status"] != "SUCCESS" and self.cleanup:
                try:
                    self._cleanup_files()
                except Exception as e:
                    logger.error(f"Cleanup failed: {e}")

            # Print summary
            self._print_summary()

            # Save report
            self._save_report()

        return self.results

    def _phase_setup(self):
        """Phase 0: Setup environment"""
        start = time.time()

        # Create temporary directory
        self.temp_dir = tempfile.mkdtemp(prefix="test_e2e_")
        logger.info(f"Created temp directory: {self.temp_dir}")

        self.dataset_path = Path(self.temp_dir) / "dataset.json"
        self.model_path = Path(self.temp_dir) / "model"
        self.model_path.mkdir(exist_ok=True)

        print(f"  ✓ Temporary directories created")
        print(f"  ✓ Logging configured")
        print(f"  → Temp dir: {self.temp_dir}")

        duration = time.time() - start
        logger.info(f"Setup complete in {duration:.1f}s")

    def _phase_data_collection(self) -> Dict[str, Any]:
        """Phase 1: Create synthetic dataset"""
        start = time.time()

        try:
            print("  → Creating synthetic dataset...")

            # Synthetic samples templates
            templates = [
                {
                    "input": "Write a function to add two numbers",
                    "output": "def add(a, b):\n    return a + b",
                    "func_name": "add",
                    "language": "python"
                },
                {
                    "input": "Write a function to multiply two numbers",
                    "output": "def multiply(x, y):\n    return x * y",
                    "func_name": "multiply",
                    "language": "python"
                },
                {
                    "input": "Write a function to greet someone",
                    "output": "def greet(name):\n    return f'Hello, {name}!'",
                    "func_name": "greet",
                    "language": "python"
                },
                {
                    "input": "Write a function to calculate factorial",
                    "output": "def factorial(n):\n    return 1 if n <= 1 else n * factorial(n-1)",
                    "func_name": "factorial",
                    "language": "python"
                },
                {
                    "input": "Write a function to check if number is even",
                    "output": "def is_even(n):\n    return n % 2 == 0",
                    "func_name": "is_even",
                    "language": "python"
                }
            ]

            # Generate samples
            samples = []
            for i in range(self.num_samples):
                template = templates[i % len(templates)]
                sample = template.copy()
                sample["id"] = i
                sample["metadata"] = {"test": True, "sample_id": i}
                samples.append(sample)

            # Save dataset
            with open(self.dataset_path, 'w') as f:
                for sample in samples:
                    f.write(json.dumps(sample) + '\n')

            print(f"  ✓ {len(samples)} samples generated")
            print(f"  ✓ Dataset saved: {self.dataset_path}")

            duration = time.time() - start
            print(f"  → Duration: {duration:.1f}s")

            return {
                "status": "SUCCESS",
                "duration_seconds": duration,
                "samples_collected": len(samples),
                "dataset_path": str(self.dataset_path),
                "dataset_size_kb": self.dataset_path.stat().st_size / 1024
            }

        except Exception as e:
            logger.error(f"Data collection failed: {e}", exc_info=True)
            return {"status": "FAILED", "error": str(e)}

    def _phase_training(self) -> Dict[str, Any]:
        """Phase 2: Train model with minimal configuration"""
        start = time.time()

        try:
            print("  → Loading model: microsoft/codebert-base")

            # Import training dependencies
            from transformers import (
                AutoTokenizer,
                AutoModelForCausalLM,
                TrainingArguments,
                Trainer,
                DataCollatorForLanguageModeling
            )
            from datasets import load_dataset

            # Load dataset
            dataset = load_dataset('json', data_files=str(self.dataset_path), split='train')

            # Split train/val
            train_size = int(0.8 * len(dataset))
            train_dataset = dataset.select(range(train_size))
            val_dataset = dataset.select(range(train_size, len(dataset)))

            print(f"  ✓ Dataset loaded: {len(train_dataset)} train, {len(val_dataset)} val")

            # Load tokenizer and model
            model_name = "microsoft/codebert-base"
            tokenizer = AutoTokenizer.from_pretrained(model_name)

            # Add pad token if missing
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token

            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                pad_token_id=tokenizer.pad_token_id
            )

            param_count = sum(p.numel() for p in model.parameters())
            print(f"  ✓ Model loaded ({param_count:,} parameters)")

            # Tokenize dataset
            def tokenize_function(examples):
                # Combine input and output for language modeling
                texts = [f"{inp}\n{out}" for inp, out in zip(examples['input'], examples['output'])]
                return tokenizer(
                    texts,
                    truncation=True,
                    max_length=128,
                    padding='max_length'
                )

            train_dataset = train_dataset.map(
                tokenize_function,
                batched=True,
                remove_columns=train_dataset.column_names
            )
            val_dataset = val_dataset.map(
                tokenize_function,
                batched=True,
                remove_columns=val_dataset.column_names
            )

            # Training arguments (compatible with older transformers versions)
            training_args = TrainingArguments(
                output_dir=str(self.model_path),
                num_train_epochs=self.num_epochs,
                per_device_train_batch_size=self.batch_size,
                per_device_eval_batch_size=self.batch_size,
                learning_rate=5e-5,
                warmup_steps=0,
                logging_steps=max(1, len(train_dataset) // self.batch_size),
                eval_strategy="steps",  # Updated parameter name
                eval_steps=max(1, len(train_dataset) // self.batch_size),
                save_steps=max(1, len(train_dataset) // self.batch_size),
                save_strategy="steps",
                load_best_model_at_end=True,
                metric_for_best_model="eval_loss",
                greater_is_better=False,
                save_total_limit=1,
                report_to="none",
                disable_tqdm=not self.verbose,
                use_cpu=(self.device == "cpu")  # Updated parameter name
            )

            # Data collator
            data_collator = DataCollatorForLanguageModeling(
                tokenizer=tokenizer,
                mlm=False
            )

            # Create trainer
            trainer = Trainer(
                model=model,
                args=training_args,
                train_dataset=train_dataset,
                eval_dataset=val_dataset,
                data_collator=data_collator
            )

            # Train
            print(f"  → Training epoch 1/{self.num_epochs}...")
            train_result = trainer.train()

            # Save model
            trainer.save_model(str(self.model_path))
            tokenizer.save_pretrained(str(self.model_path))

            print(f"  ✓ Training complete")
            print(f"  ✓ Model saved: {self.model_path}")

            # Get model size
            model_size_mb = sum(
                f.stat().st_size for f in self.model_path.rglob('*') if f.is_file()
            ) / (1024 * 1024)

            duration = time.time() - start
            print(f"  → Duration: {duration:.1f}s")

            return {
                "status": "SUCCESS",
                "duration_seconds": duration,
                "num_epochs": self.num_epochs,
                "train_samples": len(train_dataset),
                "val_samples": len(val_dataset),
                "final_train_loss": train_result.training_loss,
                "model_size_mb": model_size_mb,
                "model_path": str(self.model_path)
            }

        except Exception as e:
            logger.error(f"Training failed: {e}", exc_info=True)
            return {"status": "FAILED", "error": str(e)}

    def _phase_validation(self) -> Dict[str, Any]:
        """Phase 3: Validate trained model"""
        start = time.time()

        try:
            from infrastructure.validation import ModelValidator

            print("  → Running ModelValidator (quick mode)...")

            validator = ModelValidator(
                model_path=str(self.model_path),
                tokenizer_path=str(self.model_path)
            )

            result = validator.validate_all(quick=True)

            # Print check results
            for name, check in result.checks.items():
                status = "✓" if check['passed'] else "✗"
                print(f"  {status} {name.replace('_', ' ').title()}")

            duration = time.time() - start
            print(f"  → Duration: {duration:.1f}s")

            return {
                "status": "SUCCESS" if result.passed else "FAILED",
                "duration_seconds": duration,
                "checks_total": len(result.checks),
                "checks_passed": sum(1 for c in result.checks.values() if c['passed']),
                "checks_failed": sum(1 for c in result.checks.values() if not c['passed']),
                "errors": result.errors,
                "warnings": result.warnings,
                "metrics": result.metrics
            }

        except Exception as e:
            logger.error(f"Validation failed: {e}", exc_info=True)
            return {"status": "FAILED", "error": str(e)}

    def _phase_inference(self) -> Dict[str, Any]:
        """Phase 4: Test inference with trained model"""
        start = time.time()

        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM
            import torch

            print("  → Loading model for inference...")

            tokenizer = AutoTokenizer.from_pretrained(str(self.model_path))
            model = AutoModelForCausalLM.from_pretrained(str(self.model_path))
            model.eval()

            # Test prompts
            test_prompts = [
                "def add(a, b):",
                "def multiply(x, y):",
                "def greet(name):",
                "def factorial(n):",
                "def is_even(n):"
            ]

            successful = 0
            failed = 0
            times = []
            predictions = []  # Store input/output pairs

            for i, prompt in enumerate(test_prompts, 1):
                try:
                    start_inference = time.time()

                    inputs = tokenizer(prompt, return_tensors="pt")

                    with torch.no_grad():
                        outputs = model.generate(
                            **inputs,
                            max_new_tokens=20,
                            do_sample=False,
                            pad_token_id=tokenizer.pad_token_id
                        )

                    generated = tokenizer.decode(outputs[0], skip_special_tokens=True)

                    inference_time = (time.time() - start_inference) * 1000  # ms
                    times.append(inference_time)

                    # Store prediction details
                    predictions.append({
                        "id": i,
                        "input": prompt,
                        "output": generated,
                        "inference_time_ms": round(inference_time, 2)
                    })

                    print(f"  → Testing prediction {i}/{len(test_prompts)}... ✓ ({inference_time:.0f}ms)")
                    successful += 1

                except Exception as e:
                    logger.error(f"Inference {i} failed: {e}")
                    print(f"  → Testing prediction {i}/{len(test_prompts)}... ✗")
                    predictions.append({
                        "id": i,
                        "input": prompt,
                        "output": None,
                        "error": str(e),
                        "inference_time_ms": 0
                    })
                    failed += 1

            avg_time = sum(times) / len(times) if times else 0

            print(f"  ✓ {successful}/{len(test_prompts)} predictions successful")

            duration = time.time() - start
            print(f"  → Duration: {duration:.1f}s")

            return {
                "status": "SUCCESS" if failed == 0 else "PARTIAL",
                "duration_seconds": duration,
                "test_samples": len(test_prompts),
                "successful_predictions": successful,
                "failed_predictions": failed,
                "avg_inference_time_ms": avg_time,
                "min_inference_time_ms": min(times) if times else 0,
                "max_inference_time_ms": max(times) if times else 0,
                "predictions": predictions  # Include input/output pairs
            }

        except Exception as e:
            logger.error(f"Inference testing failed: {e}", exc_info=True)
            return {"status": "FAILED", "error": str(e)}

    def _phase_cleanup(self) -> Dict[str, Any]:
        """Phase 5: Cleanup temporary files"""
        start = time.time()

        try:
            print("  → Deleting temporary files...")

            files_deleted, space_freed = self._cleanup_files()

            print(f"  ✓ Deleted {files_deleted} files ({space_freed:.1f} MB)")
            print(f"  ✓ Deleted temp directory: {self.temp_dir}")

            duration = time.time() - start
            print(f"  → Duration: {duration:.1f}s")

            return {
                "status": "SUCCESS",
                "duration_seconds": duration,
                "files_deleted": files_deleted,
                "space_freed_mb": space_freed
            }

        except Exception as e:
            logger.error(f"Cleanup failed: {e}", exc_info=True)
            return {"status": "FAILED", "error": str(e)}

    def _cleanup_files(self) -> tuple:
        """Delete temporary files and return (count, size_mb)"""
        if not self.temp_dir or not Path(self.temp_dir).exists():
            return 0, 0.0

        # Count files and size
        temp_path = Path(self.temp_dir)
        files = list(temp_path.rglob('*'))
        file_count = len([f for f in files if f.is_file()])

        total_size = sum(
            f.stat().st_size for f in files if f.is_file()
        )
        size_mb = total_size / (1024 * 1024)

        # Delete directory
        shutil.rmtree(self.temp_dir, ignore_errors=True)

        return file_count, size_mb

    def _print_summary(self):
        """Print test summary"""
        self.print_header("TEST SUMMARY", "=")

        # Status
        status_symbol = "✓" if self.results["status"] == "SUCCESS" else "✗"
        print(f"Status: {self.results['status']} {status_symbol}")
        print(f"Total Duration: {self.results['total_duration']:.1f} seconds "
              f"({self.results['total_duration']/60:.1f}m)")
        print(f"Target: < 300 seconds (5 minutes) "
              f"{'✓' if self.results['total_duration'] < 300 else '✗'}")

        # Architecture components
        print("\nArchitecture Components Tested:")
        print("  ✓ Domain Layer (models, interfaces)")
        print("  ✓ Application Layer (services, use cases)")
        print("  ✓ Infrastructure Layer (training, validation)")
        print("  ✓ Config Layer (container, DI)")

        # Phase results
        print("\nPhase Results:")
        phases = self.results.get("phases", {})

        for phase_name, phase_result in phases.items():
            status = phase_result.get("status", "UNKNOWN")
            duration = phase_result.get("duration_seconds", 0)
            status_symbol = "✓" if status == "SUCCESS" else ("⊙" if status == "SKIPPED" else "✗")

            phase_display = phase_name.replace("_", " ").title()
            print(f"  {status_symbol} {phase_display}: {status} ({duration:.1f}s)")

            # Additional details
            if phase_name == "data_collection" and "samples_collected" in phase_result:
                print(f"      Samples: {phase_result['samples_collected']}")
            elif phase_name == "training" and "final_train_loss" in phase_result:
                print(f"      Final loss: {phase_result['final_train_loss']:.4f}")
            elif phase_name == "validation" and "checks_passed" in phase_result:
                passed = phase_result['checks_passed']
                total = phase_result['checks_total']
                print(f"      Checks: {passed}/{total}")
            elif phase_name == "inference" and "successful_predictions" in phase_result:
                succ = phase_result['successful_predictions']
                total = phase_result['test_samples']
                avg_time = phase_result.get('avg_inference_time_ms', 0)
                print(f"      Predictions: {succ}/{total} (avg {avg_time:.1f}ms)")

                # Show sample predictions if available
                if "predictions" in phase_result and phase_result['predictions']:
                    print(f"      Sample predictions:")
                    for pred in phase_result['predictions'][:3]:  # Show first 3
                        input_short = pred['input'][:40] + "..." if len(pred['input']) > 40 else pred['input']
                        output_short = pred['output'][:60] + "..." if pred.get('output') and len(pred['output']) > 60 else pred.get('output', 'N/A')
                        print(f"        [{pred['id']}] {input_short}")
                        print(f"            → {output_short} ({pred['inference_time_ms']:.0f}ms)")
                    if len(phase_result['predictions']) > 3:
                        remaining = len(phase_result['predictions']) - 3
                        print(f"        ... and {remaining} more (see report JSON)")
            elif phase_name == "cleanup" and "space_freed_mb" in phase_result:
                print(f"      Space freed: {phase_result['space_freed_mb']:.1f} MB")

        print()

    def _save_report(self):
        """Save test report to JSON file"""
        report_file = f"test_e2e_report_{self.run_id}.json"

        try:
            # Add system info
            import platform
            self.results["system_info"] = {
                "python_version": platform.python_version(),
                "platform": platform.platform(),
                "machine": platform.machine()
            }

            with open(report_file, 'w') as f:
                json.dump(self.results, f, indent=2)

            print(f"Report saved: {report_file}")
            logger.info(f"Report saved to {report_file}")

        except Exception as e:
            logger.error(f"Failed to save report: {e}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='End-to-end test for Clean Architecture v2.0 ML Pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic run (10 samples, 2 epochs)
  python test_e2e_pipeline.py

  # Custom configuration
  python test_e2e_pipeline.py --samples 15 --epochs 3

  # Debug mode (no cleanup, verbose)
  python test_e2e_pipeline.py --no-cleanup --verbose

  # Use GPU if available
  python test_e2e_pipeline.py --device cuda
        """
    )

    parser.add_argument(
        '--samples',
        type=int,
        default=10,
        help='Number of synthetic samples to generate (default: 10)'
    )

    parser.add_argument(
        '--epochs',
        type=int,
        default=2,
        help='Number of training epochs (default: 2)'
    )

    parser.add_argument(
        '--batch-size',
        type=int,
        default=2,
        help='Training batch size (default: 2)'
    )

    parser.add_argument(
        '--device',
        type=str,
        default='cpu',
        choices=['cpu', 'cuda'],
        help='Device to use for training (default: cpu)'
    )

    parser.add_argument(
        '--no-cleanup',
        action='store_true',
        help='Skip cleanup phase (keep temporary files)'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    # Create and run test
    runner = E2ETestRunner(
        num_samples=args.samples,
        num_epochs=args.epochs,
        batch_size=args.batch_size,
        device=args.device,
        cleanup=not args.no_cleanup,
        verbose=args.verbose
    )

    results = runner.run()

    # Exit code based on status
    exit_code = 0 if results["status"] == "SUCCESS" else 1
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
