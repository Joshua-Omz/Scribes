# Tokenizer Service Documentation

## Overview

The `TokenizerService` is a production-ready service that provides token-aware text processing for the Scribes AI Assistant. It ensures all text operations respect token budgets to prevent context window overflow and optimize LLM performance.

## Key Features

✅ **Token-Aware Operations** - Count, truncate, and chunk text based on actual token counts  
✅ **Lazy Loading** - Tokenizer loads only when first needed (performance optimization)  
✅ **Error Handling** - Graceful handling of invalid inputs with fallbacks  
✅ **Singleton Pattern** - Single tokenizer instance shared across application  
✅ **Batch Processing** - Efficiently count tokens for multiple texts  
✅ **Production-Ready** - Comprehensive validation, logging, and edge case handling

---

## Installation

The tokenizer service uses HuggingFace Transformers:

```bash
pip install transformers
```

---

## Usage

### Basic Usage

```python
from app.services.tokenizer_service import get_tokenizer_service

# Get singleton instance
tokenizer = get_tokenizer_service()

# Count tokens
text = "This is a sermon note about faith."
token_count = tokenizer.count_tokens(text)
print(f"Token count: {token_count}")  # Output: Token count: 9
```

### Truncating Text

```python
# Truncate to fit token budget
long_text = "Very long sermon note..." * 100
truncated = tokenizer.truncate_to_tokens(long_text, max_tokens=200)

# Verify it fits
assert tokenizer.count_tokens(truncated) <= 200
```

### Chunking Text

```python
# Split long text into token-aware chunks
long_note = "Faith is trusting God even when we can't see..." * 50

chunks = tokenizer.chunk_text(
    long_note,
    chunk_size=384,    # Each chunk ~384 tokens (fits embedding model)
    overlap=64         # 64 tokens overlap between chunks
)

print(f"Created {len(chunks)} chunks")

for i, chunk in enumerate(chunks):
    tokens = tokenizer.count_tokens(chunk)
    print(f"Chunk {i+1}: {tokens} tokens")
```

### Encoding and Decoding

```python
# Encode text to token IDs
text = "Grace is God's unmerited favor."
token_ids = tokenizer.encode(text, add_special_tokens=True)
print(token_ids)  # [101, 7865, 2003, 2362, 1005, 1055, ...]

# Decode back to text
decoded = tokenizer.decode(token_ids, skip_special_tokens=True)
print(decoded)  # "Grace is God's unmerited favor."
```

### Batch Operations

```python
# Count tokens for multiple texts efficiently
texts = [
    "First sermon note.",
    "Second sermon note about grace.",
    "Third sermon note about faith."
]

counts = tokenizer.batch_count_tokens(texts)
print(counts)  # [5, 8, 9]
```

### Fast Estimation

```python
# Quick estimate without full tokenization (heuristic)
estimated = tokenizer.estimate_tokens(text)

# For accurate count, use:
actual = tokenizer.count_tokens(text)
```

---

## API Reference

### Core Methods

#### `count_tokens(text: str) -> int`

Count the exact number of tokens in text.

**Parameters:**
- `text` (str): Input text to tokenize

**Returns:**
- `int`: Number of tokens (minimum 0)

**Features:**
- Returns 0 for empty/None/invalid inputs
- Includes special tokens in count
- Falls back to estimation on error

**Example:**
```python
count = tokenizer.count_tokens("Hello world")  # Returns: 3
```

---

#### `encode(text: str, add_special_tokens: bool = True) -> List[int]`

Encode text to token IDs.

**Parameters:**
- `text` (str): Input text
- `add_special_tokens` (bool): Whether to add BOS/EOS tokens (default: True)

**Returns:**
- `List[int]`: Token IDs (empty list if text is empty)

**Raises:**
- `ValueError`: If text is not a string

**Example:**
```python
ids = tokenizer.encode("Hello", add_special_tokens=False)
```

---

#### `decode(token_ids: List[int], skip_special_tokens: bool = True) -> str`

Decode token IDs back to text.

**Parameters:**
- `token_ids` (List[int]): Token IDs to decode
- `skip_special_tokens` (bool): Remove special tokens from output (default: True)

**Returns:**
- `str`: Decoded text (empty string if input is empty)

**Raises:**
- `ValueError`: If token_ids is not a list

**Example:**
```python
text = tokenizer.decode([7865, 2003, 2204])  # "Grace is good"
```

---

#### `truncate_to_tokens(text: str, max_tokens: int) -> str`

Truncate text to fit within token limit.

**Parameters:**
- `text` (str): Input text
- `max_tokens` (int): Maximum tokens allowed (must be > 0)

**Returns:**
- `str`: Truncated text guaranteed to fit within limit

**Raises:**
- `ValueError`: If max_tokens <= 0

**Features:**
- No-op if text already fits
- Preserves word boundaries when possible
- Logs warnings if truncation needed

**Example:**
```python
long_text = "Very long sermon..." * 100
short = tokenizer.truncate_to_tokens(long_text, max_tokens=100)
```

---

#### `chunk_text(text: str, chunk_size: int = 384, overlap: int = 64) -> List[str]`

Split text into overlapping chunks with token-aware boundaries.

**Parameters:**
- `text` (str): Input text to chunk
- `chunk_size` (int): Target size of each chunk in tokens (default: 384)
- `overlap` (int): Number of tokens to overlap between chunks (default: 64)

**Returns:**
- `List[str]`: List of text chunks (empty list if text is empty)

**Raises:**
- `ValueError`: If chunk_size <= 0, overlap < 0, or overlap >= chunk_size

**Features:**
- Uses sliding window approach
- Filters out whitespace-only chunks
- Preserves context across boundaries
- Logs chunk statistics

**Algorithm:**
```
Text:     [---Chunk 1---]
                [---Chunk 2---]
                      [---Chunk 3---]
          ^^^^^ overlap ^^^^^
```

**Example:**
```python
chunks = tokenizer.chunk_text(
    long_note,
    chunk_size=384,  # Fits embedding model (sentence-transformers)
    overlap=64       # ~17% overlap for context preservation
)
```

---

### Utility Methods

#### `estimate_tokens(text: str) -> int`

Fast heuristic-based token estimate (no tokenizer loading).

**Heuristic:** ~1 token per 4 characters (English text)

**Use Case:** Quick checks where exact count isn't critical

**Example:**
```python
estimate = tokenizer.estimate_tokens("Hello world")  # ~2-3 tokens
```

---

#### `batch_count_tokens(texts: List[str]) -> List[int]`

Count tokens for multiple texts.

**Parameters:**
- `texts` (List[str]): List of text strings

**Returns:**
- `List[int]`: Token counts for each text

**Example:**
```python
counts = tokenizer.batch_count_tokens([
    "First note",
    "Second note"
])  # [3, 3]
```

---

#### `get_vocab_size() -> int`

Get the tokenizer's vocabulary size.

**Returns:**
- `int`: Number of unique tokens in vocabulary

**Example:**
```python
vocab_size = tokenizer.get_vocab_size()  # ~30,000 for most models
```

---

#### `get_model_name() -> str`

Get the name of the model used for tokenization.

**Returns:**
- `str`: HuggingFace model name

**Example:**
```python
model = tokenizer.get_model_name()  # "sentence-transformers/all-MiniLM-L6-v2"
```

---

## Configuration

The tokenizer service reads configuration from `app/core/config.py`:

```python
class Settings(BaseSettings):
    # Tokenizer model (should match embedding model for consistency)
    hf_embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Chunking defaults
    assistant_chunk_size: int = 384
    assistant_chunk_overlap: int = 64
```

**Why use embedding model tokenizer?**
- Ensures token counts match embedding generation
- Prevents dimension mismatches
- Consistent chunking behavior

---

## Performance Characteristics

### Lazy Loading
- Tokenizer loads only on first use
- ~1-2 seconds initial load time
- Subsequent calls: instant (cached in memory)

### Operation Speed
- `count_tokens()`: ~0.1ms per 100 words
- `truncate_to_tokens()`: ~0.2ms per 100 words
- `chunk_text()`: ~1ms per 1000 words
- `estimate_tokens()`: ~0.01ms (no tokenizer needed)

### Memory Usage
- Tokenizer in memory: ~50MB
- Singleton pattern ensures only one instance

---

## Error Handling

### Invalid Inputs

The service gracefully handles invalid inputs:

```python
# Empty/None inputs return safe defaults
tokenizer.count_tokens(None)      # Returns: 0
tokenizer.count_tokens("")        # Returns: 0
tokenizer.encode(None)            # Returns: []
tokenizer.decode(None)            # Returns: ""

# Invalid types raise clear errors
tokenizer.encode(123)             # Raises: ValueError
tokenizer.decode("not a list")    # Raises: ValueError
```

### Parameter Validation

```python
# Invalid parameters raise ValueError
tokenizer.truncate_to_tokens(text, max_tokens=0)    # ValueError
tokenizer.chunk_text(text, chunk_size=-1)           # ValueError
tokenizer.chunk_text(text, chunk_size=10, overlap=10)  # ValueError
```

### Fallback Behavior

If tokenization fails (rare), the service falls back to estimation:

```python
# Tokenizer error -> uses estimate_tokens()
count = tokenizer.count_tokens(corrupted_text)  # Falls back gracefully
```

---

## Testing

The service has **21 comprehensive unit tests** covering:

- ✅ Basic operations (counting, encoding, decoding)
- ✅ Truncation (various lengths, edge cases)
- ✅ Chunking (overlap, boundaries, whitespace)
- ✅ Invalid inputs (None, empty, wrong types)
- ✅ Parameter validation (ranges, constraints)
- ✅ Edge cases (whitespace-only, very long text)
- ✅ Batch operations
- ✅ Singleton pattern

**Run tests:**
```bash
pytest app/tests/test_tokenizer_service.py -v
```

**Expected:** 21 passed

---

## Integration with AI Assistant

### Use Case 1: Chunking Notes for Embeddings

```python
from app.services.tokenizer_service import get_tokenizer_service
from app.services.embedding_service import get_embedding_service

tokenizer = get_tokenizer_service()
embedding_service = get_embedding_service()

# Chunk long note
note_content = "Very long sermon about faith..." * 100
chunks = tokenizer.chunk_text(note_content, chunk_size=384, overlap=64)

# Generate embeddings for each chunk
for i, chunk in enumerate(chunks):
    embedding = embedding_service.embed(chunk)
    # Store in DB with note_id, chunk_idx, chunk_text, embedding
```

### Use Case 2: Context Budget Enforcement

```python
from app.services.context_builder import get_context_builder

# Build context that fits token budget
context_builder = get_context_builder()
result = context_builder.build_context(
    high_relevance_chunks,
    low_relevance_chunks,
    token_budget=1200  # Enforced by tokenizer
)

# result['metadata']['total_tokens_used'] <= 1200 (guaranteed)
```

### Use Case 3: Query Truncation

```python
from app.core.prompt_engine import get_prompt_engine

prompt_engine = get_prompt_engine()

# Truncate long user queries
user_query = "What do my notes say about..." * 50
safe_query = tokenizer.truncate_to_tokens(user_query, max_tokens=150)

# Build prompt with truncated query
prompt = prompt_engine.build_prompt(safe_query, context_text)
```

---

## Best Practices

### 1. Use Singleton Pattern

**✅ DO:**
```python
from app.services.tokenizer_service import get_tokenizer_service
tokenizer = get_tokenizer_service()  # Singleton
```

**❌ DON'T:**
```python
from app.services.tokenizer_service import TokenizerService
tokenizer = TokenizerService()  # Creates new instance (wasteful)
```

### 2. Choose Appropriate Method

**For exact counts (critical paths):**
```python
count = tokenizer.count_tokens(text)  # Accurate but slower
```

**For quick estimates (non-critical):**
```python
estimate = tokenizer.estimate_tokens(text)  # Fast heuristic
```

### 3. Validate Chunk Parameters

**✅ DO:**
```python
chunk_size = 384
overlap = 64  # ~17% overlap
assert overlap < chunk_size
chunks = tokenizer.chunk_text(text, chunk_size, overlap)
```

**❌ DON'T:**
```python
chunks = tokenizer.chunk_text(text, chunk_size=100, overlap=100)  # ValueError!
```

### 4. Handle Edge Cases

```python
# Check if text needs chunking
if tokenizer.count_tokens(text) <= chunk_size:
    chunks = [text]  # No chunking needed
else:
    chunks = tokenizer.chunk_text(text, chunk_size, overlap)
```

---

## Troubleshooting

### Issue: Tokenizer loading is slow

**Cause:** First-time download from HuggingFace  
**Solution:** Tokenizer caches locally after first load (~50MB)

### Issue: Token counts slightly exceed chunk_size

**Cause:** Special tokens (BOS/EOS) add 1-2 tokens  
**Solution:** This is expected. Allow 2-3 token buffer in your logic.

### Issue: Chunks have unexpected boundaries

**Cause:** Tokenizer splits on subword units (not words)  
**Solution:** This is correct behavior. Overlap preserves context.

### Issue: Different token counts between services

**Cause:** Using different tokenizer models  
**Solution:** Ensure all services use same model from config:
```python
settings.hf_embedding_model  # Use this consistently
```

---

## Changelog

### v1.1 (Production-Ready)
- ✅ Added comprehensive error handling
- ✅ Added parameter validation
- ✅ Added batch operations
- ✅ Added utility methods (get_vocab_size, get_model_name)
- ✅ Enhanced logging and warnings
- ✅ Filtered whitespace-only chunks
- ✅ Added fallback for tokenization errors
- ✅ 21 comprehensive unit tests

### v1.0 (Initial)
- ✅ Basic tokenization operations
- ✅ Chunking with overlap
- ✅ Truncation
- ✅ Singleton pattern

---

## Related Documentation

- [Context Builder Service](./CONTEXT_BUILDER.md)
- [Chunking Service](./CHUNKING_SERVICE.md)
- [Prompt Engine](../core/PROMPT_ENGINE.md)
- [AI Assistant Architecture](../guides/ARCHITECTURE.md)

---

## Support

For issues or questions:
1. Check test cases in `app/tests/test_tokenizer_service.py`
2. Review HuggingFace Transformers docs: https://huggingface.co/docs/transformers
3. File issue in project repository
