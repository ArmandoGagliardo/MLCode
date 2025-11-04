"""
Domain Adaptive Pre-Training (DAPT) for Code Generation Models
================================================================

This script implements domain-adaptive pre-training, which continues training
a pre-trained model on domain-specific data. This is much more efficient than
training from scratch.

Benefits over training from scratch:
- 100x less compute required
- 10x faster convergence
- Often better final performance
- Preserves general knowledge while specializing

Supported base models:
- Salesforce/codegen-350M-mono (recommended for code)
- microsoft/codebert-base
- facebook/incoder-1B
- bigcode/santacoder
- Any HuggingFace causal LM model

Usage:
    # Basic domain adaptive training
    python domain_adaptive_trainer.py --base-model Salesforce/codegen-350M-mono --dataset dataset.jsonl

    # With custom parameters
    python domain_adaptive_trainer.py \\
        --base-model bigcode/santacoder \\
        --dataset dataset_storage/the_stack/python/*.jsonl \\
        --output-dir models/my_adapted_model \\
        --epochs 3 \\
        --batch-size 8 \\
        --learning-rate 2e-5

    # Resume from checkpoint
    python domain_adaptive_trainer.py --resume-from models/checkpoint-1000

Author: ML Code Intelligence Project
"""

import os
import sys
import json
import argparse
import logging
import torch
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from tqdm import tqdm
import numpy as np

# Add parent directory
sys.path.append(str(Path(__file__).parent.parent))

from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    Trainer,
    TrainingArguments,
    DataCollatorForLanguageModeling,
    EarlyStoppingCallback,
    get_linear_schedule_with_warmup
)
from datasets import load_dataset, Dataset
from torch.utils.data import DataLoader
import torch.nn.functional as F

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DomainAdaptiveTrainer:
    """
    Trainer for domain-adaptive pre-training of code generation models.
    """

    def __init__(self,
                 base_model: str = "Salesforce/codegen-350M-mono",
                 output_dir: str = "models/adapted",
                 use_gpu: bool = True):
        """
        Initialize domain adaptive trainer.

        Args:
            base_model: HuggingFace model name or path
            output_dir: Directory to save adapted model
            use_gpu: Use GPU if available
        """
        self.base_model_name = base_model
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Device configuration
        self.device = torch.device("cuda" if use_gpu and torch.cuda.is_available() else "cpu")
        logger.info(f"Using device: {self.device}")

        # Load model and tokenizer
        self.model = None
        self.tokenizer = None
        self.load_base_model()

        # Training statistics
        self.stats = {
            'initial_loss': None,
            'final_loss': None,
            'best_loss': float('inf'),
            'total_steps': 0,
            'training_time': 0
        }

    def load_base_model(self):
        """Load pre-trained model and tokenizer."""
        logger.info(f"Loading base model: {self.base_model_name}")

        try:
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.base_model_name,
                trust_remote_code=True  # Required for some models
            )

            # Add padding token if not present
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token

            # Load model
            self.model = AutoModelForCausalLM.from_pretrained(
                self.base_model_name,
                trust_remote_code=True,
                torch_dtype=torch.float16 if self.device.type == "cuda" else torch.float32,
                low_cpu_mem_usage=True
            )

            # Move to device
            self.model.to(self.device)

            # Model info
            total_params = sum(p.numel() for p in self.model.parameters())
            trainable_params = sum(p.numel() for p in self.model.parameters() if p.requires_grad)

            logger.info(f"[OK] Model loaded successfully")
            logger.info(f"  Total parameters: {total_params:,}")
            logger.info(f"  Trainable parameters: {trainable_params:,}")
            logger.info(f"  Model type: {self.model.config.model_type}")

        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise

    def prepare_dataset(self, dataset_path: str, max_length: int = 1024) -> Tuple[Dataset, Dataset]:
        """
        Prepare dataset for training.

        Args:
            dataset_path: Path to JSONL dataset file(s)
            max_length: Maximum sequence length

        Returns:
            Train and validation datasets
        """
        logger.info(f"Preparing dataset from: {dataset_path}")

        # Handle wildcards
        dataset_files = []
        if '*' in dataset_path:
            dataset_files = list(Path(dataset_path).parent.glob(Path(dataset_path).name))
        else:
            dataset_files = [Path(dataset_path)]

        logger.info(f"Found {len(dataset_files)} dataset files")

        # Load all examples
        all_examples = []
        for file_path in dataset_files:
            if file_path.suffix == '.jsonl':
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        example = json.loads(line)
                        all_examples.append(example)
            elif file_path.suffix == '.json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        all_examples.extend(data)
                    else:
                        all_examples.append(data)

        logger.info(f"Loaded {len(all_examples)} examples")

        # Format for training
        formatted_examples = []
        for ex in all_examples:
            # Create training text from input-output pairs
            if 'input' in ex and 'output' in ex:
                # Format with clear separation
                text = f"### Instruction:\n{ex['input']}\n\n### Response:\n{ex['output']}"

                # Add context if available
                if 'context' in ex and isinstance(ex['context'], dict):
                    imports = ex['context'].get('imports', [])
                    if imports:
                        imports_text = '\n'.join(imports[:5])  # Limit imports
                        text = f"{imports_text}\n\n{text}"

            elif 'output' in ex:
                # Just use output if no input
                text = ex['output']
            else:
                # Skip if no useful data
                continue

            formatted_examples.append({'text': text})

        # Create dataset
        dataset = Dataset.from_list(formatted_examples)

        # Tokenize
        def tokenize_function(examples):
            return self.tokenizer(
                examples['text'],
                truncation=True,
                padding='max_length',
                max_length=max_length
            )

        tokenized_dataset = dataset.map(
            tokenize_function,
            batched=True,
            remove_columns=['text']
        )

        # Split into train/validation (90/10)
        split_dataset = tokenized_dataset.train_test_split(test_size=0.1, seed=42)

        logger.info(f"Dataset prepared:")
        logger.info(f"  Training examples: {len(split_dataset['train'])}")
        logger.info(f"  Validation examples: {len(split_dataset['test'])}")

        return split_dataset['train'], split_dataset['test']

    def train(self,
             train_dataset: Dataset,
             val_dataset: Dataset,
             num_epochs: int = 3,
             batch_size: int = 8,
             learning_rate: float = 2e-5,
             warmup_ratio: float = 0.1,
             gradient_accumulation_steps: int = 1,
             fp16: bool = True,
             save_steps: int = 500,
             eval_steps: int = 500,
             logging_steps: int = 50):
        """
        Perform domain-adaptive training.

        Args:
            train_dataset: Training dataset
            val_dataset: Validation dataset
            num_epochs: Number of training epochs
            batch_size: Batch size per device
            learning_rate: Learning rate (should be lower than pre-training)
            warmup_ratio: Warmup ratio for learning rate
            gradient_accumulation_steps: Gradient accumulation steps
            fp16: Use mixed precision training
            save_steps: Save checkpoint every N steps
            eval_steps: Evaluate every N steps
            logging_steps: Log metrics every N steps
        """
        logger.info("="*60)
        logger.info("STARTING DOMAIN ADAPTIVE TRAINING")
        logger.info("="*60)

        # Training arguments
        training_args = TrainingArguments(
            output_dir=str(self.output_dir),
            num_train_epochs=num_epochs,
            per_device_train_batch_size=batch_size,
            per_device_eval_batch_size=batch_size,
            gradient_accumulation_steps=gradient_accumulation_steps,
            warmup_ratio=warmup_ratio,
            learning_rate=learning_rate,
            fp16=fp16 and self.device.type == "cuda",
            logging_dir=str(self.output_dir / "logs"),
            logging_steps=logging_steps,
            save_steps=save_steps,
            eval_steps=eval_steps,
            evaluation_strategy="steps",
            save_strategy="steps",
            save_total_limit=3,  # Keep only 3 checkpoints
            load_best_model_at_end=True,
            metric_for_best_model="eval_loss",
            greater_is_better=False,
            push_to_hub=False,
            report_to=["tensorboard"],  # Use TensorBoard for logging
            dataloader_drop_last=True,
            remove_unused_columns=False,
            label_names=["input_ids"],
        )

        # Data collator for language modeling
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=self.tokenizer,
            mlm=False,  # Causal LM, not masked LM
            pad_to_multiple_of=8 if fp16 else None
        )

        # Custom trainer with better metrics
        trainer = CodeGenerationTrainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=val_dataset,
            data_collator=data_collator,
            tokenizer=self.tokenizer,
            callbacks=[
                EarlyStoppingCallback(early_stopping_patience=3)
            ]
        )

        # Start training
        logger.info("Training configuration:")
        logger.info(f"  Epochs: {num_epochs}")
        logger.info(f"  Batch size: {batch_size}")
        logger.info(f"  Learning rate: {learning_rate}")
        logger.info(f"  Warmup ratio: {warmup_ratio}")
        logger.info(f"  Mixed precision: {fp16}")
        logger.info(f"  Gradient accumulation: {gradient_accumulation_steps}")

        start_time = datetime.now()

        # Train
        train_result = trainer.train()

        # Save final model
        logger.info("Saving final model...")
        trainer.save_model()
        trainer.save_state()

        # Save tokenizer
        self.tokenizer.save_pretrained(self.output_dir)

        # Calculate training time
        training_time = (datetime.now() - start_time).total_seconds()

        # Update statistics
        self.stats['final_loss'] = train_result.metrics.get('train_loss')
        self.stats['total_steps'] = train_result.global_step
        self.stats['training_time'] = training_time

        # Print results
        self._print_results(train_result)

        return train_result

    def _print_results(self, train_result):
        """Print training results."""
        print("\n" + "="*60)
        print("TRAINING COMPLETED")
        print("="*60)
        print(f"Final loss:           {train_result.metrics.get('train_loss', 'N/A'):.4f}")
        print(f"Total steps:          {train_result.global_step}")
        print(f"Training time:        {self.stats['training_time']/60:.2f} minutes")
        print(f"Model saved to:       {self.output_dir}")
        print("="*60)

    def evaluate_model(self, test_prompts: List[str] = None):
        """
        Evaluate the adapted model with test prompts.

        Args:
            test_prompts: List of test prompts to generate from
        """
        if test_prompts is None:
            test_prompts = [
                "def fibonacci(n):",
                "class DataProcessor:",
                "function calculateSum(a, b) {",
                "def parse_json(data):",
                "import numpy as np\n\ndef matrix_multiply("
            ]

        logger.info("\nEvaluating model with test prompts...")

        self.model.eval()

        for prompt in test_prompts:
            print(f"\nPrompt: {prompt}")

            # Tokenize
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)

            # Generate
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_length=100,
                    temperature=0.7,
                    do_sample=True,
                    top_p=0.9,
                    pad_token_id=self.tokenizer.pad_token_id
                )

            # Decode
            generated = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            print(f"Generated: {generated}")
            print("-" * 40)


class CodeGenerationTrainer(Trainer):
    """
    Custom trainer with better metrics for code generation.
    """

    def compute_loss(self, model, inputs, return_outputs=False):
        """
        Custom loss computation with label smoothing.
        """
        labels = inputs.pop("labels", inputs["input_ids"].clone())

        # Forward pass
        outputs = model(**inputs)

        # Shift labels for causal LM
        shift_logits = outputs.logits[..., :-1, :].contiguous()
        shift_labels = labels[..., 1:].contiguous()

        # Calculate loss with label smoothing
        loss_fct = torch.nn.CrossEntropyLoss(label_smoothing=0.1)
        loss = loss_fct(
            shift_logits.view(-1, shift_logits.size(-1)),
            shift_labels.view(-1)
        )

        return (loss, outputs) if return_outputs else loss


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(
        description="Domain Adaptive Pre-Training for code generation models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    # Model selection
    parser.add_argument('--base-model', type=str, default='Salesforce/codegen-350M-mono',
                       help='Base model from HuggingFace (default: Salesforce/codegen-350M-mono)')
    parser.add_argument('--resume-from', type=str,
                       help='Resume training from checkpoint')

    # Dataset
    parser.add_argument('--dataset', type=str, required=True,
                       help='Path to dataset file (JSONL or JSON)')
    parser.add_argument('--max-length', type=int, default=1024,
                       help='Maximum sequence length (default: 1024)')

    # Training parameters
    parser.add_argument('--epochs', type=int, default=3,
                       help='Number of epochs (default: 3)')
    parser.add_argument('--batch-size', type=int, default=8,
                       help='Batch size (default: 8)')
    parser.add_argument('--learning-rate', type=float, default=2e-5,
                       help='Learning rate (default: 2e-5)')
    parser.add_argument('--warmup-ratio', type=float, default=0.1,
                       help='Warmup ratio (default: 0.1)')
    parser.add_argument('--gradient-accumulation', type=int, default=1,
                       help='Gradient accumulation steps (default: 1)')

    # Output
    parser.add_argument('--output-dir', type=str, default='models/adapted',
                       help='Output directory (default: models/adapted)')

    # Optimization
    parser.add_argument('--fp16', action='store_true',
                       help='Use mixed precision training')
    parser.add_argument('--cpu', action='store_true',
                       help='Force CPU usage')

    # Evaluation
    parser.add_argument('--evaluate', action='store_true',
                       help='Evaluate model after training')

    args = parser.parse_args()

    # Initialize trainer
    trainer = DomainAdaptiveTrainer(
        base_model=args.base_model if not args.resume_from else args.resume_from,
        output_dir=args.output_dir,
        use_gpu=not args.cpu
    )

    # Prepare dataset
    train_dataset, val_dataset = trainer.prepare_dataset(
        dataset_path=args.dataset,
        max_length=args.max_length
    )

    # Train
    result = trainer.train(
        train_dataset=train_dataset,
        val_dataset=val_dataset,
        num_epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        warmup_ratio=args.warmup_ratio,
        gradient_accumulation_steps=args.gradient_accumulation,
        fp16=args.fp16
    )

    # Evaluate if requested
    if args.evaluate:
        trainer.evaluate_model()


if __name__ == '__main__':
    main()