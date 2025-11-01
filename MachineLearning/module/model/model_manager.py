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

# Lazy import for transformers to avoid initialization issues
def get_transformers():
    try:
        from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, AutoModelForSequenceClassification
        return AutoTokenizer, AutoModelForSeq2SeqLM, AutoModelForSequenceClassification
    except Exception as e:
        logger.error(f"Error importing transformers: {e}")
        raise

class ModelManager:
    def __init__(self, task: str, model_name: str):
        self.task = task
        self.model_name = model_name
        if task == "security_classification":
            self.num_labels = 5
        else:
            self.num_labels = 2

        try:
            # Get transformers classes
            AutoTokenizer, AutoModelForSeq2SeqLM, AutoModelForSequenceClassification = get_transformers()
            
            # Initialize tokenizer
            logger.info(f"Loading tokenizer for model: {model_name}")
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            
            # Initialize model based on task
            logger.info(f"Loading model for task: {task}")
            if task == "code_generation":
                self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
            elif task in ["text_classification", "security_classification"]:
                self.model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=self.num_labels)
            
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
