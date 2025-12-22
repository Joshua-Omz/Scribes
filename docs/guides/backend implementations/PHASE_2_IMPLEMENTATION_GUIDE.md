# Phase 2 Implementation Guide - AI Assistant

**Your Strategic Decisions:**
- ✅ **Model Strategy:** HuggingFace Inference API (no GPU required)
- ✅ **Assistant Tone:** Pastoral (warm, supportive, spiritually nurturing)
- ✅ **Context Strategy:** Separate high/low relevance chunks, store low-relevance for later use
- ✅ **Hardware:** No GPU available

---

## Table of Contents
1. [Todo 6: Retrieval Service](#todo-6-retrieval-service)
2. [Todo 7: Context Builder](#todo-7-context-builder)
3. [Todo 8: Prompt Engineering](#todo-8-prompt-engineering)
4. [Todo 9: Model Selection & Config](#todo-9-model-selection--config)
5. [Todo 10: Generation Service](#todo-10-generation-service)
6. [Testing Your Implementation](#testing-your-implementation)
7. [Environment Setup](#environment-setup)

---

## Environment Setup (Do This First)

### 1. Install Required Packages
```powershell
# Already done from Phase 1:
# pip install transformers sentence-transformers torch

# Now add HuggingFace Hub for API access
pip install huggingface-hub
```

### 2. Get HuggingFace API Token
1. Go to https://huggingface.co/settings/tokens
2. Create a new token (read access is enough)
3. Copy the token

### 3. Update `.env` File
Add to your `.env` file:
```env
# HuggingFace Configuration
HF_API_KEY=your_hf_token_here
HF_USE_API=True
HF_GENERATION_MODEL=meta-llama/Llama-3.2-3B-Instruct
# Alternative models (if Llama not available):
# HF_GENERATION_MODEL=mistralai/Mistral-7B-Instruct-v0.2
# HF_GENERATION_MODEL=HuggingFaceH4/zephyr-7b-beta
```

**Why Llama-3.2-3B-Instruct?**
- Smaller model (faster inference, lower cost)
- Optimized for instruction-following
- Good balance of quality and speed
- Supports pastoral tone well

---

## Todo 6: Retrieval Service [SECURITY-CRITICAL]

### Implementation Strategy

**Purpose:** Retrieve relevant note chunks with strict user isolation.

**Key Requirements:**
1. ✅ User isolation (prevent cross-user access)
2. ✅ Vector similarity search using pgvector
3. ✅ Return high + low relevance chunks (separated)
4. ✅ Include note metadata for citations

### Implementation

Create or replace `app/services/retrieval_service.py`:

```python
"""
Retrieval service for semantic search over note chunks.

Performs vector similarity search with user isolation.
Separates high and low relevance chunks for different uses.
"""

from typing import List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class RetrievalService:
    """
    Service for retrieving relevant note chunks via vector similarity.
    
    Features:
    - User-scoped vector search (security)
    - Separates high/low relevance chunks
    - Returns note metadata for citations
    """
    
    def __init__(self):
        """Initialize retrieval service."""
        self.relevance_threshold = 0.6  # Scores above = high relevance
        logger.info(
            f"RetrievalService initialized "
            f"(relevance_threshold={self.relevance_threshold})"
        )
    
    async def retrieve_top_chunks(
        self,
        db: AsyncSession,
        query_embedding: List[float],
        user_id: int,
        top_k: int = 50
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Retrieve top-k most relevant chunks for a query.
        
        SECURITY: Only retrieves chunks from notes owned by user_id.
        
        Args:
            db: Database session
            query_embedding: Query vector (384-dim)
            user_id: Current user's ID (for isolation)
            top_k: Number of chunks to retrieve
            
        Returns:
            Tuple of (high_relevance_chunks, low_relevance_chunks)
            Each chunk dict contains:
            {
                "chunk_id": int,
                "note_id": int,
                "chunk_idx": int,
                "chunk_text": str,
                "relevance_score": float (0-1, higher is better),
                "note_title": str,
                "note_created_at": datetime,
                "preacher": str,
                "scripture_refs": str,
                "tags": str
            }
            
        Raises:
            ValueError: If inputs invalid
            Exception: If DB error occurs
        """
        # Input validation
        if not query_embedding or len(query_embedding) != settings.assistant_embedding_dim:
            raise ValueError(
                f"Invalid query_embedding: expected {settings.assistant_embedding_dim} dimensions, "
                f"got {len(query_embedding) if query_embedding else 0}"
            )
        
        if user_id <= 0:
            raise ValueError(f"Invalid user_id: {user_id}")
        
        if top_k <= 0 or top_k > 200:
            raise ValueError(f"Invalid top_k: {top_k} (must be 1-200)")
        
        logger.info(f"Retrieving top-{top_k} chunks for user {user_id}")
        
        # SQL query with user isolation
        # Uses cosine distance (<->) for similarity
        # Joins with notes table to get metadata and enforce user_id filter
        query_sql = text("""
            SELECT 
                nc.id as chunk_id,
                nc.note_id,
                nc.chunk_idx,
                nc.chunk_text,
                1 - (nc.embedding <=> :query_vec) as relevance_score,
                n.title as note_title,
                n.created_at as note_created_at,
                n.preacher,
                n.scripture_refs,
                n.tags
            FROM note_chunks nc
            INNER JOIN notes n ON nc.note_id = n.id
            WHERE 
                n.user_id = :user_id
                AND nc.embedding IS NOT NULL
            ORDER BY nc.embedding <=> :query_vec
            LIMIT :top_k
        """)
        
        try:
            # Execute query
            result = await db.execute(
                query_sql,
                {
                    "query_vec": str(query_embedding),  # pgvector accepts string format
                    "user_id": user_id,
                    "top_k": top_k
                }
            )
            
            rows = result.fetchall()
            
            if not rows:
                logger.warning(
                    f"No chunks found for user {user_id}. "
                    f"User may have no notes with embeddings."
                )
                return [], []
            
            # Convert rows to dicts
            all_chunks = []
            for row in rows:
                chunk_dict = {
                    "chunk_id": row.chunk_id,
                    "note_id": row.note_id,
                    "chunk_idx": row.chunk_idx,
                    "chunk_text": row.chunk_text,
                    "relevance_score": float(row.relevance_score),
                    "note_title": row.note_title,
                    "note_created_at": row.note_created_at,
                    "preacher": row.preacher,
                    "scripture_refs": row.scripture_refs,
                    "tags": row.tags
                }
                all_chunks.append(chunk_dict)
            
            # Separate high and low relevance chunks
            high_relevance = [
                c for c in all_chunks 
                if c["relevance_score"] >= self.relevance_threshold
            ]
            low_relevance = [
                c for c in all_chunks 
                if c["relevance_score"] < self.relevance_threshold
            ]
            
            logger.info(
                f"Retrieved {len(all_chunks)} chunks for user {user_id}: "
                f"{len(high_relevance)} high relevance, {len(low_relevance)} low relevance"
            )
            
            return high_relevance, low_relevance
            
        except Exception as e:
            logger.error(f"Error retrieving chunks for user {user_id}: {e}", exc_info=True)
            raise Exception(f"Database error during chunk retrieval: {str(e)}")
    
    def set_relevance_threshold(self, threshold: float):
        """
        Update the relevance threshold for separating high/low relevance.
        
        Args:
            threshold: Score threshold (0-1). Scores >= threshold are "high relevance"
        """
        if not 0 <= threshold <= 1:
            raise ValueError(f"Threshold must be 0-1, got {threshold}")
        
        self.relevance_threshold = threshold
        logger.info(f"Relevance threshold updated to {threshold}")


# Singleton
_retrieval_service = None


def get_retrieval_service() -> RetrievalService:
    """Get or create retrieval service singleton."""
    global _retrieval_service
    if _retrieval_service is None:
        _retrieval_service = RetrievalService()
    return _retrieval_service
```

### Testing Retrieval Service

Create `app/tests/test_retrieval_service.py`:

```python
"""
Integration tests for RetrievalService.

Requires test database with sample data.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.retrieval_service import RetrievalService


@pytest.mark.asyncio
class TestRetrievalService:
    """Test suite for RetrievalService (requires DB)."""
    
    async def test_retrieve_with_user_isolation(self, db: AsyncSession):
        """
        Test that users can only retrieve their own chunks.
        
        TODO: Setup test data with users 1 and 2, verify isolation
        """
        pass
    
    async def test_relevance_separation(self, db: AsyncSession):
        """Test that chunks are separated by relevance score."""
        pass
    
    async def test_invalid_inputs(self, db: AsyncSession):
        """Test error handling for invalid inputs."""
        service = RetrievalService()
        
        with pytest.raises(ValueError):
            # Invalid embedding dimension
            await service.retrieve_top_chunks(db, [0.1] * 100, 1, 10)
        
        with pytest.raises(ValueError):
            # Invalid user_id
            await service.retrieve_top_chunks(db, [0.1] * 384, -1, 10)
```

---

## Todo 7: Context Builder [QUALITY-CRITICAL]

### Implementation Strategy

**Your Strategy:** Use high-relevance chunks for context, store low-relevance separately for later.

**Benefits:**
- Higher quality answers (only relevant context)
- Token budget used efficiently
- Low-relevance chunks available for refinement/expansion

### Implementation

Create or replace `app/services/context_builder.py`:

```python
"""
Context builder service for constructing LLM context from retrieved chunks.

Builds token-aware context using high-relevance chunks.
Preserves low-relevance chunks for potential later use.
"""

from typing import List, Dict, Any
import logging

from app.services.tokenizer_service import get_tokenizer_service
from app.core.config import settings

logger = logging.getLogger(__name__)


class ContextBuilder:
    """
    Service for building token-aware context from retrieved chunks.
    
    Strategy:
    - Use high-relevance chunks for main context
    - Track token usage to stay within budget
    - Store low-relevance chunks in metadata (not in context)
    - Preserve source diversity (multiple notes when possible)
    """
    
    def __init__(self):
        """Initialize context builder."""
        self.tokenizer = get_tokenizer_service()
        logger.info("ContextBuilder initialized")
    
    def build_context(
        self,
        high_relevance_chunks: List[Dict[str, Any]],
        low_relevance_chunks: List[Dict[str, Any]],
        token_budget: int
    ) -> Dict[str, Any]:
        """
        Build final context from chunks within token budget.
        
        Args:
            high_relevance_chunks: High-relevance chunks (for context)
            low_relevance_chunks: Low-relevance chunks (stored, not used)
            token_budget: Maximum tokens allowed for context
            
        Returns:
            Dictionary with structure:
            {
                "context_text": str,  # Formatted context for prompt
                "chunks_used": [list of chunks included],
                "low_relevance_stored": [list of low-relevance chunks],
                "metadata": {
                    "chunks_retrieved_high": int,
                    "chunks_retrieved_low": int,
                    "chunks_used": int,
                    "total_tokens_used": int,
                    "token_budget": int,
                    "truncated": bool,
                    "notes_cited": [list of unique note_ids]
                }
            }
        """
        logger.info(
            f"Building context from {len(high_relevance_chunks)} high-relevance "
            f"and {len(low_relevance_chunks)} low-relevance chunks "
            f"(budget: {token_budget} tokens)"
        )
        
        if not high_relevance_chunks:
            logger.warning("No high-relevance chunks provided. Context will be empty.")
            return {
                "context_text": "",
                "chunks_used": [],
                "low_relevance_stored": low_relevance_chunks,
                "metadata": {
                    "chunks_retrieved_high": 0,
                    "chunks_retrieved_low": len(low_relevance_chunks),
                    "chunks_used": 0,
                    "total_tokens_used": 0,
                    "token_budget": token_budget,
                    "truncated": False,
                    "notes_cited": []
                }
            }
        
        # Build context from high-relevance chunks
        selected_chunks = []
        tokens_used = 0
        notes_seen = set()
        truncated = False
        
        # Iterate through chunks by relevance score (already sorted from retrieval)
        for chunk in high_relevance_chunks:
            chunk_text = chunk["chunk_text"]
            chunk_tokens = self.tokenizer.count_tokens(chunk_text)
            
            # Check if adding this chunk would exceed budget
            # Reserve ~50 tokens for formatting (section headers, etc.)
            formatting_overhead = 50
            if tokens_used + chunk_tokens + formatting_overhead > token_budget:
                logger.info(
                    f"Token budget reached. Used {len(selected_chunks)} of "
                    f"{len(high_relevance_chunks)} available chunks."
                )
                truncated = True
                break
            
            # Add chunk
            selected_chunks.append(chunk)
            tokens_used += chunk_tokens
            notes_seen.add(chunk["note_id"])
        
        # Format context text
        context_text = self._format_context(selected_chunks)
        
        # Calculate actual token count of formatted context
        actual_tokens = self.tokenizer.count_tokens(context_text)
        
        result = {
            "context_text": context_text,
            "chunks_used": selected_chunks,
            "low_relevance_stored": low_relevance_chunks,
            "metadata": {
                "chunks_retrieved_high": len(high_relevance_chunks),
                "chunks_retrieved_low": len(low_relevance_chunks),
                "chunks_used": len(selected_chunks),
                "total_tokens_used": actual_tokens,
                "token_budget": token_budget,
                "truncated": truncated,
                "notes_cited": list(notes_seen)
            }
        }
        
        logger.info(
            f"Context built: {len(selected_chunks)} chunks, "
            f"{actual_tokens} tokens, {len(notes_seen)} unique notes"
        )
        
        return result
    
    def _format_context(self, chunks: List[Dict[str, Any]]) -> str:
        """
        Format chunks into context text for the prompt.
        
        Format:
        ```
        [Source: Note Title by Preacher - Scripture Refs]
        {chunk text}
        
        [Source: Another Note Title...]
        {chunk text}
        ```
        
        Args:
            chunks: Selected chunks to include
            
        Returns:
            Formatted context string
        """
        if not chunks:
            return ""
        
        context_parts = []
        
        for chunk in chunks:
            # Build source header
            source_parts = []
            if chunk.get("note_title"):
                source_parts.append(chunk["note_title"])
            if chunk.get("preacher"):
                source_parts.append(f"by {chunk['preacher']}")
            if chunk.get("scripture_refs"):
                source_parts.append(f"({chunk['scripture_refs']})")
            
            source_header = " - ".join(source_parts) if source_parts else f"Note ID {chunk['note_id']}"
            
            # Format chunk
            chunk_formatted = f"[Source: {source_header}]\n{chunk['chunk_text']}\n"
            context_parts.append(chunk_formatted)
        
        return "\n".join(context_parts)


# Singleton
_context_builder = None


def get_context_builder() -> ContextBuilder:
    """Get or create context builder singleton."""
    global _context_builder
    if _context_builder is None:
        _context_builder = ContextBuilder()
    return _context_builder
```

---

## Todo 8: Prompt Engineering [SAFETY-CRITICAL]

### Pastoral Tone Implementation

**Characteristics of Pastoral Tone:**
- Warm, compassionate, supportive
- Spiritually nurturing
- Uses inclusive "we" language
- References faith journey
- Encouraging but honest
- Respects spiritual seeking

### Implementation

Create or replace `app/core/prompt_engine.py`:

```python
"""
Prompt engine for assembling final prompts with token budget enforcement.

Implements pastoral tone for spiritual guidance.
Includes prompt injection defenses and safety measures.
"""

from typing import Dict, Any, Optional
import logging
import re

from app.services.tokenizer_service import get_tokenizer_service
from app.core.config import settings

logger = logging.getLogger(__name__)


class PromptEngine:
    """
    Engine for constructing prompts with token awareness and pastoral tone.
    """
    
    # Prompt injection patterns to detect
    INJECTION_PATTERNS = [
        r"ignore\s+(previous|above|prior|all)\s+(instructions|prompts|commands)",
        r"disregard\s+(previous|above|all)",
        r"you\s+are\s+now",
        r"new\s+instructions",
        r"system\s*:\s*you\s+are",
        r"<\s*\|system\|>",
        r"forget\s+(everything|all|previous)",
        r"roleplay\s+as",
        r"pretend\s+(you\s+are|to\s+be)",
    ]
    
    def __init__(self):
        """Initialize prompt engine."""
        self.tokenizer = get_tokenizer_service()
        self.model_context_window = settings.assistant_model_context_window
        self.system_tokens = settings.assistant_system_tokens
        self.max_output_tokens = settings.assistant_max_output_tokens
        logger.info(
            f"PromptEngine initialized (pastoral tone, "
            f"context_window={self.model_context_window})"
        )
    
    def build_prompt(
        self,
        user_query: str,
        context_text: str,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Build final prompt for generation.
        
        Args:
            user_query: User's question
            context_text: Formatted context from context builder
            system_prompt: Optional override for system instructions
            
        Returns:
            Dictionary with:
            {
                "prompt": str (full assembled prompt),
                "token_breakdown": {
                    "system_tokens": int,
                    "context_tokens": int,
                    "query_tokens": int,
                    "reserved_output_tokens": int,
                    "total_input_tokens": int
                },
                "within_budget": bool,
                "safety_warnings": [list of safety issues detected]
            }
        """
        logger.info("Building prompt with pastoral tone")
        
        # Detect prompt injection
        safety_warnings = []
        if self.detect_prompt_injection(user_query):
            logger.warning(f"Potential prompt injection detected in query: {user_query[:100]}")
            safety_warnings.append("PROMPT_INJECTION_DETECTED")
        
        # Get system prompt
        if system_prompt is None:
            system_prompt = self.get_default_system_prompt()
        
        # Count tokens for each component
        system_tokens = self.tokenizer.count_tokens(system_prompt)
        context_tokens = self.tokenizer.count_tokens(context_text)
        query_tokens = self.tokenizer.count_tokens(user_query)
        
        # Calculate total input tokens
        total_input_tokens = system_tokens + context_tokens + query_tokens
        
        # Check if within budget (leaving room for output)
        max_input_tokens = self.model_context_window - self.max_output_tokens
        within_budget = total_input_tokens <= max_input_tokens
        
        if not within_budget:
            logger.error(
                f"Prompt exceeds token budget: {total_input_tokens} > {max_input_tokens}. "
                f"This should not happen if context builder worked correctly!"
            )
            safety_warnings.append("TOKEN_BUDGET_EXCEEDED")
        
        # Assemble final prompt
        if context_text:
            full_prompt = f"""{system_prompt}

CONTEXT FROM YOUR SERMON NOTES:
---
{context_text}
---

QUESTION: {user_query}

ANSWER:"""
        else:
            # No context available
            full_prompt = f"""{system_prompt}

QUESTION: {user_query}

NOTE: I don't have any relevant sermon notes to reference for this question. I'll provide a general response based on Christian teaching.

ANSWER:"""
        
        result = {
            "prompt": full_prompt,
            "token_breakdown": {
                "system_tokens": system_tokens,
                "context_tokens": context_tokens,
                "query_tokens": query_tokens,
                "reserved_output_tokens": self.max_output_tokens,
                "total_input_tokens": total_input_tokens
            },
            "within_budget": within_budget,
            "safety_warnings": safety_warnings
        }
        
        logger.info(
            f"Prompt built: {total_input_tokens} input tokens, "
            f"{self.max_output_tokens} reserved for output"
        )
        
        return result
    
    def get_default_system_prompt(self) -> str:
        """
        Get default system instructions with pastoral tone.
        
        Returns:
            System prompt string
        """
        return """You are a compassionate pastoral assistant helping someone reflect on their sermon notes and grow in their faith journey. Your role is to:

1. Draw insights from the provided sermon notes with care and spiritual sensitivity
2. Speak with warmth and encouragement, using "we" language to walk alongside the person
3. Cite specific sources using [Note Title] format when referencing notes
4. Be honest when you don't have relevant notes - suggest the person may want to journal about the topic
5. Respect the spiritual seeking in every question
6. Offer gentle wisdom that nurtures faith and understanding

Respond with pastoral warmth, scriptural insight where appropriate, and genuine care for the person's spiritual growth. Keep responses concise but meaningful."""
    
    def detect_prompt_injection(self, user_query: str) -> bool:
        """
        Detect potential prompt injection attempts.
        
        Looks for common injection patterns like:
        - "Ignore previous instructions"
        - "You are now..."
        - Role-playing attempts
        - System prompt manipulation
        
        Args:
            user_query: User's input query
            
        Returns:
            True if potential injection detected, False otherwise
        """
        query_lower = user_query.lower()
        
        for pattern in self.INJECTION_PATTERNS:
            if re.search(pattern, query_lower, re.IGNORECASE):
                logger.warning(f"Injection pattern matched: {pattern}")
                return True
        
        return False


# Singleton
_prompt_engine = None


def get_prompt_engine() -> PromptEngine:
    """Get or create prompt engine singleton."""
    global _prompt_engine
    if _prompt_engine is None:
        _prompt_engine = PromptEngine()
    return _prompt_engine
```

---

## Todo 9: Model Selection & Config [COST-CRITICAL]

### Recommended Model: Llama-3.2-3B-Instruct

**Why this model?**
- ✅ Optimized for instruction-following
- ✅ Good at maintaining tone (pastoral)
- ✅ 3B parameters = faster + cheaper than 7B
- ✅ Available via HuggingFace Inference API
- ✅ No GPU required

**Alternative Models (if Llama unavailable):**
1. `mistralai/Mistral-7B-Instruct-v0.2` - Excellent quality, slightly slower
2. `HuggingFaceH4/zephyr-7b-beta` - Good for conversational tone
3. `google/flan-t5-large` - Smaller, faster, cheaper (but less nuanced)

### Cost Estimation

**HuggingFace Inference API Pricing:**
- ~$0.0006 per 1K tokens (as of Nov 2024)
- Average query: ~2K input + 400 output = 2.4K tokens
- Cost per query: ~$0.0014 (less than 1/10th of a cent)
- 1000 queries: ~$1.40

### Configuration

Already configured in Phase 1! Just update `.env`:

```env
HF_API_KEY=your_token_here
HF_USE_API=True
HF_GENERATION_MODEL=meta-llama/Llama-3.2-3B-Instruct
HF_GENERATION_TEMPERATURE=0.3
HF_GENERATION_TIMEOUT=30
```

**Temperature = 0.3** (slightly higher than default 0.2 for pastoral warmth)

---

## Todo 10: Generation Service [SAFETY-CRITICAL]

### Implementation

Create or replace `app/services/hf_textgen_service.py`:

```python
"""
Hugging Face text generation service using Inference API.

Handles text generation with safety controls, timeout handling, and metrics.
"""

from typing import Optional, Dict, Any
import logging
import asyncio
import time

from huggingface_hub import InferenceClient
from huggingface_hub.errors import HfHubHTTPError

from app.core.config import settings

logger = logging.getLogger(__name__)


class HFTextGenService:
    """
    Service for text generation using Hugging Face Inference API.
    
    Features:
    - Uses HF Inference API (no local GPU needed)
    - Timeout handling
    - Error recovery with fallback
    - Generation metrics logging
    """
    
    def __init__(self):
        """Initialize text generation service."""
        self.model_name = settings.hf_generation_model
        self.api_key = settings.huggingface_api_key
        self.temperature = settings.hf_generation_temperature
        self.timeout = settings.hf_generation_timeout
        
        # Initialize Inference Client
        if not self.api_key:
            raise ValueError(
                "HF_API_KEY not found in environment. "
                "Get token from https://huggingface.co/settings/tokens"
            )
        
        self.client = InferenceClient(token=self.api_key)
        
        logger.info(
            f"HFTextGenService initialized "
            f"(model={self.model_name}, API mode, timeout={self.timeout}s)"
        )
    
    async def generate(
        self,
        prompt: str,
        max_new_tokens: int = 400,
        temperature: Optional[float] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate text from prompt using HF Inference API.
        
        Args:
            prompt: Full assembled prompt
            max_new_tokens: Maximum tokens to generate
            temperature: Sampling temperature (overrides config)
            **kwargs: Additional generation params
            
        Returns:
            Dictionary with:
            {
                "generated_text": str (only the new text, not prompt),
                "full_response": str (prompt + generated),
                "tokens_generated": int (estimated),
                "latency_ms": int,
                "model_name": str,
                "truncated": bool
            }
        """
        start_time = time.time()
        
        # Use provided temperature or default
        temp = temperature if temperature is not None else self.temperature
        
        logger.info(
            f"Generating with {self.model_name} "
            f"(max_tokens={max_new_tokens}, temp={temp})"
        )
        
        try:
            # Call HF Inference API
            # Use asyncio.wait_for for timeout
            response = await asyncio.wait_for(
                self._call_api(prompt, max_new_tokens, temp, **kwargs),
                timeout=self.timeout
            )
            
            # Extract generated text (remove prompt if included)
            full_response = response
            if full_response.startswith(prompt):
                generated_text = full_response[len(prompt):].strip()
            else:
                generated_text = full_response.strip()
            
            # Calculate metrics
            latency_ms = int((time.time() - start_time) * 1000)
            
            # Estimate tokens (rough: 4 chars per token)
            tokens_generated = len(generated_text) // 4
            
            # Check if truncated (hit max_new_tokens limit)
            truncated = tokens_generated >= max_new_tokens
            
            result = {
                "generated_text": generated_text,
                "full_response": full_response,
                "tokens_generated": tokens_generated,
                "latency_ms": latency_ms,
                "model_name": self.model_name,
                "truncated": truncated
            }
            
            logger.info(
                f"Generation completed: {tokens_generated} tokens, "
                f"{latency_ms}ms latency"
            )
            
            return result
            
        except asyncio.TimeoutError:
            logger.error(f"Generation timeout after {self.timeout}s")
            raise TimeoutError(
                f"Text generation exceeded {self.timeout}s timeout. "
                "The model may be overloaded. Please try again."
            )
        
        except HfHubHTTPError as e:
            logger.error(f"HuggingFace API error: {e}", exc_info=True)
            if "rate limit" in str(e).lower():
                raise RuntimeError(
                    "HuggingFace API rate limit exceeded. Please wait a moment and try again."
                )
            elif "model" in str(e).lower() and "not found" in str(e).lower():
                raise RuntimeError(
                    f"Model {self.model_name} not found or not accessible. "
                    "Check model name and API token permissions."
                )
            else:
                raise RuntimeError(f"HuggingFace API error: {str(e)}")
        
        except Exception as e:
            logger.error(f"Unexpected generation error: {e}", exc_info=True)
            raise RuntimeError(f"Text generation failed: {str(e)}")
    
    async def _call_api(
        self,
        prompt: str,
        max_new_tokens: int,
        temperature: float,
        **kwargs
    ) -> str:
        """
        Call HuggingFace Inference API (async wrapper for sync call).
        
        Args:
            prompt: Full prompt
            max_new_tokens: Max tokens to generate
            temperature: Temperature
            **kwargs: Additional params
            
        Returns:
            Generated text string
        """
        # Run in thread pool since HF client is sync
        loop = asyncio.get_event_loop()
        
        response = await loop.run_in_executor(
            None,
            lambda: self.client.text_generation(
                prompt,
                model=self.model_name,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                return_full_text=True,  # Include prompt in response
                **kwargs
            )
        )
        
        return response
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check if model is accessible via API.
        
        Returns:
            Status dict with model info
        """
        try:
            # Simple test generation
            test_response = await asyncio.wait_for(
                self._call_api("Test prompt", max_new_tokens=5, temperature=0.1),
                timeout=10
            )
            
            return {
                "status": "healthy",
                "model": self.model_name,
                "api_accessible": True,
                "test_response_length": len(test_response)
            }
        
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "model": self.model_name,
                "api_accessible": False,
                "error": str(e)
            }


# Singleton
_textgen_service = None


def get_textgen_service() -> HFTextGenService:
    """Get or create text generation service singleton."""
    global _textgen_service
    if _textgen_service is None:
        _textgen_service = HFTextGenService()
    return _textgen_service
```

---

## Testing Your Implementation

### 1. Test Each Service Individually

**Test Retrieval:**
```python
# In Python console or test file
from app.services.retrieval_service import get_retrieval_service

# Requires: DB with note_chunks, query embedding
# Will test in integration tests
```

**Test Context Builder:**
```python
from app.services.context_builder import get_context_builder

builder = get_context_builder()

# Mock chunks
high_rel = [
    {"chunk_id": 1, "note_id": 1, "chunk_text": "Faith is...", 
     "relevance_score": 0.9, "note_title": "Sermon on Faith"}
]
low_rel = [
    {"chunk_id": 2, "note_id": 2, "chunk_text": "Other topic...",
     "relevance_score": 0.4, "note_title": "Another Sermon"}
]

context = builder.build_context(high_rel, low_rel, token_budget=1800)
print(context["context_text"])
```

**Test Prompt Engine:**
```python
from app.core.prompt_engine import get_prompt_engine

engine = get_prompt_engine()

prompt_result = engine.build_prompt(
    user_query="What does faith mean?",
    context_text="[Source: Sermon]\nFaith is trust in God..."
)

print(prompt_result["prompt"])
print(prompt_result["token_breakdown"])
```

**Test Generation (requires HF API key):**
```python
import asyncio
from app.services.hf_textgen_service import get_textgen_service

async def test_gen():
    gen = get_textgen_service()
    
    result = await gen.generate(
        "You are a pastoral assistant. What is grace?\nAnswer:",
        max_new_tokens=100
    )
    
    print(result["generated_text"])
    print(f"Tokens: {result['tokens_generated']}, Latency: {result['latency_ms']}ms")

asyncio.run(test_gen())
```

### 2. Integration Test

Create `app/tests/test_assistant_integration.py`:

```python
"""
Integration test for full assistant flow.
"""

import pytest
from app.services.tokenizer_service import get_tokenizer_service
from app.services.context_builder import get_context_builder
from app.core.prompt_engine import get_prompt_engine


def test_full_context_to_prompt_flow():
    """Test context building → prompt assembly flow."""
    
    # Mock high-relevance chunks
    high_chunks = [
        {
            "chunk_id": 1,
            "note_id": 101,
            "chunk_idx": 0,
            "chunk_text": "Faith is trusting God even when we cannot see the path ahead.",
            "relevance_score": 0.92,
            "note_title": "Sermon on Faith",
            "preacher": "Pastor John",
            "scripture_refs": "Hebrews 11:1",
            "tags": "faith,trust",
            "note_created_at": None
        },
        {
            "chunk_id": 2,
            "note_id": 102,
            "chunk_idx": 0,
            "chunk_text": "Grace is God's unmerited favor toward us.",
            "relevance_score": 0.88,
            "note_title": "Understanding Grace",
            "preacher": "Pastor Sarah",
            "scripture_refs": "Ephesians 2:8",
            "tags": "grace,salvation",
            "note_created_at": None
        }
    ]
    
    low_chunks = [
        {
            "chunk_id": 3,
            "note_id": 103,
            "chunk_idx": 0,
            "chunk_text": "The church picnic will be on Saturday.",
            "relevance_score": 0.3,
            "note_title": "Announcements",
            "preacher": None,
            "scripture_refs": None,
            "tags": "announcements",
            "note_created_at": None
        }
    ]
    
    # Build context
    builder = get_context_builder()
    context_result = builder.build_context(high_chunks, low_chunks, token_budget=1800)
    
    assert len(context_result["chunks_used"]) == 2
    assert len(context_result["low_relevance_stored"]) == 1
    assert "Faith is trusting God" in context_result["context_text"]
    assert "Grace is God's unmerited favor" in context_result["context_text"]
    
    # Build prompt
    engine = get_prompt_engine()
    prompt_result = engine.build_prompt(
        user_query="What is the relationship between faith and grace?",
        context_text=context_result["context_text"]
    )
    
    assert prompt_result["within_budget"]
    assert "pastoral assistant" in prompt_result["prompt"].lower()
    assert "Faith is trusting God" in prompt_result["prompt"]
    assert len(prompt_result["safety_warnings"]) == 0
    
    print("✅ Integration test passed!")
    print(f"Context tokens: {context_result['metadata']['total_tokens_used']}")
    print(f"Total input tokens: {prompt_result['token_breakdown']['total_input_tokens']}")
```

---

## Next Steps After Phase 2

Once Phase 2 is complete:

1. **Test with real data** - Run migration, create chunks, test queries
2. **Move to Phase 3** - Implement assistant orchestration and routes
3. **Add caching** - Phase 4 (Redis caching for repeated queries)
4. **Security review** - Phase 4 (audit logging, user isolation tests)
5. **Production tuning** - Phase 5 (load testing, optimization)

---

## Summary Checklist

- [ ] Update `.env` with HF_API_KEY and HF_USE_API=True
- [ ] Install `huggingface-hub` package
- [ ] Implement `retrieval_service.py` (copy code above)
- [ ] Implement `context_builder.py` (copy code above)
- [ ] Implement `prompt_engine.py` (copy code above)
- [ ] Verify `config.py` has HF settings (already done in Phase 1)
- [ ] Implement `hf_textgen_service.py` (copy code above)
- [ ] Test each service individually
- [ ] Run integration test
- [ ] Verify pastoral tone in generated responses

**When complete, you'll have a working AI assistant backend ready for Phase 3!**

