# 📁 model_manager.py

import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Hugging Face cache and timeout settings
import os
os.environ['HF_HOME'] = os.path.join(os.path.expanduser("~"), ".cache", "huggingface")
os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = "1"
os.environ['HF_HUB_DOWNLOAD_TIMEOUT'] = "500"

# Try importing required packages
try:
    import numpy as np
    logger.info("NumPy imported successfully")
except ImportError as e:
    logger.error(f"Error importing NumPy: {e}")
    raise

try:
    import torch
    logger.info("PyTorch imported successfully")
except ImportError as e:
    logger.error(f"Error importing PyTorch: {e}")
    raise

# Default model mappings
DEFAULT_MODELS = {
    "text_classification": "microsoft/codebert-base",
    "code_generation": "Salesforce/codegen-350M-mono",  # Model specifically trained for code generation
    "security_classification": "microsoft/codebert-base"
}

# Lazy import for transformers to avoid initialization issues
def get_transformers():
    try:
        from transformers import (
            AutoTokenizer,
            AutoModelForSeq2SeqLM,
            AutoModelForSequenceClassification,
            AutoModelForCausalLM
        )
        return AutoTokenizer, AutoModelForSeq2SeqLM, AutoModelForSequenceClassification, AutoModelForCausalLM
    except Exception as e:
        logger.error(f"Error importing transformers: {e}")
        raise

class ModelManager:
    def __init__(self, task: str, model_name: str = None):
        """
        Inizializza il model manager.
        
        Args:
            task: Tipo di task (text_classification, code_generation, security_classification)
            model_name: Nome del modello da utilizzare. Se None, usa il modello di default per il task.
        """
        self.task = task
        self.model_name = model_name or DEFAULT_MODELS.get(task)
        
        if not self.model_name:
            raise ValueError(f"Task non supportato: {task}")
            
        if task == "security_classification":
            self.num_labels = 5
        else:
            self.num_labels = 2

        try:
            # Get transformers classes
            AutoTokenizer, AutoModelForSeq2SeqLM, AutoModelForSequenceClassification, AutoModelForCausalLM = get_transformers()
            
            # Initialize tokenizer
            logger.info(f"Loading tokenizer for model: {self.model_name}")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            
            # Initialize model based on task
            logger.info(f"Loading model for task: {task}")
            
            if task == "code_generation":
                if "codegen" in self.model_name.lower():
                    self.model = AutoModelForCausalLM.from_pretrained(
                        self.model_name,
                        trust_remote_code=True,
                        pad_token_id=self.tokenizer.eos_token_id
                    )
                elif "bart" in self.model_name.lower():
                    self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name)
                else:
                    self.model = AutoModelForCausalLM.from_pretrained(
                        self.model_name,
                        trust_remote_code=True
                    )
            elif task in ["text_classification", "security_classification"]:
                self.model = AutoModelForSequenceClassification.from_pretrained(
                    self.model_name,
                    num_labels=self.num_labels
                )
            
            logger.info("Model and tokenizer loaded successfully")
            
            # Move model to appropriate device
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            self.model.to(self.device)
            logger.info(f"Model moved to device: {self.device}")
            
        except Exception as e:
            logger.error(f"Error initializing model: {e}")
            raise
        
        if task not in ["code_generation", "text_classification", "security_classification"]:
            raise ValueError(f"Task non supportato: {task}")

    def get_model(self):
        return self.model

    def get_tokenizer(self):
        return self.tokenizer
        
    def is_seq2seq_model(self):
        """Check if the current model is a sequence-to-sequence model"""
        return "bart" in self.model_name.lower()
        
    def is_causal_model(self):
        """Check if the current model is a causal language model"""
        return not self.is_seq2seq_model() and self.task == "code_generation"
        
    def is_classification_model(self):
        """Check if the current model is a classification model"""
        return self.task in ["text_classification", "security_classification"]
        
    def get_model_type(self):
        """Get the type of the current model"""
        if self.is_seq2seq_model():
            return "seq2seq"
        elif self.is_causal_model():
            return "causal"
        else:
            return "classification"

    def prepare_input_for_generation(self, text):
        """Prepare input for code generation based on model type"""
        if self.task == "code_generation":
            # Add a code generation prompt template
            if "python" in text.lower():
                prompt = f"# Python function\n# Input: {text}\n\ndef"
            else:
                prompt = f"# Task: {text}\n\ndef"
        else:
            prompt = text
            
        inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, padding=True)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        return inputs
            
    def generate_code(self, text, max_length=256, num_return_sequences=1, temperature=0.2):
        """
        Generate code based on input text using the appropriate generation strategy.

        Args:
            text (str): Input text to generate code from
            max_length (int): Maximum length of generated sequence
            num_return_sequences (int): Number of different sequences to generate
            temperature (float): Temperature parameter for sampling (higher = more random)

        Returns:
            list: List of generated code sequences
        """
        try:
            inputs = self.prepare_input_for_generation(text)
            
            generation_config = {
                "max_length": max_length,
                "num_return_sequences": num_return_sequences,
                "temperature": temperature,
                "do_sample": True,
                "pad_token_id": self.tokenizer.eos_token_id,
                "eos_token_id": self.tokenizer.eos_token_id,
                "top_p": 0.95,
                "top_k": 50,
                "repetition_penalty": 1.1,
                "length_penalty": 1.0,
                "num_beams": 5
            }
            
            if self.is_seq2seq_model():
                # Add seq2seq specific parameters
                generation_config.update({
                    "early_stopping": True,
                    "no_repeat_ngram_size": 2,
                    "length_penalty": 1.0,
                    "num_beams": 4
                })
            else:
                # Causal model specific parameters
                generation_config.update({
                    "top_p": 0.95,
                    "top_k": 50,
                    "repetition_penalty": 1.2
                })
            
            # Generate sequences
            outputs = self.model.generate(**inputs, **generation_config)
            decoded_outputs = self.tokenizer.batch_decode(outputs, skip_special_tokens=True)
            
            return decoded_outputs
            
        except Exception as e:
            logger.error(f"Failed to generate code: {e}")
            raise

    def classify_text(self, text):
        """
        Classify text using the classification model.

        Args:
            text (str): Input text to classify

        Returns:
            dict: Classification results with predicted label and probabilities
        """
        if not self.is_classification_model():
            raise ValueError("This model is not configured for classification tasks")

        try:
            # Prepare input
            inputs = self.prepare_input_for_generation(text)
            
            # Get model prediction
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits
                probs = torch.nn.functional.softmax(logits, dim=-1)

            # Get predicted class and probabilities
            predicted_class = torch.argmax(probs, dim=-1).item()
            class_probs = probs[0].cpu().numpy().tolist()

            return {
                "predicted_class": predicted_class,
                "probabilities": class_probs
            }

        except Exception as e:
            logger.error(f"Failed to classify text: {e}")
            raise
