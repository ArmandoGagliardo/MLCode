"""
Inference Infrastructure
========================

Infrastructure layer components for model inference.

This module provides:
- ModelLoader: Load trained models from checkpoints
- TextClassifier: Text classification inference
- SecurityClassifier: Security-focused classification
- CodeGenerator: Code generation inference (seq2seq and causal models)
- GenerationConfig: Configuration for code generation parameters

Example:
    >>> from infrastructure.inference import TextClassifier
    >>>
    >>> classifier = TextClassifier(model_path='models/text_classifier')
    >>> result = classifier.classify("def example(): pass")
    >>> print(f"Classification: {result}")

    >>> from infrastructure.inference import CodeGenerator, GenerationConfig
    >>>
    >>> config = GenerationConfig(max_new_tokens=256, temperature=0.7)
    >>> generator = CodeGenerator(model_path='models/codegen', config=config)
    >>> code = generator.generate("function to sort an array")
    >>> print(code)
"""

from infrastructure.inference.model_loader import ModelLoader
from infrastructure.inference.text_classifier import TextClassifier
from infrastructure.inference.security_classifier import SecurityClassifier
from infrastructure.inference.code_generator import (
    CodeGenerator,
    GenerationConfig,
    ModelType
)

__all__ = [
    'ModelLoader',
    'TextClassifier',
    'SecurityClassifier',
    'CodeGenerator',
    'GenerationConfig',
    'ModelType',
]
