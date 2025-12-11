# HF Text Generation Service — Complete Guide

**Project:** Scribes AI Assistant (Phase 6)  
**Component:** Hugging Face Text Generation Service  
**Owner:** Joshua  
**Created:** December 5, 2025  
**Last Updated:** December 9, 2025  
**Status:** Ready for Implementation

---

## 📖 Document Structure

This document has **2 tiers** for different use cases:

### **🚀 TIER 1: IMPLEMENTATION GUIDE** (Sections 1-8)
**Use this for:** Daily coding, quick reference, copy-paste implementation
- Compact, code-first, tactical
- Everything you need to build the service TODAY
- ~2000 words

### **📚 TIER 2: REFERENCE ARCHITECTURE** (Sections 9-19)
**Use this for:** Deep dives, production hardening, team onboarding, future scaling
- Detailed explanations, optimizations, deployment strategies
- Reference when you need depth
- ~5000 words

**💡 Tip:** Start with Tier 1, reference Tier 2 only when needed.

---

# 🚀 TIER 1: IMPLEMENTATION GUIDE

---

## 1. What This Service Does (Core Purpose)

The **HF Text Generation Service** is the **brain** of Scribes' AI Assistant. It:

1. **Receives a fully-assembled prompt** from PromptEngine (system + context + user query)
2. **Generates a theological answer** using HuggingFace models (local or API)
3. **Returns clean text** with metadata (tokens, latency, citations)

**Critical Requirements:**
- ✅ Never hallucinate scripture - only use RAG context
- ✅ Stay within strict token limits (400 tokens max output)
- ✅ Complete generation in <5 seconds (p95)
- ✅ Handle both local GPU inference and HF API calls
- ✅ Graceful degradation on failures

---

## 2. Position in RAG Pipeline (Where It Fits)

```plaintext
User Query
    ↓
[1] TokenizerService → validate query tokens
[2] EmbeddingService → query → vector
[3] RetrievalService → fetch top-K chunks (pgvector)
[4] ContextBuilder → select chunks within 1200 token budget
[5] PromptEngine → assemble final prompt
    ↓
[6] 🔥 HFTextGenService → GENERATE ANSWER (YOU ARE HERE)
    ↓
[7] PostProcessor → clean output, extract citations
[8] Return to user
```

**Your Input:** Fully-assembled prompt (system + context + query)  
**Your Output:** Generated answer string  
**Your Constraints:** Max 400 tokens, <5s latency, no hallucinations

---

## 3. Architecture Patterns (Follow These)

This service **MUST** match Scribes' existing patterns:

| Pattern | Why | Implementation |
|---------|-----|----------------|
| **Singleton** | Only one model loaded in memory | `_instance = None` + `__new__()` |
| **Lazy Loading** | Load model only when first used | `@property` for model access |
| **Config-Driven** | All settings from `.env` | Use `settings.hf_generation_model` |
| **Retry Logic** | Handle transient API failures | `@retry` from `tenacity` |
| **Structured Logging** | Observability | `logger.info()` with `extra={}` |
| **Custom Exceptions** | Clear error handling | `GenerationError`, `ModelLoadError` |

**Examples in codebase:** `EmbeddingService`, `TokenizerService`, `RetrievalService`

---

## 4. Quick Setup (What You Need)

### 4.1 Config Settings (Already in `config.py` ✅)

```python
# app/core/config.py
hf_api_key: str = ""  # Get from huggingface.co/settings/tokens
hf_generation_model: str = "meta-llama/Llama-2-7b-chat-hf"
hf_use_api: bool = True  # Start with API (simpler), switch to local later
hf_generation_temperature: float = 0.2  # Low = deterministic, factual
hf_generation_timeout: int = 30  # Max 30s per generation
assistant_max_output_tokens: int = 400  # Never exceed
```

### 4.2 Environment Variables (Add to `.env`)

```bash
HF_API_KEY=hf_your_token_here_from_huggingface
HF_USE_API=true  # Start with API mode (no GPU needed)
```

### 4.3 Dependencies (Add to `requirements.txt`)

```plaintext
# Already have:
transformers>=4.35.0
torch>=2.0.0
tenacity==8.2.3

# Need to ADD:
huggingface_hub>=0.20.0  # For API client
```

Install:
```powershell
pip install huggingface_hub
```

---

## 5. Service Implementation (Copy-Paste Ready)

### 5.1 File: `app/services/hf_textgen_service.py`

```python
"""
HuggingFace Text Generation Service for Scribes AI Assistant.

Generates pastoral answers from prompts using either local models or HF Inference API.
Implements singleton pattern, retry logic, and strict token budgeting.
"""

import logging
import time
from typing import Optional, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential

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
        
        if not settings.hf_api_key:
            raise ValueError(
                "HF_API_KEY not set in environment. "
                "Get token from https://huggingface.co/settings/tokens"
            )
        
        self._api_client = InferenceClient(
            model=self.model_name,
            token=settings.hf_api_key,
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
```

---

## 6. Integration with AssistantService

### How to Use in `app/services/assistant_service.py`

```python
from app.services.hf_textgen_service import get_textgen_service, GenerationError

class AssistantService:
    def __init__(self):
        # ... other services ...
        self.textgen = get_textgen_service()  # Singleton - loads once
    
    async def query(self, user_query: str, user_id: int, db: AsyncSession):
        # ... steps 1-5: tokenize, embed, retrieve, build context, assemble prompt ...
        
        # Step 6: Generate answer
        try:
            final_prompt = self.prompt_engine.build(context, user_query)
            
            answer = self.textgen.generate(
                prompt=final_prompt,
                max_new_tokens=400,  # Strict limit
                temperature=0.2  # Low temp for factual, pastoral tone
            )
            
            # Validate answer
            if not answer or len(answer) < 20:
                raise ValueError("Generated answer too short")
            
            logger.info(f"Generated answer: {len(answer)} chars")
            
        except GenerationError as e:
            logger.error(f"Generation failed: {e}")
            return {
                "answer": "I'm having trouble generating a response right now. Please try again in a moment.",
                "sources": [],
                "error": str(e),
                "status": "generation_failed"
            }
        
        # Step 7: Extract citations, format response
        return {
            "answer": answer,
            "sources": self._extract_sources(context),
            "metadata": {...}
        }
```

---

## 7. Testing Strategy

### 7.1 Unit Test (`tests/test_hf_textgen_service.py`)

```python
import pytest
from app.services.hf_textgen_service import HFTextGenService, GenerationError, get_textgen_service

def test_service_singleton():
    """Verify singleton pattern works."""
    service1 = get_textgen_service()
    service2 = get_textgen_service()
    assert service1 is service2  # Same instance

def test_get_model_info():
    """Test model info retrieval."""
    service = get_textgen_service()
    info = service.get_model_info()
    
    assert "model_name" in info
    assert "mode" in info
    assert info["initialized"] is True

def test_generate_basic():
    """Test basic generation."""
    service = get_textgen_service()
    
    prompt = "What is faith according to the Bible?"
    result = service.generate(prompt, max_new_tokens=50)
    
    assert result
    assert len(result) > 10
    assert isinstance(result, str)

def test_empty_prompt_raises_error():
    """Test empty prompt handling."""
    service = get_textgen_service()
    
    with pytest.raises(GenerationError):
        service.generate("", max_new_tokens=10)

def test_generation_respects_token_limit():
    """Test that output doesn't wildly exceed token limit."""
    service = get_textgen_service()
    
    prompt = "Explain the concept of grace in Christianity."
    result = service.generate(prompt, max_new_tokens=100)
    
    # Rough check: shouldn't be more than 2x the token limit in characters
    # (1 token ≈ 4 chars for English)
    assert len(result) < 100 * 4 * 2  # 800 chars max
```

### 7.2 Quick Manual Test

```python
# In Python shell or Jupyter:
from app.services.hf_textgen_service import get_textgen_service

service = get_textgen_service()

# Test 1: Simple generation
answer = service.generate("What is faith?", max_new_tokens=100)
print(answer)

# Test 2: Get model info
info = service.get_model_info()
print(info)

# Test 3: Check initialization
assert service._initialized is True
```

---

## 8. Quick Start Commands

### Setup
```powershell
# 1. Install dependencies
pip install huggingface_hub

# 2. Set environment variable
# Add to .env file:
# HF_API_KEY=hf_your_token_here

# 3. Test the service
python -c "from app.services.hf_textgen_service import get_textgen_service; s = get_textgen_service(); print(s.generate('What is grace?', max_new_tokens=50))"
```

### Run Tests
```powershell
pytest tests/test_hf_textgen_service.py -v
```

### Check Status
```python
from app.services.hf_textgen_service import get_textgen_service

service = get_textgen_service()
print(service.get_model_info())
```

---

**🎯 END OF TIER 1 (IMPLEMENTATION GUIDE)**

Everything above is what you need to **build and deploy** the service TODAY.

Below is **Tier 2** - reference material for deep dives, optimization, and production hardening.

---

# 📚 TIER 2: REFERENCE ARCHITECTURE

**Use this section for:**
- Understanding design decisions
- Production optimization
- Troubleshooting
- Advanced features
- Scaling considerations

---

## 9. Monitoring & Observability

### 9.1 Key Metrics to Log

```python
# In generate_with_metadata()
metrics = {
    "latency_ms": generation_time * 1000,
    "tokens_generated": token_count,
    "model_used": self.model_name,
    "mode": "api" if self.use_api else "local",
    "temperature": temperature,
    "finish_reason": finish_reason,  # "length" | "eos" | "stop"
    "gpu_memory_mb": gpu_memory if torch.cuda.is_available() else None
}

logger.info(f"Generation completed: {metrics}")
```

### 9.2 Alerts to Configure

- **Latency > 10s:** Investigate model/GPU
- **OOM errors:** Need quantization or smaller model
- **Validation failures > 5%:** Review generation params
- **API rate limits:** Switch to local or increase quota

---

## 10. Deployment Checklist

### 10.1 Pre-Deployment

- [ ] Add HF packages to `requirements.txt`
- [ ] Set `HF_API_KEY` in production `.env`
- [ ] Choose mode: `HF_USE_API=true` (start with API for simplicity)
- [ ] Test with small query load (10 requests)
- [ ] Verify token limits enforced correctly
- [ ] Check logs for errors

### 10.2 Local Model Deployment (if using)

- [ ] Verify GPU available (`nvidia-smi`)
- [ ] Download model to server: `huggingface-cli download meta-llama/Llama-2-7b-chat-hf`
- [ ] Test model load time (should be <60s)
- [ ] Monitor GPU memory usage during generation
- [ ] Set up GPU memory clearing on errors
- [ ] Configure restart policy for OOM crashes

### 10.3 API Deployment

- [ ] Create HF API token (huggingface.co/settings/tokens)
- [ ] Set rate limits in HF dashboard
- [ ] Monitor API quota usage
- [ ] Set up fallback to local if API fails
- [ ] Configure retry delays for 429 errors

---

## 11. Performance Optimization

### 11.1 Speed Optimizations

| Technique | Speedup | Trade-off |
|-----------|---------|-----------|
| **8-bit quantization** | 2x faster | Slight quality loss |
| **Flash Attention 2** | 1.5x faster | Requires newer GPU |
| **Batch generation** | 3x throughput | Higher latency per request |
| **Model pruning** | 1.3x faster | Quality loss |
| **Smaller model** (Mistral-7B) | 1.5x faster | May reduce answer quality |

**Recommended for Production:**
```python
# In _load_local_model()
model_kwargs = {
    "device_map": "auto",
    "load_in_8bit": True,  # Enable quantization
    "torch_dtype": torch.float16,  # Half precision
}
```

### 11.2 Memory Optimizations

```python
# Clear cache after generation
def generate(self, prompt: str, **kwargs) -> str:
    try:
        result = self._generate_local(prompt, **kwargs)
        return result
    finally:
        if torch.cuda.is_available():
            torch.cuda.empty_cache()  # Free unused memory
```

---

## 9. Advanced Model Configuration (Local Inference Optimization)

### 9.1 Quantization for GPU Memory Savings

**8-bit Quantization** (saves ~4GB VRAM for Llama-7B):

```python
# Add to config.py
hf_use_quantization: bool = Field(default=False)

# In _load_local_model():
if settings.hf_use_quantization and torch.cuda.is_available():
    model_kwargs["load_in_8bit"] = True
    logger.info("Using 8-bit quantization (saves ~50% VRAM)")
```

**4-bit Quantization** (saves ~75% VRAM, slight quality loss):

```python
# Requires: pip install bitsandbytes
model_kwargs["load_in_4bit"] = True
model_kwargs["bnb_4bit_compute_dtype"] = torch.float16
```

### 9.2 GPU Device Management

```python
# Multi-GPU support
model_kwargs["device_map"] = "auto"  # Automatically distributes layers

# Single GPU
model_kwargs["device_map"] = {"": 0}  # Force to GPU 0

# CPU fallback
if not torch.cuda.is_available():
    model_kwargs["device_map"] = "cpu"
    logger.warning("No GPU - generation will be 10-50x slower")
```

### 9.3 Memory Cleanup After Generation

```python
def generate(self, prompt: str, **kwargs) -> str:
    try:
        result = self._generate_local(prompt, **kwargs)
        return result
    finally:
        # Clear unused GPU cache after each generation
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
```

---

## 10. Monitoring & Observability

### 10.1 Key Metrics to Track

| Metric | Type | Purpose | Alert Threshold |
|--------|------|---------|-----------------|
| `generation_latency_ms` | Histogram | Track response time | p95 > 5000ms |
| `generation_errors_total` | Counter | Track failure rate | Error rate > 5% |
| `tokens_generated` | Histogram | Track output length | p99 > 450 tokens |
| `api_calls_total` | Counter | HF API usage tracking | - |
| `gpu_memory_mb` | Gauge | Monitor VRAM usage | > 90% capacity |

### 10.2 Structured Logging Example

```python
logger.info(
    "generation_completed",
    extra={
        "duration_ms": 1250,
        "tokens_generated": 387,
        "model": "llama-2-7b",
        "mode": "api",
        "temperature": 0.2,
        "user_id": user_id,
        "status": "success"
    }
)
```

### 10.3 Prometheus Metrics (Optional)

```python
from prometheus_client import Histogram, Counter

GENERATION_LATENCY = Histogram(
    'textgen_latency_seconds',
    'Text generation latency',
    ['model', 'mode']
)

GENERATION_ERRORS = Counter(
    'textgen_errors_total',
    'Text generation errors',
    ['error_type']
)

# Usage:
with GENERATION_LATENCY.labels(model=self.model_name, mode='api').time():
    result = self._generate_api(...)
```

---

## 11. Performance Optimization

### 11.1 Speed Optimizations

| Technique | Speedup | Trade-off | When to Use |
|-----------|---------|-----------|-------------|
| **8-bit quantization** | 2x faster | Slight quality loss | GPU VRAM < 12GB |
| **Flash Attention 2** | 1.5x faster | Requires A100/H100 | Production with modern GPUs |
| **Batch generation** | 3x throughput | Higher latency/request | Bulk processing |
| **Smaller model** (Mistral-7B) | 1.5x faster | May reduce quality | Dev/staging |
| **Greedy decoding** (temp=0) | 1.3x faster | Less creative output | Factual queries |

### 11.2 Recommended Production Config

```python
# For production with GPU (8-16GB VRAM):
model_kwargs = {
    "device_map": "auto",
    "load_in_8bit": True,  # Quantization
    "torch_dtype": torch.float16,  # Half precision
    "low_cpu_mem_usage": True
}

# Generation params for pastoral QA:
gen_config = {
    "max_new_tokens": 400,
    "temperature": 0.2,  # Low for factual
    "top_p": 0.9,
    "repetition_penalty": 1.1,
    "do_sample": True
}
```

---

## 12. Security Considerations

### 12.1 Input Sanitization (Prevent Prompt Injection)

```python
def _sanitize_prompt(self, prompt: str) -> str:
    """Remove potential prompt injection attacks."""
    import re
    
    # Remove excessive newlines (common injection vector)
    prompt = re.sub(r'\n{3,}', '\n\n', prompt)
    
    # Truncate to max context window
    max_chars = settings.assistant_model_context_window * 4  # ~4 chars/token
    if len(prompt) > max_chars:
        logger.warning(f"Prompt truncated from {len(prompt)} to {max_chars} chars")
        prompt = prompt[:max_chars]
    
    # Remove control characters
    prompt = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', prompt)
    
    return prompt
```

### 12.2 Output Filtering (Prevent PII Leaks)

```python
def _filter_output(self, text: str) -> str:
    """Remove sensitive data from output."""
    import re
    
    # Mask email addresses
    text = re.sub(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        '[EMAIL]',
        text
    )
    
    # Mask phone numbers
    text = re.sub(
        r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
        '[PHONE]',
        text
    )
    
    # Mask credit cards
    text = re.sub(
        r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
        '[CARD]',
        text
    )
    
    return text
```

### 12.3 Rate Limiting (Prevent Abuse)

```python
# In AssistantService, before calling textgen:
from app.utils.rate_limiter import check_rate_limit

if not check_rate_limit(user_id, limit=10, window=60):
    raise HTTPException(
        status_code=429,
        detail="Rate limit exceeded. Max 10 queries per minute."
    )
```

---

## 13. Deployment Checklist

### 13.1 Pre-Deployment (Development)

- [ ] Add `huggingface_hub` to `requirements.txt`
- [ ] Set `HF_API_KEY` in `.env` (get from https://huggingface.co/settings/tokens)
- [ ] Set `HF_USE_API=true` (start with API mode)
- [ ] Test with sample queries (5-10 requests)
- [ ] Verify token limits enforced (check logs)
- [ ] Run unit tests: `pytest tests/test_hf_textgen_service.py`
- [ ] Check error handling (test with empty prompt, invalid params)

### 13.2 Production Deployment (API Mode)

- [ ] Create production HF API token with rate limits
- [ ] Configure monitoring/alerting (latency, errors)
- [ ] Set up log aggregation (Datadog, Splunk, etc.)
- [ ] Test with 50+ concurrent requests (load testing)
- [ ] Configure retry delays for 429 errors
- [ ] Set up fallback strategy (API → local if API fails)
- [ ] Document API quota limits for team

### 13.3 Production Deployment (Local Model)

- [ ] Verify GPU available: `nvidia-smi`
- [ ] Download model: `huggingface-cli download meta-llama/Llama-2-7b-chat-hf`
- [ ] Test model load time (<60s)
- [ ] Monitor GPU memory during generation
- [ ] Set up GPU memory clearing on OOM errors
- [ ] Configure restart policy for crashes
- [ ] Set up GPU health checks
- [ ] Test failover to API mode on GPU failure

---

## 14. Troubleshooting Guide

| Issue | Symptoms | Cause | Solution |
|-------|----------|-------|----------|
| **CUDA out of memory** | `torch.cuda.OutOfMemoryError` | Model too large for GPU | Enable 8-bit quantization or use API mode |
| **Model loading timeout** | Hangs >5min | Slow download/large model | Pre-download: `huggingface-cli download <model>` |
| **Empty output** | Blank or very short response | Bad prompt, wrong params | Log prompt, check temp/top_p, verify context |
| **Repetitive output** | Same phrases repeated | Low repetition_penalty | Increase to 1.2-1.5 |
| **Slow generation (>30s)** | High latency | CPU inference or overloaded | Use GPU, check GPU utilization, scale up |
| **API 429 error** | `Rate limit exceeded` | HF API quota exceeded | Add retry with backoff, upgrade quota, or use local |
| **Bad output quality** | Nonsensical answers | Temperature too high | Lower temp to 0.1-0.3 for factual tasks |
| **Token limit exceeded** | Truncated context | Prompt too long | Reduce context chunks, increase compression |

### 14.1 Debugging Commands

```powershell
# Check GPU status
nvidia-smi

# Test service initialization
python -c "from app.services.hf_textgen_service import get_textgen_service; print(get_textgen_service().get_model_info())"

# Check model download
huggingface-cli scan-cache

# Clear model cache
huggingface-cli delete-cache

# Test generation
python -c "from app.services.hf_textgen_service import get_textgen_service; s = get_textgen_service(); print(s.generate('What is faith?', max_new_tokens=50))"
```

---

## 15. Model Comparison & Selection

### 15.1 Recommended Models by Use Case

| Model | Size | VRAM | Speed | Quality | Use Case |
|-------|------|------|-------|---------|----------|
| **Llama-2-7B-chat** | 7B | 14GB | Medium | High | Production (recommended) |
| **Llama-2-7B-chat (8-bit)** | 7B | 7GB | Fast | High | Production (GPU-constrained) |
| **Mistral-7B-Instruct** | 7B | 14GB | Fast | High | Alternative to Llama-2 |
| **Phi-2** | 2.7B | 6GB | Very Fast | Medium | Development/testing |
| **GPT-2** | 1.5B | 3GB | Very Fast | Low | CI/unit tests only |

### 15.2 Evaluation Criteria

```python
# Test different models:
models = [
    "meta-llama/Llama-2-7b-chat-hf",
    "mistralai/Mistral-7B-Instruct-v0.2",
    "microsoft/phi-2"
]

test_queries = [
    "What is grace according to the Bible?",
    "Explain the concept of faith with examples.",
    "How does the pastor describe salvation?"
]

# Measure:
# - Latency (p50, p95, p99)
# - Quality (theological accuracy, citation quality)
# - Token efficiency (output length vs. quality)
# - Cost (API pricing or GPU hours)
```

---

## 16. Advanced Features (Phase 7+)

### 16.1 Streaming Responses (Server-Sent Events)

```python
async def generate_stream(self, prompt: str, **kwargs):
    """Stream generation token-by-token for real-time UI updates."""
    if self.use_api:
        # HF API supports streaming
        for token in self._api_client.text_generation(prompt, stream=True, **kwargs):
            yield token
    else:
        # Local streaming with transformers
        from transformers import TextIteratorStreamer
        # Implementation here...
```

### 16.2 Caching Common Queries

```python
from functools import lru_cache
import hashlib

def _cache_key(prompt: str, max_tokens: int) -> str:
    """Generate cache key from prompt."""
    return hashlib.sha256(f"{prompt}:{max_tokens}".encode()).hexdigest()

@lru_cache(maxsize=100)
def generate_cached(self, prompt: str, max_tokens: int) -> str:
    """Cache generated responses for repeated queries."""
    return self.generate(prompt, max_new_tokens=max_tokens)
```

### 16.3 Fine-tuning for Pastoral QA

```python
# Future: Train custom model on pastoral Q&A dataset
# Dataset: 1000+ sermon notes + theological Q&A pairs
# Method: LoRA fine-tuning (parameter-efficient)
# Tools: Hugging Face PEFT library

from peft import LoraConfig, get_peft_model

lora_config = LoraConfig(
    r=16,  # Low-rank adaptation rank
    lora_alpha=32,
    target_modules=["q_proj", "v_proj"],
    lora_dropout=0.05,
    task_type="CAUSAL_LM"
)

model = get_peft_model(base_model, lora_config)
# Train on custom dataset...
```

---

## 17. API Cost Tracking & Budgeting

### 17.1 HuggingFace Pricing (as of Dec 2025)

- **Free Tier:** 30,000 requests/month
- **Pro Tier:** $9/month for 1M tokens
- **Enterprise:** Custom pricing

**Cost Calculation:**
```python
# Estimate cost per query:
# - Input tokens: ~1800 (context + query)
# - Output tokens: ~400 (answer)
# - Total per query: 2200 tokens
# - Cost: (2200 / 1,000,000) * $9 = $0.02 per query

# For 1000 queries/day:
monthly_cost = (1000 * 30 * 2200 / 1_000_000) * 9
# = $5.94/month
```

### 17.2 Cost Tracking Implementation

```python
# In generate():
from app.services.tokenizer_service import get_tokenizer_service

tokenizer = get_tokenizer_service()
input_tokens = tokenizer.count_tokens(prompt)
output_tokens = tokenizer.count_tokens(answer)

# Log for cost tracking
logger.info(
    "api_usage",
    extra={
        "user_id": user_id,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "estimated_cost_usd": (input_tokens + output_tokens) / 1_000_000 * 9
    }
)
```

---

## 18. Success Criteria & KPIs

### 18.1 Performance Targets

| Metric | Target | Measured How |
|--------|--------|--------------|
| **Latency (p95)** | <5 seconds | Prometheus histogram |
| **Latency (p99)** | <8 seconds | Prometheus histogram |
| **Error Rate** | <1% | Counter / Total requests |
| **Token Limit Compliance** | 100% | Never >400 output tokens |
| **Concurrent Requests** | 100+ | Load testing |
| **GPU Memory Stability** | No leaks over 1000 requests | Monitor VRAM |
| **Uptime** | >99.5% | Service availability |

### 18.2 Quality Targets

| Metric | Target | Measured How |
|--------|--------|--------------|
| **Citation Accuracy** | >95% | Manual review of 100 samples |
| **Theological Soundness** | >90% | Pastor/theologian review |
| **Hallucination Rate** | <5% | Check for unsourced claims |
| **User Satisfaction** | >4.0/5.0 | User feedback surveys |

### 18.3 Validation Checklist

- [x] Service follows Scribes architecture patterns (singleton, config-driven)
- [ ] Generates answers in <5s (p95 latency)
- [ ] Handles 100 concurrent requests without crashing
- [ ] Token limits strictly enforced (never >400 output tokens)
- [ ] Zero prompt leaks in production logs
- [ ] Graceful degradation on failures (returns error, doesn't crash)
- [ ] GPU memory stable over 1000 requests (no leaks)
- [ ] Citations extracted correctly (>95% accuracy)
- [ ] No hallucinated scripture (verified via testing)

---

## 19. Next Steps & Future Roadmap

### Phase 6 (Current) - Basic Implementation
- [x] Tier 1 implementation (API mode)
- [ ] Integration with AssistantService
- [ ] End-to-end testing
- [ ] Production deployment (API mode)

### Phase 7 - Production Hardening
- [ ] Add local model support (GPU inference)
- [ ] Implement streaming responses
- [ ] Add response caching
- [ ] Set up comprehensive monitoring
- [ ] Load testing (1000+ concurrent)
- [ ] Cost optimization

### Phase 8 - Advanced Features
- [ ] Fine-tune custom model on sermon data
- [ ] Add multi-turn conversation support
- [ ] Implement answer ranking/reranking
- [ ] A/B test different models
- [ ] Add answer explanation/reasoning

### Phase 9 - Scale & Optimize
- [ ] Multi-model ensemble
- [ ] Distributed inference (multiple GPUs)
- [ ] Edge deployment options
- [ ] Mobile-optimized models

---

## 20. References & Resources

### Documentation
- **Hugging Face Transformers:** https://huggingface.co/docs/transformers/
- **Text Generation Guide:** https://huggingface.co/docs/transformers/main_classes/text_generation
- **Llama-2 Model Card:** https://huggingface.co/meta-llama/Llama-2-7b-chat-hf
- **Quantization Guide:** https://huggingface.co/docs/transformers/main_classes/quantization
- **HF Inference API:** https://huggingface.co/docs/api-inference/

### Internal Docs
- **Scribes Architecture:** `docs/ARCHITECTURE.md`
- **Tokenizer Service:** `docs/guides/backend implementations/assistant_tokenization_blueprint.md`
- **Observability Metrics:** `docs/guides/backend implementations/TOKENIZER_OBSERVABILITY_METRICS.md`

### Tools
- **Model Download:** `huggingface-cli download <model>`
- **GPU Monitoring:** `nvidia-smi` or `gpustat`
- **Load Testing:** `locust` or `k6`

---

**Document Version:** 2.0 (Hybrid 2-Tier Structure)  
**Last Updated:** December 9, 2025  
**Maintained By:** Joshua

---

## Quick Navigation

**🚀 For Implementation:** See Sections 1-8 (Tier 1)  
**📚 For Deep Dives:** See Sections 9-20 (Tier 2)  
**🔧 For Troubleshooting:** See Section 14  
**📊 For Monitoring:** See Section 10  
**💰 For Cost Tracking:** See Section 17  
**🎯 For Success Metrics:** See Section 18

---

## 14. Implementation Phases

### Phase 1: Basic Service (1-2 days) ✅ PRIORITY
- [ ] Create `hf_textgen_service.py` with singleton pattern
- [ ] Implement API mode (simpler, no GPU needed)
- [ ] Add basic `generate()` method
- [ ] Write unit tests with GPT-2 (small model)
- [ ] Integrate with `AssistantService`
- [ ] Test end-to-end with simple query

### Phase 2: Local Model Support (2-3 days)
- [ ] Implement `_load_local_model()` with device_map
- [ ] Add quantization support (8-bit)
- [ ] Test on GPU server
- [ ] Add OOM handling
- [ ] Benchmark vs API mode

### Phase 3: Production Hardening (1-2 days)
- [ ] Add retry logic with exponential backoff
- [ ] Implement fallback strategies
- [ ] Add comprehensive logging
- [ ] Add output validation
- [ ] Add GPU memory monitoring
- [ ] Load testing with 50+ concurrent requests

### Phase 4: Optimization (1-2 days)
- [ ] Add caching for repeated prompts (optional)
- [ ] Optimize generation params (temperature, top_p)
- [ ] Add batch generation support
- [ ] Add streaming support (optional, for long answers)

---

## 15. Quick Start Commands

### Install Dependencies
```powershell
# Add to requirements.txt, then:
pip install huggingface_hub accelerate bitsandbytes

# If using local models, download:
huggingface-cli login  # Enter HF token
huggingface-cli download meta-llama/Llama-2-7b-chat-hf
```

### Test Service
```python
# In Python shell:
from app.services.hf_textgen_service import get_textgen_service

service = get_textgen_service()
result = service.generate("What is faith?", max_new_tokens=100)
print(result)
```

### Run Tests
```powershell
pytest tests/test_hf_textgen_service.py -v
```

---

## 16. Troubleshooting Guide

| Issue | Cause | Solution |
|-------|-------|----------|
| `CUDA out of memory` | Model too large for GPU | Enable 8-bit quantization or use API mode |
| `Model loading timeout` | Slow download/large model | Pre-download model with `huggingface-cli` |
| `Empty output` | Bad prompt or wrong params | Log prompt, check temperature/top_p |
| `Repetitive output` | Low repetition_penalty | Increase to 1.2-1.5 |
| `Slow generation (>30s)` | CPU inference or large model | Use GPU or switch to API |
| `API 429 error` | Rate limit exceeded | Add retry with backoff, or use local |

---

## 17. Success Criteria

- [x] Service follows Scribes architecture patterns (singleton, lazy loading, config-driven)
- [ ] Generates answers in <5s (90th percentile)
- [ ] Handles 100 concurrent requests without crashing
- [ ] Token limits strictly enforced (never exceed 400 output tokens)
- [ ] Zero prompt leaks in production logs
- [ ] Graceful degradation on failures (returns error, doesn't crash)
- [ ] GPU memory stable over 1000 requests (no leaks)

---

## 18. Next Steps After Implementation

1. **Prompt Engineering:** Iterate on PromptEngine templates based on user feedback
2. **Model Evaluation:** A/B test Llama-2 vs Mistral vs Phi-3
3. **Fine-tuning:** Train custom model on pastoral Q&A dataset (advanced)
4. **Streaming:** Add SSE streaming for real-time answers (Phase 7)
5. **Caching:** Add Redis cache for common queries

---

## 19. References

- **Hugging Face Docs:** https://huggingface.co/docs/transformers/main_classes/text_generation
- **Llama-2 Model Card:** https://huggingface.co/meta-llama/Llama-2-7b-chat-hf
- **Quantization Guide:** https://huggingface.co/docs/transformers/main_classes/quantization
- **Scribes Architecture:** `docs/ARCHITECTURE.md`
- **Tokenizer Blueprint:** `docs/guides/backend implementations/assistant_tokenization_blueprint.md`

---

**Status:** Ready for scaffolding. Say "scaffold now" to generate the complete `hf_textgen_service.py` with tests.

---

**Document Version:** 1.0  
**Last Updated:** December 5, 2025  
**Maintained By:** Joshua
