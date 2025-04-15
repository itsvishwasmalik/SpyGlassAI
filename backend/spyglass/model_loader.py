import os
import torch
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForCausalLM
import psutil

class ModelLoader:
    def __init__(self, cache_dir="model_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.model = None
        self.tokenizer = None
        self.model_id = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
        
        # Force CPU mode due to memory constraints
        self.device = "cpu"
        print(f"[INFO] Using device: {self.device}")
        
        # Check available memory
        memory = psutil.virtual_memory()
        self.available_memory_gb = round(memory.available / (2**30))
        print(f"[INFO] Available memory: {self.available_memory_gb} GB")
        
    def load_model(self):
        """Load model and tokenizer if not already loaded"""
        if self.model is None:
            print(f"[INFO] Loading model: {self.model_id}")
            
            try:
                # Load tokenizer
                self.tokenizer = AutoTokenizer.from_pretrained(
                    self.model_id,
                    cache_dir=str(self.cache_dir)
                )
                
                # Load model with memory optimization for small model
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_id,
                    torch_dtype=torch.float32,
                    low_cpu_mem_usage=True,
                    cache_dir=str(self.cache_dir)
                )
                
                print("[INFO] Model loaded successfully")
                
            except Exception as e:
                print(f"[ERROR] Failed to load model: {str(e)}")
                raise
        
        return self.model, self.tokenizer
    
    def get_model(self):
        """Get the loaded model and tokenizer"""
        return self.load_model()

# Singleton instance
_model_loader = None

def get_model_loader(cache_dir="model_cache"):
    """Get or create the ModelLoader singleton instance"""
    global _model_loader
    if _model_loader is None:
        _model_loader = ModelLoader(cache_dir)
    return _model_loader