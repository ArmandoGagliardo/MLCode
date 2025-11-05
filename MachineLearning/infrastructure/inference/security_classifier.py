"""
Security Classifier
===================

Infrastructure component for security-focused classification inference.

Supports:
- Security vulnerability detection
- Code pattern analysis
- Confidence scores
- Batch processing

Example:
    >>> from infrastructure.inference import SecurityClassifier
    >>>
    >>> classifier = SecurityClassifier(model_path='models/security_classifier')
    >>> result = classifier.classify("eval(user_input)")
    >>> if result['label_name'] == 'vulnerable':
    ...     print(f"Security issue detected: {result['confidence']:.2%}")
"""

import logging
from typing import Dict, List, Optional, Union

import torch
import torch.nn.functional as F

from infrastructure.inference.model_loader import ModelLoader
from domain.exceptions import InferenceError

logger = logging.getLogger(__name__)


class SecurityClassifier:
    """
    Security-focused classification inference.

    Specialized classifier for detecting security vulnerabilities and patterns
    in code.

    Attributes:
        model: Loaded classification model
        tokenizer: Loaded tokenizer
        device: Device for inference
        label_names: Mapping of label IDs to security categories

    Example:
        >>> classifier = SecurityClassifier('models/security')
        >>> result = classifier.classify("SELECT * FROM users WHERE id = " + user_id)
        >>> if result['is_vulnerable']:
        ...     print(f"SQL Injection risk: {result['confidence']:.2%}")
    """

    def __init__(
        self,
        model_path: str,
        label_names: Optional[List[str]] = None,
        device: Optional[str] = None,
        local_files_only: bool = True,
        vulnerability_threshold: float = 0.5
    ):
        """
        Initialize SecurityClassifier.

        Args:
            model_path: Path to model checkpoint
            label_names: Optional list of security label names
                        (e.g., ['safe', 'vulnerable', 'suspicious'])
            device: Optional device override
            local_files_only: Whether to load only from local files
            vulnerability_threshold: Confidence threshold for vulnerability detection

        Raises:
            InferenceError: If model loading fails
        """
        try:
            logger.info(f"Initializing SecurityClassifier from {model_path}")

            # Load model using ModelLoader
            loader = ModelLoader(device=device)
            self.model, self.tokenizer = loader.load_classification_model(
                model_path=model_path,
                local_files_only=local_files_only
            )

            self.device = loader.get_device()
            self.label_names = label_names
            self.num_labels = self.model.config.num_labels
            self.vulnerability_threshold = vulnerability_threshold

            # Validate label_names if provided
            if label_names and len(label_names) != self.num_labels:
                raise InferenceError(
                    f"label_names length ({len(label_names)}) "
                    f"doesn't match model num_labels ({self.num_labels})"
                )

            logger.info(
                f"SecurityClassifier ready: {self.num_labels} labels, "
                f"threshold={vulnerability_threshold}, device={self.device}"
            )

        except Exception as e:
            raise InferenceError(f"Failed to initialize SecurityClassifier: {e}")

    def classify(
        self,
        text: str,
        return_confidence: bool = True,
        return_all_scores: bool = False
    ) -> Dict[str, Union[int, str, float, bool, List[float]]]:
        """
        Classify code for security issues.

        Args:
            text: Input code to analyze
            return_confidence: Whether to return confidence score
            return_all_scores: Whether to return scores for all labels

        Returns:
            Dictionary with:
                - label: Predicted label ID
                - label_name: Security category (if label_names provided)
                - confidence: Confidence score (if return_confidence=True)
                - is_vulnerable: Boolean indicating if vulnerability detected
                - scores: All label scores (if return_all_scores=True)

        Example:
            >>> result = classifier.classify("os.system(user_input)")
            >>> if result['is_vulnerable']:
            ...     print(f"Command injection risk: {result['confidence']:.2%}")
        """
        try:
            # Tokenize
            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=512
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            # Inference
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits

            # Get prediction
            probs = F.softmax(logits, dim=-1)
            pred_label = torch.argmax(probs, dim=-1).item()
            confidence = probs[0, pred_label].item()

            # Determine vulnerability
            # Assumes label 0 = safe, label 1+ = vulnerable/suspicious
            is_vulnerable = self._is_vulnerable(pred_label, confidence)

            # Build result
            result = {
                'label': pred_label,
                'is_vulnerable': is_vulnerable
            }

            if self.label_names:
                result['label_name'] = self.label_names[pred_label]

            if return_confidence:
                result['confidence'] = confidence

            if return_all_scores:
                result['scores'] = probs[0].cpu().tolist()

            return result

        except Exception as e:
            raise InferenceError(f"Security classification failed: {e}")

    def classify_batch(
        self,
        texts: List[str],
        batch_size: int = 32
    ) -> List[Dict[str, Union[int, str, float, bool]]]:
        """
        Classify batch of code samples for security issues.

        Args:
            texts: List of code samples to analyze
            batch_size: Batch size for processing

        Returns:
            List of security classification results

        Example:
            >>> codes = [
            ...     "eval(user_input)",
            ...     "safe_function(validated_input)"
            ... ]
            >>> results = classifier.classify_batch(codes)
            >>> vulnerable = [r for r in results if r['is_vulnerable']]
            >>> print(f"{len(vulnerable)} vulnerable samples found")
        """
        results = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]

            try:
                # Tokenize batch
                inputs = self.tokenizer(
                    batch,
                    return_tensors="pt",
                    padding=True,
                    truncation=True,
                    max_length=512
                )
                inputs = {k: v.to(self.device) for k, v in inputs.items()}

                # Inference
                with torch.no_grad():
                    outputs = self.model(**inputs)
                    logits = outputs.logits

                # Get predictions
                probs = F.softmax(logits, dim=-1)
                pred_labels = torch.argmax(probs, dim=-1).cpu().tolist()
                confidences = probs.max(dim=-1).values.cpu().tolist()

                # Build results
                for label, conf in zip(pred_labels, confidences):
                    is_vulnerable = self._is_vulnerable(label, conf)

                    result = {
                        'label': label,
                        'confidence': conf,
                        'is_vulnerable': is_vulnerable
                    }
                    if self.label_names:
                        result['label_name'] = self.label_names[label]
                    results.append(result)

            except Exception as e:
                logger.error(f"Batch security classification failed: {e}")
                # Add error results for failed batch
                for _ in batch:
                    results.append({
                        'label': -1,
                        'confidence': 0.0,
                        'is_vulnerable': False,
                        'error': str(e)
                    })

        return results

    def filter_vulnerable(
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

        Example:
            >>> codes = ["safe_code()", "eval(user_input)", "normal_func()"]
            >>> vulnerable = classifier.filter_vulnerable(codes)
            >>> for v in vulnerable:
            ...     print(f"Index {v['index']}: {v['confidence']:.2%}")
        """
        results = self.classify_batch(texts, batch_size=batch_size)

        vulnerable = []
        for idx, (text, result) in enumerate(zip(texts, results)):
            if result.get('is_vulnerable', False):
                vulnerable.append({
                    'index': idx,
                    'text': text,
                    'label': result['label'],
                    'label_name': result.get('label_name'),
                    'confidence': result['confidence']
                })

        return vulnerable

    def _is_vulnerable(self, label: int, confidence: float) -> bool:
        """
        Determine if prediction indicates vulnerability.

        Default implementation:
        - label 0 = safe
        - label 1+ = vulnerable/suspicious (if confidence > threshold)

        Override this method for custom vulnerability logic.

        Args:
            label: Predicted label ID
            confidence: Prediction confidence

        Returns:
            True if vulnerable
        """
        if label == 0:
            return False
        return confidence >= self.vulnerability_threshold

    def set_threshold(self, threshold: float) -> None:
        """
        Update vulnerability threshold.

        Args:
            threshold: New threshold (0.0 to 1.0)

        Raises:
            ValueError: If threshold out of range
        """
        if not 0.0 <= threshold <= 1.0:
            raise ValueError(f"Threshold must be in [0, 1], got {threshold}")

        self.vulnerability_threshold = threshold
        logger.info(f"Vulnerability threshold updated to {threshold}")

    def get_threshold(self) -> float:
        """Get current vulnerability threshold."""
        return self.vulnerability_threshold

    def get_label_names(self) -> Optional[List[str]]:
        """Get label names if available."""
        return self.label_names

    def get_num_labels(self) -> int:
        """Get number of labels."""
        return self.num_labels

    def __str__(self) -> str:
        """String representation."""
        return (
            f"SecurityClassifier(labels={self.num_labels}, "
            f"threshold={self.vulnerability_threshold:.2f}, device={self.device})"
        )

    def __repr__(self) -> str:
        """Detailed representation."""
        return (
            f"SecurityClassifier(num_labels={self.num_labels}, "
            f"device='{self.device}', "
            f"threshold={self.vulnerability_threshold}, "
            f"has_label_names={self.label_names is not None})"
        )
