"""
Model Validation Framework

Comprehensive validation for trained models:
- Model file integrity checks
- Architecture validation
- Inference testing
- Performance benchmarks
- Output quality assessment
"""

import torch
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import time

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of model validation."""

    model_path: str
    timestamp: str
    passed: bool
    checks: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metrics: Dict[str, float] = field(default_factory=dict)

    def add_check(self, name: str, passed: bool, details: Dict[str, Any]):
        """Add a validation check result."""
        self.checks[name] = {
            'passed': passed,
            'details': details
        }

        if not passed:
            self.passed = False

    def add_error(self, error: str):
        """Add an error message."""
        self.errors.append(error)
        self.passed = False

    def add_warning(self, warning: str):
        """Add a warning message."""
        self.warnings.append(warning)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'model_path': self.model_path,
            'timestamp': self.timestamp,
            'passed': self.passed,
            'checks': self.checks,
            'errors': self.errors,
            'warnings': self.warnings,
            'metrics': self.metrics
        }

    def save(self, output_path: str):
        """Save validation result to JSON file."""
        with open(output_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
        logger.info(f"[SAVE] Validation result saved to {output_path}")


class ModelValidator:
    """Validator for trained models."""

    def __init__(self, model_path: str, tokenizer_path: Optional[str] = None):
        """
        Initialize model validator.

        Args:
            model_path: Path to model directory or file
            tokenizer_path: Path to tokenizer (optional, defaults to model_path)
        """
        self.model_path = Path(model_path)
        self.tokenizer_path = Path(tokenizer_path) if tokenizer_path else self.model_path

        self.result = ValidationResult(
            model_path=str(self.model_path),
            timestamp=datetime.now().isoformat(),
            passed=True
        )

    def validate_all(self, quick: bool = False) -> ValidationResult:
        """
        Run all validation checks.

        Args:
            quick: Skip time-consuming checks

        Returns:
            ValidationResult object
        """
        logger.info(f"[*] Starting model validation: {self.model_path}")

        # Essential checks (always run)
        self.check_files_exist()
        self.check_model_loadable()
        self.check_tokenizer_loadable()

        if not quick:
            # Comprehensive checks
            self.check_model_architecture()
            self.check_inference_works()
            self.benchmark_inference_speed()
            self.check_output_quality()

        logger.info(f"[*] Validation complete: {'PASSED' if self.result.passed else 'FAILED'}")

        return self.result

    def check_files_exist(self):
        """Check that all required files exist."""
        logger.info("[CHECK] Checking file existence...")

        required_files = []
        found_files = []
        missing_files = []

        # Model files
        model_files = [
            'pytorch_model.bin',
            'model.safetensors',
            'config.json'
        ]

        for filename in model_files:
            filepath = self.model_path / filename
            if filepath.exists():
                found_files.append(filename)
                break
        else:
            missing_files.append("model file (pytorch_model.bin or model.safetensors)")

        # Config file
        config_file = self.model_path / 'config.json'
        if config_file.exists():
            found_files.append('config.json')
        else:
            missing_files.append('config.json')

        # Tokenizer files
        tokenizer_files = [
            'tokenizer.json',
            'tokenizer_config.json',
            'vocab.json'
        ]

        tokenizer_found = False
        for filename in tokenizer_files:
            filepath = self.tokenizer_path / filename
            if filepath.exists():
                found_files.append(filename)
                tokenizer_found = True

        if not tokenizer_found:
            self.result.add_warning("No tokenizer files found")

        # Record check result
        passed = len(missing_files) == 0

        self.result.add_check('files_exist', passed, {
            'found_files': found_files,
            'missing_files': missing_files,
            'model_path': str(self.model_path),
            'tokenizer_path': str(self.tokenizer_path)
        })

        if passed:
            logger.info(f"  [OK] All required files found")
        else:
            logger.error(f"  [FAIL] Missing files: {', '.join(missing_files)}")

    def check_model_loadable(self):
        """Check that model can be loaded."""
        logger.info("[CHECK] Checking model loading...")

        try:
            from transformers import AutoModelForCausalLM, AutoConfig

            start_time = time.time()

            # Load config first
            config = AutoConfig.from_pretrained(str(self.model_path))
            config_load_time = time.time() - start_time

            # Load model
            model_start = time.time()
            model = AutoModelForCausalLM.from_pretrained(
                str(self.model_path),
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map='auto' if torch.cuda.is_available() else None
            )
            model_load_time = time.time() - model_start

            # Get model info
            param_count = sum(p.numel() for p in model.parameters())
            trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)

            self.result.add_check('model_loadable', True, {
                'config_load_time': f"{config_load_time:.2f}s",
                'model_load_time': f"{model_load_time:.2f}s",
                'total_parameters': param_count,
                'trainable_parameters': trainable_params,
                'model_type': config.model_type,
                'architecture': model.__class__.__name__
            })

            self.result.metrics['model_load_time'] = model_load_time
            self.result.metrics['param_count'] = param_count

            logger.info(f"  [OK] Model loaded successfully")
            logger.info(f"       Parameters: {param_count:,} (trainable: {trainable_params:,})")
            logger.info(f"       Load time: {model_load_time:.2f}s")

            # Store model for further checks
            self.model = model
            self.config = config

        except Exception as e:
            error_msg = f"Failed to load model: {str(e)}"
            self.result.add_check('model_loadable', False, {'error': error_msg})
            self.result.add_error(error_msg)
            logger.error(f"  [FAIL] {error_msg}")

    def check_tokenizer_loadable(self):
        """Check that tokenizer can be loaded."""
        logger.info("[CHECK] Checking tokenizer loading...")

        try:
            from transformers import AutoTokenizer

            start_time = time.time()
            tokenizer = AutoTokenizer.from_pretrained(str(self.tokenizer_path))
            load_time = time.time() - start_time

            vocab_size = tokenizer.vocab_size
            special_tokens = tokenizer.special_tokens_map

            self.result.add_check('tokenizer_loadable', True, {
                'load_time': f"{load_time:.2f}s",
                'vocab_size': vocab_size,
                'special_tokens': list(special_tokens.keys())
            })

            logger.info(f"  [OK] Tokenizer loaded successfully")
            logger.info(f"       Vocab size: {vocab_size:,}")
            logger.info(f"       Load time: {load_time:.2f}s")

            # Store tokenizer for further checks
            self.tokenizer = tokenizer

        except Exception as e:
            error_msg = f"Failed to load tokenizer: {str(e)}"
            self.result.add_check('tokenizer_loadable', False, {'error': error_msg})
            self.result.add_warning(error_msg)
            logger.warning(f"  [WARN] {error_msg}")

    def check_model_architecture(self):
        """Validate model architecture."""
        logger.info("[CHECK] Checking model architecture...")

        if not hasattr(self, 'model') or not hasattr(self, 'config'):
            self.result.add_warning("Model not loaded, skipping architecture check")
            return

        try:
            # Check architecture components
            has_embeddings = hasattr(self.model, 'get_input_embeddings')
            has_lm_head = hasattr(self.model, 'lm_head') or hasattr(self.model, 'get_output_embeddings')

            # Get layer count
            if hasattr(self.config, 'num_hidden_layers'):
                num_layers = self.config.num_hidden_layers
            elif hasattr(self.config, 'n_layer'):
                num_layers = self.config.n_layer
            else:
                num_layers = "unknown"

            # Get hidden size
            if hasattr(self.config, 'hidden_size'):
                hidden_size = self.config.hidden_size
            elif hasattr(self.config, 'd_model'):
                hidden_size = self.config.d_model
            else:
                hidden_size = "unknown"

            self.result.add_check('architecture', True, {
                'has_embeddings': has_embeddings,
                'has_lm_head': has_lm_head,
                'num_layers': num_layers,
                'hidden_size': hidden_size,
                'model_type': self.config.model_type
            })

            logger.info(f"  [OK] Architecture valid")
            logger.info(f"       Type: {self.config.model_type}")
            logger.info(f"       Layers: {num_layers}")
            logger.info(f"       Hidden size: {hidden_size}")

        except Exception as e:
            error_msg = f"Architecture check failed: {str(e)}"
            self.result.add_check('architecture', False, {'error': error_msg})
            self.result.add_warning(error_msg)
            logger.warning(f"  [WARN] {error_msg}")

    def check_inference_works(self, test_prompts: Optional[List[str]] = None):
        """Test that model can perform inference."""
        logger.info("[CHECK] Testing inference...")

        if not hasattr(self, 'model') or not hasattr(self, 'tokenizer'):
            self.result.add_warning("Model or tokenizer not loaded, skipping inference check")
            return

        if test_prompts is None:
            test_prompts = [
                "def hello_world():",
                "function add(a, b) {",
                "Write a Python function to"
            ]

        try:
            results = []

            for prompt in test_prompts:
                start_time = time.time()

                # Tokenize
                inputs = self.tokenizer(prompt, return_tensors="pt")
                if torch.cuda.is_available():
                    inputs = {k: v.cuda() for k, v in inputs.items()}

                # Generate
                with torch.no_grad():
                    outputs = self.model.generate(
                        **inputs,
                        max_new_tokens=20,
                        do_sample=False,
                        pad_token_id=self.tokenizer.eos_token_id
                    )

                # Decode
                generated = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

                inference_time = time.time() - start_time

                results.append({
                    'prompt': prompt[:50],
                    'output': generated[:100],
                    'time': f"{inference_time:.3f}s"
                })

            self.result.add_check('inference', True, {
                'test_count': len(test_prompts),
                'results': results
            })

            avg_time = sum(float(r['time'].replace('s', '')) for r in results) / len(results)
            self.result.metrics['avg_inference_time'] = avg_time

            logger.info(f"  [OK] Inference working")
            logger.info(f"       Tests passed: {len(test_prompts)}")
            logger.info(f"       Avg time: {avg_time:.3f}s")

        except Exception as e:
            error_msg = f"Inference failed: {str(e)}"
            self.result.add_check('inference', False, {'error': error_msg})
            self.result.add_error(error_msg)
            logger.error(f"  [FAIL] {error_msg}")

    def benchmark_inference_speed(self, num_samples: int = 10):
        """Benchmark inference speed."""
        logger.info(f"[CHECK] Benchmarking inference speed ({num_samples} samples)...")

        if not hasattr(self, 'model') or not hasattr(self, 'tokenizer'):
            self.result.add_warning("Model or tokenizer not loaded, skipping benchmark")
            return

        try:
            test_prompt = "def calculate_sum(numbers):"
            times = []

            for _ in range(num_samples):
                start = time.time()

                inputs = self.tokenizer(test_prompt, return_tensors="pt")
                if torch.cuda.is_available():
                    inputs = {k: v.cuda() for k, v in inputs.items()}

                with torch.no_grad():
                    _ = self.model.generate(
                        **inputs,
                        max_new_tokens=50,
                        do_sample=False,
                        pad_token_id=self.tokenizer.eos_token_id
                    )

                times.append(time.time() - start)

            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)

            self.result.add_check('benchmark', True, {
                'samples': num_samples,
                'avg_time': f"{avg_time:.3f}s",
                'min_time': f"{min_time:.3f}s",
                'max_time': f"{max_time:.3f}s",
                'tokens_per_second': f"{50 / avg_time:.1f}"
            })

            self.result.metrics['benchmark_avg_time'] = avg_time
            self.result.metrics['tokens_per_second'] = 50 / avg_time

            logger.info(f"  [OK] Benchmark complete")
            logger.info(f"       Avg: {avg_time:.3f}s")
            logger.info(f"       Min: {min_time:.3f}s, Max: {max_time:.3f}s")
            logger.info(f"       ~{50 / avg_time:.1f} tokens/sec")

        except Exception as e:
            error_msg = f"Benchmark failed: {str(e)}"
            self.result.add_check('benchmark', False, {'error': error_msg})
            self.result.add_warning(error_msg)
            logger.warning(f"  [WARN] {error_msg}")

    def check_output_quality(self):
        """Basic quality checks on model outputs."""
        logger.info("[CHECK] Checking output quality...")

        if not hasattr(self, 'model') or not hasattr(self, 'tokenizer'):
            self.result.add_warning("Model or tokenizer not loaded, skipping quality check")
            return

        try:
            # Test if model produces reasonable code
            test_cases = [
                ("def add_numbers(a, b):", "python"),
                ("function multiply(x, y) {", "javascript"),
                ("public class Hello {", "java")
            ]

            quality_scores = []

            for prompt, language in test_cases:
                inputs = self.tokenizer(prompt, return_tensors="pt")
                if torch.cuda.is_available():
                    inputs = {k: v.cuda() for k, v in inputs.items()}

                with torch.no_grad():
                    outputs = self.model.generate(
                        **inputs,
                        max_new_tokens=50,
                        do_sample=True,
                        temperature=0.7,
                        top_p=0.9,
                        pad_token_id=self.tokenizer.eos_token_id
                    )

                generated = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

                # Basic quality metrics
                has_code = any(char in generated for char in '(){}[]')
                reasonable_length = 10 < len(generated) < 500
                not_repetitive = len(set(generated.split())) / max(len(generated.split()), 1) > 0.3

                score = sum([has_code, reasonable_length, not_repetitive]) / 3
                quality_scores.append(score)

            avg_quality = sum(quality_scores) / len(quality_scores)

            self.result.add_check('output_quality', avg_quality > 0.5, {
                'avg_quality_score': f"{avg_quality:.2f}",
                'test_cases': len(test_cases),
                'passed': avg_quality > 0.5
            })

            self.result.metrics['quality_score'] = avg_quality

            logger.info(f"  [OK] Quality check complete")
            logger.info(f"       Quality score: {avg_quality:.2f}/1.00")

        except Exception as e:
            error_msg = f"Quality check failed: {str(e)}"
            self.result.add_check('output_quality', False, {'error': error_msg})
            self.result.add_warning(error_msg)
            logger.warning(f"  [WARN] {error_msg}")

    def get_result(self) -> ValidationResult:
        """Get validation result."""
        return self.result

    def print_summary(self):
        """Print validation summary."""
        print("\n" + "="*70)
        print("[*] MODEL VALIDATION SUMMARY")
        print("="*70)

        print(f"\nModel: {self.model_path}")
        print(f"Status: {'PASSED' if self.result.passed else 'FAILED'}")
        print(f"Timestamp: {self.result.timestamp}")

        print(f"\nChecks: ({len(self.result.checks)} total)")
        for name, check in self.result.checks.items():
            status = "[OK]" if check['passed'] else "[FAIL]"
            print(f"  {status} {name.replace('_', ' ').title()}")

        if self.result.metrics:
            print(f"\nMetrics:")
            for key, value in self.result.metrics.items():
                print(f"  {key.replace('_', ' ').title()}: {value:.2f}")

        if self.result.errors:
            print(f"\nErrors ({len(self.result.errors)}):")
            for error in self.result.errors:
                print(f"  [ERROR] {error}")

        if self.result.warnings:
            print(f"\nWarnings ({len(self.result.warnings)}):")
            for warning in self.result.warnings:
                print(f"  [WARN] {warning}")

        print("\n" + "="*70 + "\n")


__all__ = ['ModelValidator', 'ValidationResult']
