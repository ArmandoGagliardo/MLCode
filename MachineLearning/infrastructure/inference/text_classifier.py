"""
Text Classifier
===============

Infrastructure component for text classification inference.

Supports:
- Multi-label text classification
- Batch processing
- Confidence scores
- Automatic device management

Example:
    >>> from infrastructure.inference import TextClassifier
    >>>
    >>> classifier = TextClassifier(model_path='models/text_classifier')
    >>> result = classifier.classify("def example(): pass")
    >>> print(f"Label: {result['label']}, Confidence: {result['confidence']:.2f}")
"""

import logging
from typing import Dict, List, Optional, Union
from pathlib import Path

import torch
import torch.nn.functional as F

from infrastructure.inference.model_loader import ModelLoader
from domain.exceptions import InferenceError

logger = logging.getLogger(__name__)


class TextClassifier:
    """
    Text classification inference.

    Provides text classification with confidence scores and batch processing.

    Attributes:
        model: Loaded classification model
        tokenizer: Loaded tokenizer
        device: Device for inference
        label_names: Optional mapping of label IDs to names

    Example:
        >>> classifier = TextClassifier('models/classifier')
        >>> result = classifier.classify("Sample text")
        >>> print(result['label'])
    """

    def __init__(
        self,
        model_path: str,
        label_names: Optional[List[str]] = None,
        device: Optional[str] = None,
        local_files_only: bool = True
    ):
        """
        Initialize TextClassifier.

        Args:
            model_path: Path to model checkpoint
            label_names: Optional list of label names (e.g., ['python', 'java', 'javascript'])
            device: Optional device override
            local_files_only: Whether to load only from local files

        Raises:
            InferenceError: If model loading fails
        """
        try:
            logger.info(f"Initializing TextClassifier from {model_path}")

            # Load model using ModelLoader
            loader = ModelLoader(device=device)
            self.model, self.tokenizer = loader.load_classification_model(
                model_path=model_path,
                local_files_only=local_files_only
            )

            self.device = loader.get_device()
            self.label_names = label_names
            self.num_labels = self.model.config.num_labels

            # Validate label_names if provided
            if label_names and len(label_names) != self.num_labels:
                raise InferenceError(
                    f"label_names length ({len(label_names)}) "
                    f"doesn't match model num_labels ({self.num_labels})"
                )

            logger.info(
                f"TextClassifier ready: {self.num_labels} labels, device={self.device}"
            )

        except Exception as e:
            raise InferenceError(f"Failed to initialize TextClassifier: {e}")

    def classify(
        self,
        text: str,
        return_confidence: bool = True,
        return_all_scores: bool = False
    ) -> Dict[str, Union[int, str, float, List[float]]]:
        """
        Classify single text.

        Args:
            text: Input text to classify
            return_confidence: Whether to return confidence score
            return_all_scores: Whether to return scores for all labels

        Returns:
            Dictionary with:
                - label: Predicted label ID
                - label_name: Label name (if label_names provided)
                - confidence: Confidence score (if return_confidence=True)
                - scores: All label scores (if return_all_scores=True)

        Example:
            >>> result = classifier.classify("def foo(): pass")
            >>> print(result)
            {'label': 0, 'label_name': 'python', 'confidence': 0.95}
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

            # Build result
            result = {
                'label': pred_label
            }

            if self.label_names:
                result['label_name'] = self.label_names[pred_label]

            if return_confidence:
                result['confidence'] = confidence

            if return_all_scores:
                result['scores'] = probs[0].cpu().tolist()

            return result

        except Exception as e:
            raise InferenceError(f"Classification failed: {e}")

    def classify_batch(
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

        Example:
            >>> texts = ["def foo(): pass", "public class Bar {}"]
            >>> results = classifier.classify_batch(texts)
            >>> for r in results:
            ...     print(f"{r['label_name']}: {r['confidence']:.2f}")
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
                    result = {
                        'label': label,
                        'confidence': conf
                    }
                    if self.label_names:
                        result['label_name'] = self.label_names[label]
                    results.append(result)

            except Exception as e:
                logger.error(f"Batch classification failed: {e}")
                # Add error results for failed batch
                for _ in batch:
                    results.append({
                        'label': -1,
                        'confidence': 0.0,
                        'error': str(e)
                    })

        return results

    def get_label_names(self) -> Optional[List[str]]:
        """Get label names if available."""
        return self.label_names

    def get_num_labels(self) -> int:
        """Get number of labels."""
        return self.num_labels

    def __str__(self) -> str:
        """String representation."""
        return f"TextClassifier(labels={self.num_labels}, device={self.device})"

    def __repr__(self) -> str:
        """Detailed representation."""
        return (
            f"TextClassifier(num_labels={self.num_labels}, "
            f"device='{self.device}', "
            f"has_label_names={self.label_names is not None})"
        )
