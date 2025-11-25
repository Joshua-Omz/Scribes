"""
Hugging Face text generation service.

🔴 SAFETY-CRITICAL: YOU MUST IMPLEMENT THIS

This service handles text generation with:
- Model loading (local or API)
- Generation with safety controls
- Timeout handling
- Output filtering
- Fallback strategies

Key responsibilities:
- Load HF model with proper config
- Generate text with token limits
- Handle OOM errors gracefully
- Filter unsafe outputs
- Log metrics (latency, tokens)

Implementation decisions YOU must make:
1. Local model vs. HF Inference API?
2. Quantization settings (4-bit, 8-bit for local)?
3. Temperature and sampling parameters?
4. Content moderation strategy?
5. Fallback model if OOM?
6. Hardware requirements documentation?

DO NOT implement until you've tested model loading!
"""

from typing import Optional, Dict, Any
import logging
import asyncio

from app.core.config import settings

logger = logging.getLogger(__name__)


class HFTextGenService:
    """
    Service for text generation using Hugging Face models.
    
    ⚠️  PLACEHOLDER - YOU MUST IMPLEMENT THIS WITH SAFETY IN MIND
    """
    
    def __init__(self):
        """Initialize text generation service."""
        self.model_name = settings.hf_generation_model
        self.use_api = settings.hf_use_api
        self.temperature = settings.hf_generation_temperature
        self.timeout = settings.hf_generation_timeout
        self._model = None
        self._tokenizer = None
        logger.warning("HFTextGenService initialized - PLACEHOLDER ONLY")
    
    async def generate(
        self,
        prompt: str,
        max_new_tokens: int = 400,
        temperature: Optional[float] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate text from prompt.
        
        ⚠️  YOU MUST IMPLEMENT THIS
        
        Safety requirements:
        - MUST enforce max_new_tokens limit
        - MUST implement timeout
        - MUST handle OOM errors
        - SHOULD filter unsafe outputs
        - SHOULD log generation metrics
        
        Args:
            prompt: Full assembled prompt
            max_new_tokens: Maximum tokens to generate
            temperature: Sampling temperature (overrides config)
            **kwargs: Additional generation params
            
        Returns:
            Dictionary with structure:
            {
                "generated_text": str (only the new text, not prompt),
                "tokens_generated": int,
                "latency_ms": int,
                "model_name": str,
                "truncated": bool (if hit max_tokens)
            }
            
        Raises:
            TimeoutError: If generation exceeds timeout
            RuntimeError: If OOM or other model error
        """
        raise NotImplementedError(
            "HFTextGenService.generate() MUST be implemented by YOU. "
            "This is safety-critical - test model loading first!"
        )
    
    def load_model(self):
        """
        Load the generation model.
        
        ⚠️  YOU MUST IMPLEMENT THIS
        
        Considerations:
        - Local: transformers.AutoModelForCausalLM
        - Quantization: use bitsandbytes (4-bit/8-bit)
        - API: use huggingface_hub.InferenceClient
        - Device placement (GPU/CPU)
        - Memory management
        
        Should be called during app startup or lazy-loaded.
        """
        raise NotImplementedError("Model loading not implemented")
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check if model is loaded and ready.
        
        Returns:
            Status dict with model info
        """
        raise NotImplementedError("Health check not implemented")


# Singleton
_textgen_service = None


def get_textgen_service() -> HFTextGenService:
    """Get or create text generation service singleton."""
    global _textgen_service
    if _textgen_service is None:
        _textgen_service = HFTextGenService()
    return _textgen_service

