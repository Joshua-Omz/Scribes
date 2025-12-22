# HFTextGenService Integration Planning Document

**Date:** December 9, 2025  
**Status:** 🔍 PLANNING PHASE  
**Phase:** Pre-Implementation Audit

---

## Executive Summary

This document provides a comprehensive audit of the current AI infrastructure and detailed planning for integrating `HFTextGenService` into the `AssistantService` RAG pipeline. All prerequisite services are implemented and ready; only the final integration step remains.

---

## 1. Current Infrastructure Audit

### 1.1 Service Status Overview

| Service | Status | Location | Singleton | Tests |
|---------|--------|----------|-----------|-------|
| **TokenizerService** | ✅ Complete | `app/services/tokenizer_service.py` | Yes | ✅ Passing |
| **EmbeddingService** | ✅ Complete | `app/services/embedding_service.py` | Yes | ✅ Passing |
| **RetrievalService** | ✅ Complete | `app/services/retrieval_service.py` | Yes | ✅ Passing |
| **ContextBuilder** | ✅ Complete | `app/services/context_builder.py` | Yes | ✅ Passing |
| **PromptEngine** | ✅ Complete | `app/core/prompt_engine.py` | Yes | ✅ Passing |
| **HFTextGenService** | ✅ Complete | `app/services/hf_textgen_service.py` | Yes | ✅ 19/19 |
| **AssistantService** | ❌ Scaffold Only | `app/services/assistant_service.py` | Yes | ❌ Not Implemented |

### 1.2 Dependencies Already Initialized in AssistantService

```python
class AssistantService:
    def __init__(self):
        self.tokenizer = get_tokenizer_service()           # ✅ Ready
        self.embedding_service = EmbeddingService()        # ✅ Ready
        self.retrieval = get_retrieval_service()           # ✅ Ready
        self.context_builder = get_context_builder()       # ✅ Ready
        self.prompt_engine = get_prompt_engine()           # ✅ Ready
        self.textgen = get_textgen_service()               # ✅ Ready (already imported!)
```

**Key Finding:** HFTextGenService is **already imported and initialized** in AssistantService. We only need to implement the `query()` method logic.

---

## 2. Token Budget Analysis

### 2.1 Complete Token Flow

```
User Query (150 tokens max)
    ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: Query Validation & Tokenization                    │
│ • Validate: not empty, <500 chars                          │
│ • Count tokens: tokenizer.count_tokens(query)              │
│ • Budget allocated: 150 tokens                             │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 2: Embedding Generation                               │
│ • Generate 384-dim vector: embedding_service.generate()    │
│ • No token impact (vector, not text)                       │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 3: Chunk Retrieval (Vector Search)                    │
│ • Retrieve top-K chunks: retrieval.retrieve_top_chunks()   │
│ • Returns: (high_relevance, low_relevance)                 │
│ • No token budget yet (just retrieval)                     │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 4: Context Building (Token-Aware)                     │
│ • Fit chunks into budget: context_builder.build_context()  │
│ • Budget allocated: 1200 tokens                            │
│ • Returns: context_text, chunks_used, sources, etc.        │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 5: Prompt Assembly                                    │
│ • Build Llama-2 format: prompt_engine.build_prompt()       │
│ • Components:                                              │
│   - System prompt: 150 tokens (fixed)                      │
│   - Context: 1200 tokens (from Step 4)                     │
│   - User query: 150 tokens                                 │
│   - Format overhead: ~50 tokens                            │
│ • Total input: ~1550 tokens                                │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 6: Text Generation ⚠️ MISSING - TO IMPLEMENT          │
│ • Generate answer: textgen.generate(prompt)                │
│ • Budget allocated: 400 tokens max                         │
│ • Input + Output: 1550 + 400 = 1950 tokens                 │
│ • Model context window: 2048 tokens                        │
│ • Safety buffer: 98 tokens (✅ within budget)              │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 7: Response Formatting                                │
│ • Extract answer: prompt_engine.extract_answer()           │
│ • Build response dict with metadata                        │
│ • Return to user                                           │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Token Budget Breakdown

| Component | Tokens | Source | Validation |
|-----------|--------|--------|------------|
| **System Prompt** | 150 | `prompt_engine.SYSTEM_PROMPT` | Fixed, pre-measured |
| **Context Chunks** | 1200 | `context_builder` enforces | Strict greedy fitting |
| **User Query** | 150 | `_sanitize_user_query()` truncates | Max 500 chars → ~150 tokens |
| **Format Overhead** | ~50 | Llama-2 tags (`<s>`, `[INST]`, etc.) | Estimated |
| **Total Input** | ~1550 | Sum of above | ✅ Fits in 2048 window |
| **Output** | 400 | `assistant_max_output_tokens` | Hard limit enforced |
| **Total** | 1950 | Input + Output | ✅ 98 token buffer |

**Safety Margin:** 98 tokens (4.8% of context window) - sufficient for variability.

---

## 3. Integration Points

### 3.1 Current AssistantService.query() Method

**Status:** Currently raises `NotImplementedError`

```python
async def query(
    self,
    user_query: str,
    user_id: int,
    db: AsyncSession,
    max_sources: int = 5,
    include_metadata: bool = True
) -> Dict[str, Any]:
    # TODO: YOU implement full pipeline
    raise NotImplementedError(
        "AssistantService.query() flow needs implementation."
    )
```

### 3.2 Required Implementation Steps

#### Step 1: Query Validation ✅ (Straightforward)
```python
# Validate query
if not user_query or not user_query.strip():
    raise ValueError("Query cannot be empty")

# Count tokens for logging
query_tokens = self.tokenizer.count_tokens(user_query)
logger.info(f"Query tokens: {query_tokens}")
```

#### Step 2: Embedding Generation ✅ (Service Ready)
```python
# Generate embedding
query_embedding = self.embedding_service.generate(user_query)
logger.debug(f"Query embedding: {len(query_embedding)} dimensions")
```

#### Step 3: Chunk Retrieval ✅ (Service Ready)
```python
# Retrieve relevant chunks
high_rel, low_rel = await self.retrieval.retrieve_top_chunks(
    db=db,
    query_embedding=query_embedding,
    user_id=user_id,
    top_k=settings.assistant_top_k  # Default: 10
)
logger.info(f"Retrieved {len(high_rel)} high-rel, {len(low_rel)} low-rel chunks")
```

#### Step 4: Context Building ✅ (Service Ready)
```python
# Build context within token budget
context_result = self.context_builder.build_context(
    high_relevance_chunks=high_rel,
    low_relevance_chunks=low_rel,
    token_budget=settings.assistant_max_context_tokens  # 1200
)

context_text = context_result["context_text"]
sources = context_result["sources"]
logger.info(f"Context: {context_result['total_tokens']} tokens, {len(sources)} sources")
```

#### Step 5: Prompt Assembly ✅ (Service Ready)
```python
# Build prompt
final_prompt = self.prompt_engine.build_prompt(
    user_query=user_query,
    context_text=context_text,
    sources=sources
)
logger.debug(f"Prompt: {len(final_prompt)} chars")
```

#### Step 6: Text Generation ⚠️ **CRITICAL - TO IMPLEMENT**
```python
# Generate answer
try:
    raw_answer = self.textgen.generate(
        prompt=final_prompt,
        max_new_tokens=settings.assistant_max_output_tokens,  # 400
        temperature=settings.hf_generation_temperature,  # 0.2
        top_p=settings.assistant_model_top_p,  # 0.9
        repetition_penalty=settings.assistant_model_repition_penalty  # 1.1
    )
    logger.info(f"Generated answer: {len(raw_answer)} chars")
except GenerationError as e:
    logger.error(f"Generation failed: {e}")
    # Fallback response
    raw_answer = "I'm having trouble generating a response. Please try again."
```

#### Step 7: Response Formatting ✅ (Straightforward)
```python
# Extract clean answer
answer = self.prompt_engine.extract_answer_from_response(raw_answer)

# Build response dict
duration_ms = (time.time() - start_time) * 1000

response = {
    "answer": answer,
    "sources": sources,
    "metadata": {
        "chunks_used": len(context_result["chunks_used"]),
        "chunks_skipped": len(context_result["chunks_skipped"]),
        "context_tokens": context_result["total_tokens"],
        "query_tokens": query_tokens,
        "truncated": context_result["truncated"],
        "duration_ms": duration_ms
    } if include_metadata else None
}

logger.info(f"Query completed in {duration_ms:.0f}ms")
return response
```

---

## 4. Error Handling Strategy

### 4.1 Error Categories & Responses

| Error Type | Cause | User Message | HTTP Status |
|------------|-------|--------------|-------------|
| **ValueError** | Empty query, invalid input | "Please provide a valid question" | 400 |
| **GenerationError** | LLM API failure, timeout | "I'm having trouble right now. Please try again." | 500 |
| **ModelLoadError** | Service init failure | "Service temporarily unavailable" | 503 |
| **DatabaseError** | Retrieval failure | "Unable to access your notes right now" | 500 |
| **No Chunks** | User has no notes | Polite "no notes" message | 200 |

### 4.2 Error Handling Pattern

```python
try:
    # Main pipeline
    ...
except ValueError as e:
    logger.warning(f"Invalid input: {e}")
    return {
        "answer": "I need a valid question to help you explore your sermon notes.",
        "sources": [],
        "metadata": {"error": "invalid_input"}
    }
except GenerationError as e:
    logger.error(f"Generation failed: {e}")
    return {
        "answer": "I'm having trouble generating a response right now. Please try rephrasing your question or try again in a moment.",
        "sources": [],
        "metadata": {"error": "generation_failed"}
    }
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
    return {
        "answer": "Something went wrong. Please try again.",
        "sources": [],
        "metadata": {"error": "unexpected"}
    }
```

---

## 5. Edge Cases & Handling

### 5.1 No Relevant Chunks Found

**Scenario:** User query returns no high-relevance chunks (score < 0.6)

**Current Behavior:** `context_builder.build_context()` returns empty context

**Handling:**
```python
if not context_result["context_text"]:
    logger.info("No relevant context found - returning pre-generated response")
    return {
        "answer": self.prompt_engine.build_no_context_response(user_query),
        "sources": [],
        "metadata": {
            "no_context": True,
            "chunks_retrieved": len(low_rel)
        }
    }
```

**Benefit:** Saves LLM API costs by not calling generation when no context available.

### 5.2 User Has No Notes

**Scenario:** New user or user with no embeddings

**Current Behavior:** `retrieval.retrieve_top_chunks()` returns `([], [])`

**Handling:** Same as above (no relevant chunks)

### 5.3 Generation Returns Empty Output

**Scenario:** LLM returns empty string or only whitespace

**Current Behavior:** `_validate_output()` in HFTextGenService raises `GenerationError`

**Handling:** Caught by try/except, returns fallback message

### 5.4 Prompt Injection Attempt

**Scenario:** User tries to manipulate system prompt

**Current Behavior:** `prompt_engine._sanitize_user_query()` detects patterns and replaces with safe query

**Handling:** Already implemented - no additional action needed

---

## 6. Testing Strategy

### 6.1 Unit Tests Required

```python
# tests/test_assistant_service.py

class TestAssistantService:
    """Test AssistantService integration."""
    
    def test_query_with_valid_context(self):
        """Test successful query with relevant chunks."""
        # Mock all dependencies
        # Assert: answer generated, sources returned
    
    def test_query_with_no_context(self):
        """Test query when no relevant chunks found."""
        # Mock retrieval to return empty
        # Assert: no_context response, no LLM call
    
    def test_query_with_generation_error(self):
        """Test graceful handling of LLM failure."""
        # Mock textgen to raise GenerationError
        # Assert: fallback message returned
    
    def test_query_with_empty_query(self):
        """Test validation of empty query."""
        # Assert: ValueError raised or handled
    
    def test_token_budget_enforcement(self):
        """Test that token budgets are respected."""
        # Assert: context <= 1200, output <= 400
```

### 6.2 Integration Tests Required

```python
# tests/integration/test_assistant_rag_pipeline.py

async def test_end_to_end_query():
    """Test complete RAG pipeline with real database."""
    # Setup: Create user, notes with embeddings
    # Execute: Run full query
    # Assert: Valid response with sources
    # Cleanup: Delete test data
```

### 6.3 Manual Testing Checklist

- [ ] Query with relevant context → Answer with citations
- [ ] Query with no relevant context → Polite "no notes" message
- [ ] Query with prompt injection attempt → Safe query replacement
- [ ] Query from user with no notes → Helpful onboarding message
- [ ] Very long query (>500 chars) → Truncated to 150 tokens
- [ ] LLM API failure → Graceful fallback message
- [ ] Check metrics logged (duration, tokens, chunks)

---

## 7. Configuration Checklist

### 7.1 Required Environment Variables

```env
# HuggingFace API (for text generation)
HF_API_KEY=hf_xxxxxxxxxxxxxxxxxxxxx  # ⚠️ MUST BE SET

# Generation settings (already in config.py)
HF_USE_API=true
HF_GENERATION_MODEL=meta-llama/Llama-2-7b-chat-hf
HF_GENERATION_TEMPERATURE=0.2
HF_GENERATION_TIMEOUT=60

# Token budgets (already in config.py)
ASSISTANT_MODEL_CONTEXT_WINDOW=2048
ASSISTANT_MAX_OUTPUT_TOKENS=400
ASSISTANT_MAX_CONTEXT_TOKENS=1200
ASSISTANT_TOP_K=10
```

### 7.2 Configuration Validation

Before deployment, verify:
```python
from app.core.config import settings

assert settings.huggingface_api_key, "HF_API_KEY not set!"
assert settings.hf_use_api is True, "API mode recommended for start"
assert settings.assistant_max_output_tokens == 400, "Output budget mismatch"
assert settings.assistant_max_context_tokens == 1200, "Context budget mismatch"
```

---

## 8. Implementation Roadmap

### Phase 1: Core Integration (2-3 hours)
- [ ] Implement AssistantService.query() with all 7 steps
- [ ] Add comprehensive error handling
- [ ] Add logging at each step
- [ ] Handle no-context edge case

### Phase 2: Testing (2-3 hours)
- [ ] Write unit tests for AssistantService
- [ ] Write integration test for full pipeline
- [ ] Manual testing with various queries
- [ ] Fix any bugs discovered

### Phase 3: Refinement (1-2 hours)
- [ ] Add response validation
- [ ] Optimize logging
- [ ] Add performance metrics
- [ ] Documentation updates

### Phase 4: Deployment (1 hour)
- [ ] Set HF_API_KEY in production .env
- [ ] Deploy updated code
- [ ] Smoke test in production
- [ ] Monitor first 50 queries

**Total Estimated Time:** 6-9 hours

---

## 9. Success Criteria

### Must Have (Phase 1)
✅ AssistantService.query() fully implemented  
✅ All 7 pipeline steps working  
✅ Error handling for common failures  
✅ No-context edge case handled  
✅ Token budgets enforced  
✅ Basic logging in place

### Should Have (Phase 2)
✅ Unit tests passing  
✅ Integration test passing  
✅ Manual testing complete  
✅ Generation quality validated

### Nice to Have (Phase 3+)
- Response caching for common queries
- Query classification (factual vs. reflective)
- Streaming responses
- Multi-turn conversation support

---

## 10. Risk Assessment

### High Risk
❌ **None** - All services tested and ready

### Medium Risk
⚠️ **HF API Rate Limits** - Mitigation: Monitor usage, implement caching  
⚠️ **Generation Quality** - Mitigation: Test with real queries, tune temperature

### Low Risk
✅ **Token Budget Violations** - Already enforced in services  
✅ **Prompt Injection** - Already sanitized  
✅ **Service Initialization** - All singletons tested

---

## 11. Monitoring & Observability

### Metrics to Track

```python
# Log at each step:
logger.info(
    "assistant_query_completed",
    extra={
        "user_id": user_id,
        "query_length": len(user_query),
        "query_tokens": query_tokens,
        "chunks_retrieved": len(high_rel) + len(low_rel),
        "chunks_used": len(context_result["chunks_used"]),
        "context_tokens": context_result["total_tokens"],
        "answer_length": len(answer),
        "duration_ms": duration_ms,
        "sources_count": len(sources),
        "truncated": context_result["truncated"],
        "no_context": not context_text
    }
)
```

### Alerts to Configure

- Generation error rate > 5%
- Average duration > 10 seconds
- No-context queries > 50%
- Token budget violations (should be 0%)

---

## 12. Next Steps

### Immediate Actions
1. ✅ **Mark Planning Complete** - This audit is comprehensive
2. ⏳ **Implement AssistantService.query()** - Use code from Section 3.2
3. ⏳ **Write Tests** - Use test plan from Section 6
4. ⏳ **Set HF_API_KEY** - Required before testing
5. ⏳ **Manual Testing** - Validate end-to-end flow

### Follow-Up Actions
- Create integration testing checklist document
- Write deployment runbook
- Document common troubleshooting scenarios
- Create example queries for testing

---

**Status:** ✅ PLANNING COMPLETE  
**Ready for Implementation:** YES  
**Confidence Level:** HIGH (all prerequisites verified)

---

**Document Prepared By:** GitHub Copilot  
**Review Status:** Ready for User Review  
**Next Phase:** Implementation (Todo #4)
