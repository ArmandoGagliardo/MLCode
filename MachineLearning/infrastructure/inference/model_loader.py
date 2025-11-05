"""
Model Loader
============

Infrastructure component for loading trained models from checkpoints.

Supports:
- Sequence-to-sequence models (code generation)
- Classification models (text, security)
- Automatic device detection (CPU/GPU)
- Checkpoint validation

Example:
    >>> from infrastructure.inference import ModelLoader
    >>>
    >>> loader = ModelLoader()
    >>> model, tokenizer = loader.load_seq2seq_model('models/code_generator')
    >>> print(f"Model loaded on {loader.device}")
"""

import logging
from pathlib import Path
from typing import Tuple, Optional

import torch
from transformers import (
    AutoTokenizer,
    AutoModelForSeq2SeqLM,
    AutoModelForSequenceClassification,
    AutoModelForCausalLM
)

from domain.exceptions import InferenceError

logger = logging.getLogger(__name__)


class ModelLoader:
    """
    Load trained models from checkpoints.

    Handles device management and model initialization for inference.

    Attributes:
        device: Device for inference (cuda/cpu)

    Example:
        >>> loader = ModelLoader()
        >>> model, tokenizer = loader.load_classification_model('models/classifier')
    """

    def __init__(self, device: Optional[str] = None):
        """
        Initialize ModelLoader.

        Args:
            device: Optional device ('cuda', 'cpu'). If None, auto-detect.
        """
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)

        logger.info(f"ModelLoader initialized on device: {self.device}")

    def load_seq2seq_model(
        self,
        model_path: str,
        local_files_only: bool = False
    ) -> Tuple[AutoModelForSeq2SeqLM, AutoTokenizer]:
        """
        Load sequence-to-sequence model for code generation.

        Args:
            model_path: Path to model checkpoint
            local_files_only: Whether to load only from local files

        Returns:
            Tuple of (model, tokenizer)

        Raises:
            InferenceError: If model loading fails

        Example:
            >>> model, tokenizer = loader.load_seq2seq_model('models/codegen')
        """
        try:
            model_path = Path(model_path)
            if not model_path.exists() and local_files_only:
                raise InferenceError(f"Model not found: {model_path}")

            logger.info(f"Loading seq2seq model from {model_path}")

            tokenizer = AutoTokenizer.from_pretrained(
                str(model_path),
                local_files_only=local_files_only
            )

            model = AutoModelForSeq2SeqLM.from_pretrained(
                str(model_path),
                local_files_only=local_files_only
            )

            model.to(self.device)
            model.eval()

            logger.info(f"Model loaded successfully ({model.num_parameters():,} parameters)")
            return model, tokenizer

        except Exception as e:
            raise InferenceError(f"Failed to load seq2seq model: {e}")

    def load_causal_model(
        self,
        model_path: str,
        local_files_only: bool = False
    ) -> Tuple[AutoModelForCausalLM, AutoTokenizer]:
        """
        Load causal language model for code generation.

        Args:
            model_path: Path to model checkpoint
            local_files_only: Whether to load only from local files

        Returns:
            Tuple of (model, tokenizer)

        Raises:
            InferenceError: If model loading fails

        Example:
            >>> model, tokenizer = loader.load_causal_model('models/codegen')
        """
        try:
            model_path = Path(model_path)
            if not model_path.exists() and local_files_only:
                raise InferenceError(f"Model not found: {model_path}")

            logger.info(f"Loading causal model from {model_path}")

            tokenizer = AutoTokenizer.from_pretrained(
                str(model_path),
                local_files_only=local_files_only
            )

            model = AutoModelForCausalLM.from_pretrained(
                str(model_path),
                local_files_only=local_files_only
            )

            # Set pad token if not present
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token

            model.to(self.device)
            model.eval()

            logger.info(f"Model loaded successfully ({model.num_parameters():,} parameters)")
            return model, tokenizer

        except Exception as e:
            raise InferenceError(f"Failed to load causal model: {e}")

    def load_classification_model(
        self,
        model_path: str,
        local_files_only: bool = True
    ) -> Tuple[AutoModelForSequenceClassification, AutoTokenizer]:
        """
        Load classification model.

        Args:
            model_path: Path to model checkpoint
            local_files_only: Whether to load only from local files

        Returns:
            Tuple of (model, tokenizer)

        Raises:
            InferenceError: If model loading fails

        Example:
            >>> model, tokenizer = loader.load_classification_model('models/classifier')
        """
        try:
            model_path = Path(model_path)
            if not model_path.exists() and local_files_only:
                raise InferenceError(f"Model not found: {model_path}")

            logger.info(f"Loading classification model from {model_path}")

            tokenizer = AutoTokenizer.from_pretrained(
                str(model_path),
                local_files_only=local_files_only
            )

            model = AutoModelForSequenceClassification.from_pretrained(
                str(model_path),
                local_files_only=local_files_only
            )

            model.to(self.device)
            model.eval()

            num_labels = model.config.num_labels
            logger.info(
                f"Model loaded successfully ({model.num_parameters():,} parameters, "
                f"{num_labels} labels)"
            )
            return model, tokenizer

        except Exception as e:
            raise InferenceError(f"Failed to load classification model: {e}")

    def get_device(self) -> torch.device:
        """Get current device."""
        return self.device

    def __str__(self) -> str:
        """String representation."""
        return f"ModelLoader(device={self.device})"

    def __repr__(self) -> str:
        """Detailed representation."""
        return f"ModelLoader(device='{self.device}')"
