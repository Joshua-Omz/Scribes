"""
HuggingFace Text Generation Service

Singleton service for generating theological answers using LLMs.
Supports both HuggingFace Inference API and local model inference.
"""

import logging
import time
from typing import Dict, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential
from transformers import AutoTokenizer
from app.core.config import settings

logger = logging.getLogger(__name__)


class GenerationError(Exception):
    """Base exception for text generation failures."""
    pass


class ModelLoadError(GenerationError):
    """Failed to load model."""
    pass


class HFTextGenService:
    """
    Singleton service for HuggingFace text generation.
    
    Supports:
    - Local model inference (GPU/CPU)
    - HuggingFace Inference API
    - Automatic retry on transient failures
    - Token limit enforcement
    - Output validation
    """
    
    _instance = None
    _model = None
    _tokenizer = None
    _api_client = None
    
    def __new__(cls):
        """Singleton pattern - only one instance exists."""
        if cls._instance is None:
            cls._instance = super(HFTextGenService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize service based on config (API or local model)."""
        if self._initialized:
            return  # Already initialized
        
        self.model_name = settings.hf_generation_model
        self.use_api = settings.hf_use_api
        
        logger.info(
            f"Initializing HFTextGenService: mode={'API' if self.use_api else 'LOCAL'}, "
            f"model={self.model_name}"
        )
        
        try:
            if self.use_api:
                self._init_api_client()
            else:
                self._load_local_model()
            
            self._initialized = True
            logger.info("HFTextGenService initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize text generation service: {e}", exc_info=True)
            raise ModelLoadError(f"Service initialization failed: {str(e)}")
    
    def _init_api_client(self):
        """Initialize HuggingFace Inference API client."""
        from huggingface_hub import InferenceClient
        
        if not settings.huggingface_api_key:
            raise ValueError(
                "HF_API_KEY not set in environment. "
                "Get token from https://huggingface.co/settings/tokens"
            )
        
        self._api_client = InferenceClient(
            model=self.model_name,
            token=settings.huggingface_api_key,
            timeout=settings.hf_generation_timeout
        )
        
        logger.info(f"HF Inference API client initialized for {self.model_name}")
    
    def _load_local_model(self):
        """Load model locally to GPU/CPU (for production with GPU)."""
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            import torch
            
            logger.info(f"Loading local model: {self.model_name} (this may take 30-60s)")
            
            # Load tokenizer
            self._tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=True
            )
            
            # Load model with auto device mapping
            model_kwargs = {
                "trust_remote_code": True,
                "low_cpu_mem_usage": True
            }
            
            if torch.cuda.is_available():
                model_kwargs["device_map"] = "auto"  # Auto-distribute to GPUs
                logger.info(f"Using GPU: {torch.cuda.get_device_name(0)}")
            else:
                model_kwargs["device_map"] = "cpu"
                logger.warning("No GPU detected - using CPU (generation will be slow)")
            
            self._model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                **model_kwargs
            )
            
            self._model.eval()  # Set to evaluation mode
            
            logger.info(f"Model loaded on device: {next(self._model.parameters()).device}")
            
        except Exception as e:
            logger.error(f"Failed to load local model: {e}", exc_info=True)
            raise ModelLoadError(f"Local model loading failed: {str(e)}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    def generate(
        self,
        prompt: str,
        max_new_tokens: int = None,
        temperature: float = None,
        top_p: float = None,
        repetition_penalty: float = None
    ) -> str:
        """
        Generate text from prompt.
        
        Args:
            prompt: Full assembled prompt (system + context + query)
            max_new_tokens: Max tokens to generate (default from config: 400)
            temperature: Randomness 0-1 (default: 0.2 for factual)
            top_p: Nucleus sampling (default: 0.9)
            repetition_penalty: Penalty for repetition (default: 1.1)
        
        Returns:
            Generated answer text (cleaned, no prompt echo)
        
        Raises:
            GenerationError: If generation fails after retries
        """
        # Use config defaults if not specified
        max_new_tokens = max_new_tokens or settings.assistant_max_output_tokens
        temperature = temperature or settings.hf_generation_temperature
        top_p = top_p or settings.assistant_model_top_p
        repetition_penalty = repetition_penalty or settings.assistant_model_repition_penalty
        
        # Validate inputs
        if not prompt or not prompt.strip():
            raise GenerationError("Cannot generate from empty prompt")
        
        logger.info(
            f"Generating answer: max_tokens={max_new_tokens}, temp={temperature}, "
            f"mode={'API' if self.use_api else 'LOCAL'}"
        )
        
        start_time = time.perf_counter()
        #this is where the stuff actually happens
        try:
            if self.use_api:
                answer = self._generate_api(prompt, max_new_tokens, temperature, top_p, repetition_penalty)
            else:
                answer = self._generate_local(prompt, max_new_tokens, temperature, top_p, repetition_penalty)
            
            # Validate output
            if not self._validate_output(answer):
                raise GenerationError("Generated output failed validation (too short or repetitive)")
            
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            logger.info(
                f"Generation successful: {len(answer)} chars, {duration_ms:.0f}ms",
                extra={
                    "duration_ms": duration_ms,
                    "output_length": len(answer),
                    "status": "success"
                }
            )
            
            return answer.strip()
            
        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                f"Generation failed after {duration_ms:.0f}ms: {e}",
                extra={
                    "duration_ms": duration_ms,
                    "error": str(e),
                    "status": "error"
                }
            )
            raise GenerationError(f"Text generation failed: {str(e)}")
    
    def _generate_api(
        self,
        prompt: str,
        max_new_tokens: int,
        temperature: float,
        top_p: float,
        repetition_penalty: float
    ) -> str:
        """Generate using HuggingFace Inference API."""
        try:
            response = self._api_client.text_generation(
                prompt,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=top_p,
                repetition_penalty=repetition_penalty,
                return_full_text=False  # Don't echo the prompt
            )
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"HF API generation failed: {e}", exc_info=True)
            raise GenerationError(f"API call failed: {str(e)}")
    
    def _generate_local(
        self,
        prompt: str,
        max_new_tokens: int,
        temperature: float,
        top_p: float,
        repetition_penalty: float
    ) -> str:
        """Generate using local model (GPU/CPU)."""
        try:
            import torch
            
            # Tokenize input
            inputs = self._tokenizer(
                prompt,
                return_tensors="pt",
                truncation=True,
                max_length=settings.assistant_model_context_window - max_new_tokens
            ).to(self._model.device)
            
            # Generation config
            gen_config = {
                "max_new_tokens": max_new_tokens,
                "temperature": temperature,
                "top_p": top_p,
                "repetition_penalty": repetition_penalty,
                "do_sample": temperature > 0,  # Greedy decoding if temp=0
                "pad_token_id": self._tokenizer.eos_token_id,
                "eos_token_id": self._tokenizer.eos_token_id
            }
            
            # Generate (no gradient computation needed)
            with torch.no_grad():
                outputs = self._model.generate(**inputs, **gen_config)
            
            # Decode (skip the input prompt tokens)
            generated_text = self._tokenizer.decode(
                outputs[0][inputs["input_ids"].shape[1]:],  # Only new tokens
                skip_special_tokens=True
            )
            
            return generated_text.strip()
            
        except torch.cuda.OutOfMemoryError:
            logger.error("GPU out of memory during generation")
            # Clear GPU cache
            if hasattr(torch, 'cuda'):
                torch.cuda.empty_cache()
            raise GenerationError("GPU out of memory - consider using API mode or smaller model")
            
        except Exception as e:
            logger.error(f"Local generation failed: {e}", exc_info=True)
            raise GenerationError(f"Local inference error: {str(e)}")
    
    def _validate_output(self, text: str) -> bool:
        """
        Validate generated output quality.
        
        Checks:
        - Not empty
        - Minimum length (20 chars)
        - Not excessively repetitive
        """
        if not text or len(text.strip()) < 20:
            logger.warning("Generated text too short")
            return False
        
        # Check for extreme repetition (basic heuristic)
        words = text.split()
        if len(words) > 10:
            # Check if more than 50% of 3-word sequences are unique
            trigrams = set(tuple(words[i:i+3]) for i in range(len(words)-2))
            if len(trigrams) < len(words) * 0.3:
                logger.warning("Generated text appears highly repetitive")
                return False
        
        return True
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model configuration."""
        return {
            "model_name": self.model_name,
            "mode": "api" if self.use_api else "local",
            "max_output_tokens": settings.assistant_max_output_tokens,
            "temperature": settings.hf_generation_temperature,
            "initialized": self._initialized
        }


# Global singleton instance
_textgen_service_instance = None


def get_textgen_service() -> HFTextGenService:
    """
    Get or create global HFTextGenService instance.
    
    Returns:
        HFTextGenService singleton
    """
    global _textgen_service_instance
    if _textgen_service_instance is None:
        _textgen_service_instance = HFTextGenService()
    return _textgen_service_instance