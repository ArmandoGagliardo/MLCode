"""
Inference Service
=================

Application service for managing model inference operations.

Orchestrates:
- Text classification
- Security classification
- Code generation
- Model loading and caching

Example:
    >>> from application.services import InferenceService
    >>>
    >>> service = InferenceService()
    >>> service.load_text_classifier('models/text_classifier')
    >>> result = service.classify_text("def example(): pass")
    >>> print(f"Classification: {result['label_name']}")
"""

import logging
from typing import Dict, List, Optional, Union
from pathlib import Path

from infrastructure.inference import (
    ModelLoader,
    TextClassifier,
    SecurityClassifier,
    CodeGenerator,
    GenerationConfig,
    ModelType
)
from domain.exceptions import InferenceError

logger = logging.getLogger(__name__)


class InferenceService:
    """
    Application service for model inference.

    Provides high-level API for inference operations with model caching
    and unified error handling.

    Attributes:
        text_classifier: Text classification model (lazy loaded)
        security_classifier: Security classification model (lazy loaded)
        code_generator: Code generation model (lazy loaded)
        device: Inference device

    Example:
        >>> service = InferenceService(device='cuda')
        >>> service.load_text_classifier('models/classifier')
        >>> result = service.classify_text("sample code")
    """

    def __init__(self, device: Optional[str] = None):
        """
        Initialize InferenceService.

        Args:
            device: Optional device override ('cuda', 'cpu')
        """
        self.device = device
        self._text_classifier: Optional[TextClassifier] = None
        self._security_classifier: Optional[SecurityClassifier] = None
        self._code_generator: Optional[CodeGenerator] = None

        logger.info(f"InferenceService initialized (device={device or 'auto'})")

    # ============================================================
    # Text Classification
    # ============================================================

    def load_text_classifier(
        self,
        model_path: str,
        label_names: Optional[List[str]] = None,
        local_files_only: bool = True
    ) -> None:
        """
        Load text classification model.

        Args:
            model_path: Path to model checkpoint
            label_names: Optional label names
            local_files_only: Whether to load only from local files

        Raises:
            InferenceError: If loading fails
        """
        try:
            logger.info(f"Loading text classifier from {model_path}")
            self._text_classifier = TextClassifier(
                model_path=model_path,
                label_names=label_names,
                device=self.device,
                local_files_only=local_files_only
            )
            logger.info("Text classifier loaded successfully")
        except Exception as e:
            raise InferenceError(f"Failed to load text classifier: {e}")

    def classify_text(
        self,
        text: str,
        return_confidence: bool = True,
        return_all_scores: bool = False
    ) -> Dict[str, Union[int, str, float, List[float]]]:
        """
        Classify text.

        Args:
            text: Input text
            return_confidence: Whether to return confidence score
            return_all_scores: Whether to return all label scores

        Returns:
            Classification result dictionary

        Raises:
            InferenceError: If classifier not loaded or classification fails
        """
        if self._text_classifier is None:
            raise InferenceError(
                "Text classifier not loaded. Call load_text_classifier() first."
            )

        return self._text_classifier.classify(
            text=text,
            return_confidence=return_confidence,
            return_all_scores=return_all_scores
        )

    def classify_texts_batch(
        self,
        texts: List[str],
        batch_size: int = 32
    ) -> List[Dict[str, Union[int, str, float]]]:
        """
        Classify batch of texts.

        Args:
            texts: List of input texts
            batch_size: Batch size for processing

        Returns:
            List of classification results

        Raises:
            InferenceError: If classifier not loaded
        """
        if self._text_classifier is None:
            raise InferenceError(
                "Text classifier not loaded. Call load_text_classifier() first."
            )

        return self._text_classifier.classify_batch(texts, batch_size=batch_size)

    # ============================================================
    # Security Classification
    # ============================================================

    def load_security_classifier(
        self,
        model_path: str,
        label_names: Optional[List[str]] = None,
        vulnerability_threshold: float = 0.5,
        local_files_only: bool = True
    ) -> None:
        """
        Load security classification model.

        Args:
            model_path: Path to model checkpoint
            label_names: Optional security label names
            vulnerability_threshold: Confidence threshold for vulnerabilities
            local_files_only: Whether to load only from local files

        Raises:
            InferenceError: If loading fails
        """
        try:
            logger.info(f"Loading security classifier from {model_path}")
            self._security_classifier = SecurityClassifier(
                model_path=model_path,
                label_names=label_names,
                device=self.device,
                local_files_only=local_files_only,
                vulnerability_threshold=vulnerability_threshold
            )
            logger.info("Security classifier loaded successfully")
        except Exception as e:
            raise InferenceError(f"Failed to load security classifier: {e}")

    def classify_security(
        self,
        text: str,
        return_confidence: bool = True,
        return_all_scores: bool = False
    ) -> Dict[str, Union[int, str, float, bool, List[float]]]:
        """
        Classify code for security issues.

        Args:
            text: Code to analyze
            return_confidence: Whether to return confidence score
            return_all_scores: Whether to return all label scores

        Returns:
            Security classification result with is_vulnerable flag

        Raises:
            InferenceError: If classifier not loaded or classification fails
        """
        if self._security_classifier is None:
            raise InferenceError(
                "Security classifier not loaded. Call load_security_classifier() first."
            )

        return self._security_classifier.classify(
            text=text,
            return_confidence=return_confidence,
            return_all_scores=return_all_scores
        )

    def classify_security_batch(
        self,
        texts: List[str],
        batch_size: int = 32
    ) -> List[Dict[str, Union[int, str, float, bool]]]:
        """
        Classify batch of code for security issues.

        Args:
            texts: List of code samples
            batch_size: Batch size for processing

        Returns:
            List of security classification results

        Raises:
            InferenceError: If classifier not loaded
        """
        if self._security_classifier is None:
            raise InferenceError(
                "Security classifier not loaded. Call load_security_classifier() first."
            )

        return self._security_classifier.classify_batch(texts, batch_size=batch_size)

    def filter_vulnerable_code(
        self,
        texts: List[str],
        batch_size: int = 32
    ) -> List[Dict[str, Union[str, float, int]]]:
        """
        Filter and return only vulnerable code samples.

        Args:
            texts: List of code samples
            batch_size: Batch size for processing

        Returns:
            List of vulnerable samples with metadata

        Raises:
            InferenceError: If classifier not loaded
        """
        if self._security_classifier is None:
            raise InferenceError(
                "Security classifier not loaded. Call load_security_classifier() first."
            )

        return self._security_classifier.filter_vulnerable(texts, batch_size=batch_size)

    def set_vulnerability_threshold(self, threshold: float) -> None:
        """
        Update vulnerability detection threshold.

        Args:
            threshold: New threshold (0.0 to 1.0)

        Raises:
            InferenceError: If classifier not loaded
            ValueError: If threshold out of range
        """
        if self._security_classifier is None:
            raise InferenceError(
                "Security classifier not loaded. Call load_security_classifier() first."
            )

        self._security_classifier.set_threshold(threshold)

    # ============================================================
    # Code Generation
    # ============================================================

    def load_code_generator(
        self,
        model_path: str,
        model_type: Union[str, ModelType] = ModelType.SEQ2SEQ,
        config: Optional[GenerationConfig] = None,
        local_files_only: bool = False
    ) -> None:
        """
        Load code generation model.

        Args:
            model_path: Path to model checkpoint or HuggingFace model ID
            model_type: Type of model ('seq2seq' or 'causal')
            config: Generation configuration
            local_files_only: Whether to load only from local files

        Raises:
            InferenceError: If loading fails
        """
        try:
            logger.info(f"Loading code generator from {model_path} (type={model_type})")
            self._code_generator = CodeGenerator(
                model_path=model_path,
                model_type=model_type,
                config=config,
                device=self.device,
                local_files_only=local_files_only
            )
            logger.info("Code generator loaded successfully")
        except Exception as e:
            raise InferenceError(f"Failed to load code generator: {e}")

    def generate_code(
        self,
        prompt: str,
        config: Optional[GenerationConfig] = None
    ) -> str:
        """
        Generate code from prompt.

        Args:
            prompt: Natural language description or code prefix
            config: Optional generation config override

        Returns:
            Generated code string

        Raises:
            InferenceError: If generator not loaded or generation fails
        """
        if self._code_generator is None:
            raise InferenceError(
                "Code generator not loaded. Call load_code_generator() first."
            )

        return self._code_generator.generate(prompt, config=config)

    def generate_code_batch(
        self,
        prompts: List[str],
        config: Optional[GenerationConfig] = None,
        batch_size: int = 8
    ) -> List[str]:
        """
        Generate code for batch of prompts.

        Args:
            prompts: List of prompts
            config: Optional generation config override
            batch_size: Batch size for processing

        Returns:
            List of generated code strings

        Raises:
            InferenceError: If generator not loaded
        """
        if self._code_generator is None:
            raise InferenceError(
                "Code generator not loaded. Call load_code_generator() first."
            )

        return self._code_generator.generate_batch(
            prompts,
            config=config,
            batch_size=batch_size
        )

    def generate_code_variations(
        self,
        prompt: str,
        num_variations: int = 3,
        config: Optional[GenerationConfig] = None
    ) -> List[str]:
        """
        Generate multiple code variations for single prompt.

        Args:
            prompt: Input prompt
            num_variations: Number of variations to generate
            config: Optional generation config override

        Returns:
            List of generated code strings

        Raises:
            InferenceError: If generator not loaded
        """
        if self._code_generator is None:
            raise InferenceError(
                "Code generator not loaded. Call load_code_generator() first."
            )

        return self._code_generator.generate_multiple(
            prompt,
            num_sequences=num_variations,
            config=config
        )

    def update_generation_config(self, config: GenerationConfig) -> None:
        """
        Update code generation configuration.

        Args:
            config: New generation configuration

        Raises:
            InferenceError: If generator not loaded
        """
        if self._code_generator is None:
            raise InferenceError(
                "Code generator not loaded. Call load_code_generator() first."
            )

        self._code_generator.set_config(config)

    # ============================================================
    # Model Management
    # ============================================================

    def is_text_classifier_loaded(self) -> bool:
        """Check if text classifier is loaded."""
        return self._text_classifier is not None

    def is_security_classifier_loaded(self) -> bool:
        """Check if security classifier is loaded."""
        return self._security_classifier is not None

    def is_code_generator_loaded(self) -> bool:
        """Check if code generator is loaded."""
        return self._code_generator is not None

    def unload_text_classifier(self) -> None:
        """Unload text classifier to free memory."""
        if self._text_classifier is not None:
            logger.info("Unloading text classifier")
            del self._text_classifier
            self._text_classifier = None

    def unload_security_classifier(self) -> None:
        """Unload security classifier to free memory."""
        if self._security_classifier is not None:
            logger.info("Unloading security classifier")
            del self._security_classifier
            self._security_classifier = None

    def unload_code_generator(self) -> None:
        """Unload code generator to free memory."""
        if self._code_generator is not None:
            logger.info("Unloading code generator")
            del self._code_generator
            self._code_generator = None

    def unload_all(self) -> None:
        """Unload all models to free memory."""
        logger.info("Unloading all models")
        self.unload_text_classifier()
        self.unload_security_classifier()
        self.unload_code_generator()

    def get_loaded_models(self) -> Dict[str, bool]:
        """
        Get status of loaded models.

        Returns:
            Dictionary with model loading status
        """
        return {
            'text_classifier': self.is_text_classifier_loaded(),
            'security_classifier': self.is_security_classifier_loaded(),
            'code_generator': self.is_code_generator_loaded()
        }

    def __str__(self) -> str:
        """String representation."""
        loaded = self.get_loaded_models()
        loaded_count = sum(loaded.values())
        return f"InferenceService({loaded_count}/3 models loaded)"

    def __repr__(self) -> str:
        """Detailed representation."""
        loaded = self.get_loaded_models()
        return (
            f"InferenceService("
            f"text_classifier={loaded['text_classifier']}, "
            f"security_classifier={loaded['security_classifier']}, "
            f"code_generator={loaded['code_generator']}, "
            f"device={self.device})"
        )
