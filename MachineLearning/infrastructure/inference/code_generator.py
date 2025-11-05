"""
Code Generator
==============

Infrastructure component for code generation inference.

Supports:
- Sequence-to-sequence models (T5, BART)
- Causal language models (GPT, CodeGen)
- Configurable generation parameters
- Batch generation

Example:
    >>> from infrastructure.inference import CodeGenerator
    >>>
    >>> generator = CodeGenerator(model_path='models/codegen', model_type='seq2seq')
    >>> code = generator.generate("create a function that calculates fibonacci")
    >>> print(code)
"""

import logging
from typing import Dict, List, Optional, Union
from enum import Enum

import torch

from infrastructure.inference.model_loader import ModelLoader
from domain.exceptions import InferenceError

logger = logging.getLogger(__name__)


class ModelType(Enum):
    """Supported model types for code generation."""
    SEQ2SEQ = "seq2seq"
    CAUSAL = "causal"


class GenerationConfig:
    """
    Configuration for code generation.

    Attributes:
        max_new_tokens: Maximum tokens to generate
        do_sample: Whether to use sampling (vs greedy)
        temperature: Sampling temperature (0.0 to 2.0)
        top_p: Nucleus sampling parameter
        top_k: Top-k sampling parameter
        num_beams: Number of beams for beam search
        num_return_sequences: Number of sequences to generate
        early_stopping: Whether to stop when all beams finish
    """

    def __init__(
        self,
        max_new_tokens: int = 128,
        do_sample: bool = True,
        temperature: float = 0.8,
        top_p: float = 0.95,
        top_k: int = 50,
        num_beams: int = 5,
        num_return_sequences: int = 1,
        early_stopping: bool = True
    ):
        self.max_new_tokens = max_new_tokens
        self.do_sample = do_sample
        self.temperature = temperature
        self.top_p = top_p
        self.top_k = top_k
        self.num_beams = num_beams
        self.num_return_sequences = num_return_sequences
        self.early_stopping = early_stopping

    def to_dict(self) -> Dict:
        """Convert to dictionary for model.generate()."""
        return {
            'max_new_tokens': self.max_new_tokens,
            'do_sample': self.do_sample,
            'temperature': self.temperature,
            'top_p': self.top_p,
            'top_k': self.top_k,
            'num_beams': self.num_beams,
            'num_return_sequences': self.num_return_sequences,
            'early_stopping': self.early_stopping
        }


class CodeGenerator:
    """
    Code generation inference.

    Supports both sequence-to-sequence and causal language models for
    generating code from natural language prompts.

    Attributes:
        model: Loaded generation model
        tokenizer: Loaded tokenizer
        device: Device for inference
        model_type: Type of model (seq2seq or causal)
        config: Generation configuration

    Example:
        >>> config = GenerationConfig(max_new_tokens=256, temperature=0.7)
        >>> generator = CodeGenerator('models/codegen', config=config)
        >>> code = generator.generate("create a binary search function")
    """

    def __init__(
        self,
        model_path: str,
        model_type: Union[str, ModelType] = ModelType.SEQ2SEQ,
        config: Optional[GenerationConfig] = None,
        device: Optional[str] = None,
        local_files_only: bool = False
    ):
        """
        Initialize CodeGenerator.

        Args:
            model_path: Path to model checkpoint or HuggingFace model ID
            model_type: Type of model ('seq2seq' or 'causal')
            config: Generation configuration (uses defaults if None)
            device: Optional device override
            local_files_only: Whether to load only from local files

        Raises:
            InferenceError: If model loading fails
        """
        try:
            logger.info(f"Initializing CodeGenerator from {model_path}")

            # Parse model type
            if isinstance(model_type, str):
                model_type = ModelType(model_type.lower())
            self.model_type = model_type

            # Load model using ModelLoader
            loader = ModelLoader(device=device)

            if model_type == ModelType.SEQ2SEQ:
                self.model, self.tokenizer = loader.load_seq2seq_model(
                    model_path=model_path,
                    local_files_only=local_files_only
                )
            elif model_type == ModelType.CAUSAL:
                self.model, self.tokenizer = loader.load_causal_model(
                    model_path=model_path,
                    local_files_only=local_files_only
                )
            else:
                raise InferenceError(f"Unsupported model_type: {model_type}")

            self.device = loader.get_device()
            self.config = config or GenerationConfig()

            logger.info(
                f"CodeGenerator ready: {model_type.value} model, "
                f"device={self.device}"
            )

        except Exception as e:
            raise InferenceError(f"Failed to initialize CodeGenerator: {e}")

    def generate(
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

        Example:
            >>> code = generator.generate("function to reverse a string")
            >>> print(code)
        """
        try:
            gen_config = config or self.config

            # Tokenize input
            inputs = self.tokenizer(
                prompt,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=512
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            # Generate
            with torch.no_grad():
                outputs = self.model.generate(
                    input_ids=inputs['input_ids'],
                    attention_mask=inputs['attention_mask'],
                    **gen_config.to_dict()
                )

            # Decode
            generated = self.tokenizer.decode(
                outputs[0],
                skip_special_tokens=True
            ).strip()

            return generated

        except Exception as e:
            raise InferenceError(f"Code generation failed: {e}")

    def generate_batch(
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

        Example:
            >>> prompts = [
            ...     "function to sort array",
            ...     "class for binary tree"
            ... ]
            >>> codes = generator.generate_batch(prompts)
        """
        gen_config = config or self.config
        results = []

        for i in range(0, len(prompts), batch_size):
            batch = prompts[i:i + batch_size]

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

                # Generate
                with torch.no_grad():
                    outputs = self.model.generate(
                        input_ids=inputs['input_ids'],
                        attention_mask=inputs['attention_mask'],
                        **gen_config.to_dict()
                    )

                # Decode all outputs
                for output in outputs:
                    generated = self.tokenizer.decode(
                        output,
                        skip_special_tokens=True
                    ).strip()
                    results.append(generated)

            except Exception as e:
                logger.error(f"Batch generation failed: {e}")
                # Add error placeholders
                for _ in batch:
                    results.append(f"# Error: {e}")

        return results

    def generate_multiple(
        self,
        prompt: str,
        num_sequences: int = 3,
        config: Optional[GenerationConfig] = None
    ) -> List[str]:
        """
        Generate multiple code variations for single prompt.

        Args:
            prompt: Input prompt
            num_sequences: Number of variations to generate
            config: Optional generation config override

        Returns:
            List of generated code strings

        Example:
            >>> codes = generator.generate_multiple(
            ...     "function to calculate factorial",
            ...     num_sequences=3
            ... )
            >>> for i, code in enumerate(codes, 1):
            ...     print(f"Variation {i}:\\n{code}\\n")
        """
        # Create config with num_return_sequences
        gen_config = config or self.config
        multi_config = GenerationConfig(
            max_new_tokens=gen_config.max_new_tokens,
            do_sample=True,  # Force sampling for diversity
            temperature=gen_config.temperature,
            top_p=gen_config.top_p,
            top_k=gen_config.top_k,
            num_beams=max(gen_config.num_beams, num_sequences),
            num_return_sequences=num_sequences,
            early_stopping=gen_config.early_stopping
        )

        try:
            # Tokenize
            inputs = self.tokenizer(
                prompt,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=512
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            # Generate multiple sequences
            with torch.no_grad():
                outputs = self.model.generate(
                    input_ids=inputs['input_ids'],
                    attention_mask=inputs['attention_mask'],
                    **multi_config.to_dict()
                )

            # Decode all
            results = []
            for output in outputs:
                generated = self.tokenizer.decode(
                    output,
                    skip_special_tokens=True
                ).strip()
                results.append(generated)

            return results

        except Exception as e:
            raise InferenceError(f"Multiple sequence generation failed: {e}")

    def set_config(self, config: GenerationConfig) -> None:
        """
        Update generation configuration.

        Args:
            config: New generation configuration
        """
        self.config = config
        logger.info(f"Generation config updated: {config.to_dict()}")

    def get_config(self) -> GenerationConfig:
        """Get current generation configuration."""
        return self.config

    def get_model_type(self) -> ModelType:
        """Get model type."""
        return self.model_type

    def __str__(self) -> str:
        """String representation."""
        return (
            f"CodeGenerator(type={self.model_type.value}, "
            f"device={self.device})"
        )

    def __repr__(self) -> str:
        """Detailed representation."""
        return (
            f"CodeGenerator(model_type='{self.model_type.value}', "
            f"device='{self.device}', "
            f"max_new_tokens={self.config.max_new_tokens})"
        )
