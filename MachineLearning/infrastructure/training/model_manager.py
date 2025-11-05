"""
Model Manager
=============

Manages ML model initialization and configuration.

This component handles:
- Model loading from HuggingFace
- Tokenizer initialization
- Device management (CPU/GPU/Multi-GPU)
- Model type detection (seq2seq, causal, classification)
- Default model selection per task

Supported Tasks:
----------------
- text_classification: Binary or multi-class classification
- code_generation: Code generation with causal LM
- security_classification: 5-class security categorization

Example:
    >>> from infrastructure.training import ModelManager
    >>>
    >>> # Initialize for code generation
    >>> manager = ModelManager(
    ...     task='code_generation',
    ...     model_name='Salesforce/codegen-350M-mono'
    ... )
    >>>
    >>> # Get model and tokenizer
    >>> model = manager.get_model()
    >>> tokenizer = manager.get_tokenizer()
    >>>
    >>> # Check model type
    >>> print(manager.get_model_type())  # 'causal'
    >>> print(manager.device)  # cuda or cpu
"""

import os
import logging
from typing import Tuple, Optional
from enum import Enum

from domain.exceptions import ConfigurationError, TrainingError

logger = logging.getLogger(__name__)


class TaskType(Enum):
    """Supported ML tasks."""
    TEXT_CLASSIFICATION = "text_classification"
    CODE_GENERATION = "code_generation"
    SECURITY_CLASSIFICATION = "security_classification"


class ModelType(Enum):
    """Model architecture types."""
    SEQ2SEQ = "seq2seq"
    CAUSAL = "causal"
    CLASSIFICATION = "classification"


# Default models for each task
DEFAULT_MODELS = {
    TaskType.TEXT_CLASSIFICATION: "microsoft/codebert-base",
    TaskType.CODE_GENERATION: "Salesforce/codegen-350M-mono",
    TaskType.SECURITY_CLASSIFICATION: "microsoft/codebert-base"
}


class ModelManager:
    """
    Model Manager for ML training infrastructure.

    Handles model and tokenizer initialization, device management,
    and model type detection following Clean Architecture principles.

    Attributes:
        task: ML task type
        model_name: HuggingFace model name
        num_labels: Number of labels for classification tasks
        device: PyTorch device (cpu/cuda)
        model: Loaded model
        tokenizer: Loaded tokenizer

    Example:
        >>> manager = ModelManager(
        ...     task='code_generation',
        ...     model_name='Salesforce/codegen-350M-mono',
        ...     device='cuda'
        ... )
        >>> model, tokenizer = manager.get_model(), manager.get_tokenizer()
    """

    def __init__(
        self,
        task: str,
        model_name: Optional[str] = None,
        num_labels: Optional[int] = None,
        device: Optional[str] = None,
        trust_remote_code: bool = True
    ):
        """
        Initialize Model Manager.

        Args:
            task: Task type (text_classification, code_generation, security_classification)
            model_name: HuggingFace model name (uses default if None)
            num_labels: Number of labels for classification (auto-detected if None)
            device: Device to use ('cpu', 'cuda', or None for auto-detect)
            trust_remote_code: Whether to trust remote code in models

        Raises:
            ConfigurationError: If task is unsupported or configuration invalid
            TrainingError: If model loading fails

        Example:
            >>> # Use default model for task
            >>> manager = ModelManager(task='code_generation')
            >>>
            >>> # Use custom model
            >>> manager = ModelManager(
            ...     task='text_classification',
            ...     model_name='bert-base-uncased',
            ...     num_labels=3
            ... )
        """
        # Validate and set task
        try:
            self.task = TaskType(task)
        except ValueError:
            raise ConfigurationError(
                f"Unsupported task: {task}",
                details={
                    'task': task,
                    'supported_tasks': [t.value for t in TaskType]
                }
            )

        # Set model name (use default if not provided)
        self.model_name = model_name or DEFAULT_MODELS.get(self.task)
        if not self.model_name:
            raise ConfigurationError(f"No default model for task: {task}")

        # Set number of labels for classification
        if num_labels is not None:
            self.num_labels = num_labels
        elif self.task == TaskType.SECURITY_CLASSIFICATION:
            self.num_labels = 5  # 5-class security categorization
        elif self.task == TaskType.TEXT_CLASSIFICATION:
            self.num_labels = 2  # Binary classification
        else:
            self.num_labels = None  # Not applicable for generation

        self.trust_remote_code = trust_remote_code

        # Configure HuggingFace cache
        self._configure_huggingface()

        # Initialize device
        self.device = self._initialize_device(device)

        # Load model and tokenizer
        self.model = None
        self.tokenizer = None
        self._load_model_and_tokenizer()

        logger.info(
            f"ModelManager initialized: task={self.task.value}, "
            f"model={self.model_name}, device={self.device}"
        )

    def _configure_huggingface(self) -> None:
        """Configure HuggingFace environment variables."""
        # Set cache directory
        hf_home = os.path.join(os.path.expanduser("~"), ".cache", "huggingface")
        os.environ.setdefault('HF_HOME', hf_home)

        # Disable symlinks warning (Windows compatibility)
        os.environ.setdefault('HF_HUB_DISABLE_SYMLINKS_WARNING', "1")

        # Increase download timeout
        os.environ.setdefault('HF_HUB_DOWNLOAD_TIMEOUT', "500")

        logger.debug(f"HuggingFace cache configured: {hf_home}")

    def _initialize_device(self, device: Optional[str] = None) -> str:
        """
        Initialize PyTorch device.

        Args:
            device: Device string ('cpu', 'cuda', or None for auto-detect)

        Returns:
            Device string

        Raises:
            TrainingError: If PyTorch import fails
        """
        try:
            import torch
        except ImportError:
            raise TrainingError(
                "PyTorch not installed. Install with: pip install torch"
            )

        if device:
            return device

        # Auto-detect device
        if torch.cuda.is_available():
            device = "cuda"
            num_gpus = torch.cuda.device_count()
            logger.info(f"CUDA available: {num_gpus} GPU(s) detected")
        else:
            device = "cpu"
            logger.info("CUDA not available, using CPU")

        return device

    def _load_model_and_tokenizer(self) -> None:
        """
        Load model and tokenizer from HuggingFace.

        Raises:
            TrainingError: If loading fails
        """
        try:
            from transformers import (
                AutoTokenizer,
                AutoModelForSeq2SeqLM,
                AutoModelForSequenceClassification,
                AutoModelForCausalLM
            )
            import torch
        except ImportError as e:
            raise TrainingError(
                f"Required library not installed: {e}. "
                "Install with: pip install transformers torch"
            )

        try:
            # Load tokenizer
            logger.info(f"Loading tokenizer: {self.model_name}")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)

            # Ensure tokenizer has pad token
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
                logger.debug("Set pad_token to eos_token")

            # Load model based on task
            logger.info(f"Loading model for task: {self.task.value}")

            if self.task == TaskType.CODE_GENERATION:
                # Code generation uses causal LM
                if "codegen" in self.model_name.lower():
                    self.model = AutoModelForCausalLM.from_pretrained(
                        self.model_name,
                        trust_remote_code=self.trust_remote_code,
                        pad_token_id=self.tokenizer.eos_token_id
                    )
                elif "bart" in self.model_name.lower():
                    # BART uses seq2seq
                    self.model = AutoModelForSeq2SeqLM.from_pretrained(
                        self.model_name
                    )
                else:
                    # Generic causal LM
                    self.model = AutoModelForCausalLM.from_pretrained(
                        self.model_name,
                        trust_remote_code=self.trust_remote_code
                    )

            elif self.task in [TaskType.TEXT_CLASSIFICATION, TaskType.SECURITY_CLASSIFICATION]:
                # Classification tasks
                self.model = AutoModelForSequenceClassification.from_pretrained(
                    self.model_name,
                    num_labels=self.num_labels
                )

            # Move model to device
            import torch
            device_obj = torch.device(self.device)
            self.model.to(device_obj)

            logger.info(f"Model loaded and moved to {self.device}")

        except Exception as e:
            raise TrainingError(
                f"Failed to load model: {e}",
                details={
                    'model_name': self.model_name,
                    'task': self.task.value
                }
            )

    def get_model(self):
        """
        Get loaded model.

        Returns:
            Loaded PyTorch model

        Example:
            >>> model = manager.get_model()
            >>> output = model(**inputs)
        """
        return self.model

    def get_tokenizer(self):
        """
        Get loaded tokenizer.

        Returns:
            Loaded HuggingFace tokenizer

        Example:
            >>> tokenizer = manager.get_tokenizer()
            >>> inputs = tokenizer("def hello():", return_tensors="pt")
        """
        return self.tokenizer

    def is_seq2seq_model(self) -> bool:
        """
        Check if model is sequence-to-sequence.

        Returns:
            True if seq2seq model

        Example:
            >>> if manager.is_seq2seq_model():
            ...     # Use seq2seq training
        """
        return "bart" in self.model_name.lower() or "t5" in self.model_name.lower()

    def is_causal_model(self) -> bool:
        """
        Check if model is causal language model.

        Returns:
            True if causal LM

        Example:
            >>> if manager.is_causal_model():
            ...     # Use causal LM training
        """
        return (
            not self.is_seq2seq_model()
            and self.task == TaskType.CODE_GENERATION
        )

    def is_classification_model(self) -> bool:
        """
        Check if model is for classification.

        Returns:
            True if classification model

        Example:
            >>> if manager.is_classification_model():
            ...     # Use classification training
        """
        return self.task in [
            TaskType.TEXT_CLASSIFICATION,
            TaskType.SECURITY_CLASSIFICATION
        ]

    def get_model_type(self) -> ModelType:
        """
        Get model architecture type.

        Returns:
            ModelType enum value

        Example:
            >>> model_type = manager.get_model_type()
            >>> if model_type == ModelType.CAUSAL:
            ...     print("Causal language model")
        """
        if self.is_seq2seq_model():
            return ModelType.SEQ2SEQ
        elif self.is_causal_model():
            return ModelType.CAUSAL
        else:
            return ModelType.CLASSIFICATION

    def prepare_input_for_generation(self, text: str) -> str:
        """
        Prepare input text for code generation.

        Args:
            text: Input description or prompt

        Returns:
            Formatted prompt for generation

        Example:
            >>> prompt = manager.prepare_input_for_generation("sort a list")
            >>> # Returns: "# Task: sort a list\n\ndef"
        """
        if self.task != TaskType.CODE_GENERATION:
            return text

        # Add code generation prompt template
        if "python" in text.lower():
            return f"# Python function\n# Input: {text}\n\ndef"
        else:
            return f"# Task: {text}\n\ndef"

    def get_num_parameters(self) -> int:
        """
        Get number of model parameters.

        Returns:
            Total number of parameters

        Example:
            >>> num_params = manager.get_num_parameters()
            >>> print(f"Model has {num_params:,} parameters")
        """
        return sum(p.numel() for p in self.model.parameters())

    def get_trainable_parameters(self) -> int:
        """
        Get number of trainable parameters.

        Returns:
            Number of trainable parameters

        Example:
            >>> trainable = manager.get_trainable_parameters()
            >>> total = manager.get_num_parameters()
            >>> print(f"Trainable: {trainable/total*100:.1f}%")
        """
        return sum(p.numel() for p in self.model.parameters() if p.requires_grad)

    def __str__(self) -> str:
        """String representation."""
        return (
            f"ModelManager(task={self.task.value}, "
            f"model={self.model_name}, device={self.device})"
        )

    def __repr__(self) -> str:
        """Detailed representation."""
        return (
            f"ModelManager(task='{self.task.value}', "
            f"model_name='{self.model_name}', "
            f"num_labels={self.num_labels}, "
            f"device='{self.device}', "
            f"model_type='{self.get_model_type().value}')"
        )
