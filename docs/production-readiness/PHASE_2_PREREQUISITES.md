# Phase 2 Prerequisites: Essential Knowledge Guide

**Purpose:** Comprehensive preparation for AI-specific caching implementation  
**Audience:** Backend developers implementing semantic caching  
**Reading Time:** 45-60 minutes  
**Prerequisite:** Basic Python, FastAPI, and Redis knowledge

---

## 📚 Table of Contents

1. [Core Concepts](#core-concepts)
2. [Technologies & Libraries](#technologies--libraries)
3. [RAG Pipeline Deep Dive](#rag-pipeline-deep-dive)
4. [Caching Fundamentals](#caching-fundamentals)
5. [Semantic Similarity](#semantic-similarity)
6. [Redis Data Structures](#redis-data-structures)
7. [Implementation Patterns](#implementation-patterns)
8. [Performance Metrics](#performance-metrics)
9. [Testing Strategy](#testing-strategy)
10. [Glossary](#glossary)

---

## 1. Core Concepts

### 1.1 What is Caching?

**Definition:** Storing computed results to avoid expensive recomputation.

**Simple analogy:**
```
Without cache:
User asks "2 + 2" → Calculator computes → Returns 4
User asks "2 + 2" → Calculator computes → Returns 4 (waste!)

With cache:
User asks "2 + 2" → Calculator computes → Cache it → Returns 4
User asks "2 + 2" → Check cache → Found! → Returns 4 (fast!)
```

**Key terms:**
- **Cache Hit:** Found in cache (fast, cheap)
- **Cache Miss:** Not in cache (slow, expensive)
- **Hit Rate:** Percentage of requests served from cache (target: 60%+)
- **TTL (Time To Live):** How long data stays in cache before expiring

---

### 1.2 Why Semantic Caching?

**Traditional caching (what gateway does):**
```python
# URL-based cache key
cache_key = "GET /api/assistant?q=What+is+faith"

# Problem: Different wording = different URL = cache miss
"What is faith?" → cache miss
"Define faith" → cache miss
"Explain faith" → cache miss
# 3 requests, 3 API calls, 0 cache hits
```

**Semantic caching (what we're building):**
```python
# Meaning-based cache key
cache_key = hash(embedding_vector)  # Same for similar meanings

# Solution: Similar meaning = same embedding = cache hit!
"What is faith?" → embedding [0.2, 0.8, ...] → cache miss → store
"Define faith" → embedding [0.21, 0.79, ...] → similar! → cache hit ✅
"Explain faith" → embedding [0.19, 0.81, ...] → similar! → cache hit ✅
# 3 requests, 1 API call, 2 cache hits (66% savings!)
```

**Key insight:** We cache based on **meaning**, not **exact text match**.

---

### 1.3 RAG Pipeline Overview

**RAG = Retrieval-Augmented Generation**

Think of it like an open-book exam:
1. Student reads question (Query)
2. Student searches textbook for relevant chapters (Retrieval)
3. Student writes answer using textbook info (Generation)

**The 7 steps:**
```
Step 1: Validate Query
   ↓
Step 2: Embed Query (convert to 384-dim vector)
   ↓
Step 3: Vector Search (find similar sermon chunks)
   ↓
Step 4: Build Context (assemble relevant text)
   ↓
Step 5: Assemble Prompt (system + context + query)
   ↓
Step 6: Generate Answer (call LLM API)
   ↓
Step 7: Post-Process (clean up, add citations)
```

**Where caching helps:**
- **After Step 2:** Cache embeddings (expensive to compute)
- **After Step 4:** Cache context assembly (expensive DB queries)
- **After Step 6:** Cache complete answers (most expensive - LLM call)

---

## 2. Technologies & Libraries

### 2.1 Redis (In-Memory Data Store)

**What is Redis?**
- In-memory database (data stored in RAM, not disk)
- Super fast (<1ms read/write latency)
- Supports key-value storage
- Built-in TTL (automatic expiration)

**Why Redis for caching?**
- **Speed:** RAM is 1000x faster than disk
- **Distributed:** Multiple app instances share same cache
- **Persistence:** Can save to disk (survives restarts)
- **Simple:** Easy to use, battle-tested

**Basic Redis operations:**
```python
import redis

# Connect
r = redis.Redis(host='localhost', port=6379, db=0)

# Set with TTL
r.setex('my_key', 3600, 'my_value')  # Expires in 1 hour

# Get
value = r.get('my_key')  # Returns 'my_value' or None

# Delete
r.delete('my_key')
```

**Redis data types we'll use:**
- **String:** Store JSON, embeddings, complete responses
- **Hash:** Store structured data (metadata)
- **Sorted Set:** For similarity search (advanced)

---

### 2.2 aiocache (Python Async Caching Library)

**What is aiocache?**
- Python library that simplifies caching
- Async-friendly (works with FastAPI)
- Supports multiple backends (Redis, Memcached, Memory)
- Handles serialization automatically

**Why aiocache?**
- Cleaner code than raw Redis commands
- Automatic serialization (Python objects ↔ Redis)
- Decorator pattern (easy to add caching)
- TTL management built-in

**Basic aiocache usage:**
```python
from aiocache import Cache

# Create cache
cache = Cache(Cache.REDIS, endpoint="localhost", port=6379, namespace="ai")

# Set
await cache.set("my_key", {"data": "value"}, ttl=3600)

# Get
result = await cache.get("my_key")  # Returns dict or None

# Decorator pattern
from aiocache import cached

@cached(ttl=3600, key="user:{user_id}")
async def expensive_operation(user_id):
    # This runs only on cache miss
    return await slow_computation()
```

---

### 2.3 sentence-transformers (Embedding Library)

**What are embeddings?**
Text → Vector (array of numbers that represents meaning)

**Example:**
```python
"faith" → [0.23, -0.45, 0.67, ..., 0.12]  # 384 numbers
"belief" → [0.21, -0.43, 0.69, ..., 0.14]  # Similar numbers!
"car" → [-0.67, 0.82, -0.21, ..., 0.45]  # Different numbers
```

**Why embeddings?**
- Captures semantic meaning
- Math operations work on vectors
- Can measure similarity (cosine distance)

**sentence-transformers usage:**
```python
from sentence_transformers import SentenceTransformer

# Load model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Create embedding
text = "What is faith?"
embedding = model.encode(text)  # Returns numpy array [384 floats]

# Embedding is now a vector we can cache/compare
```

---

### 2.4 HuggingFace Inference API

**What is HuggingFace?**
- Platform for AI models
- Provides hosted API for LLM inference
- We use: Llama-3.2-3B-Instruct

**Why HuggingFace?**
- No model hosting required (they handle it)
- Pay per request (cost-effective for small scale)
- Professional uptime & support

**Cost structure:**
```python
# Pricing (approximate)
input_cost = tokens * 0.0000002  # $0.0000002 per input token
output_cost = tokens * 0.0000006  # $0.0000006 per output token

# Example query
query_tokens = 45
context_tokens = 850
output_tokens = 120

input_cost = (45 + 850) * 0.0000002 = 0.000179
output_cost = 120 * 0.0000006 = 0.000072
total = 0.000251 (~$0.00026 per request)
```

**Why caching matters:** At 1000 requests/day, that's $0.26/day → $7.80/month

---

### 2.5 msgpack (Serialization Library)

**What is serialization?**
Converting Python objects → bytes (for storage)

**Why msgpack?**
- **Faster than JSON** (2-3x)
- **Smaller size** (binary format)
- **Python-friendly** (handles numpy arrays)

**JSON vs msgpack:**
```python
import json
import msgpack
import numpy as np

# Example: Store embedding vector
embedding = np.array([0.1, 0.2, 0.3])

# JSON (doesn't support numpy directly)
json_data = json.dumps(embedding.tolist())  # Convert to list first
# Size: ~30 bytes

# msgpack (supports numpy)
msgpack_data = msgpack.packb(embedding, use_bin_type=True)
# Size: ~15 bytes (50% smaller!)
```

**In our cache:**
```python
from aiocache import Cache
from aiocache.serializers import MsgPackSerializer

cache = Cache(
    Cache.REDIS,
    serializer=MsgPackSerializer()  # Use msgpack
)
```

---

## 3. RAG Pipeline Deep Dive

### 3.1 Current Implementation (No Caching)

**File:** `app/services/ai/assistant_service.py`

**Step-by-step flow:**
```python
async def query(user_id: int, query_text: str, db: AsyncSession):
    # Step 1: Validate & truncate query
    if len(query_text) > 500:
        query_text = truncate(query_text, 150)  # tokens
    
    # Step 2: Embed query (EXPENSIVE: 200ms + API cost)
    query_embedding = await embedding_service.embed(query_text)
    
    # Step 3: Vector search (DB query: ~100ms)
    chunks = await note_repo.search_by_embedding(
        embedding=query_embedding,
        user_id=user_id,
        limit=5
    )
    
    # Step 4: Build context (EXPENSIVE: DB + assembly)
    if not chunks:
        return no_context_response()  # Fast path!
    
    context = build_context(chunks, max_tokens=1200)
    
    # Step 5: Assemble prompt
    prompt = f"""System: {SYSTEM_PROMPT}
    Context: {context}
    Question: {query_text}"""
    
    # Step 6: Generate answer (MOST EXPENSIVE: 3.5s + $0.00026)
    response = await hf_service.chat_completion(prompt)
    
    # Step 7: Post-process
    answer = clean_response(response)
    
    return {
        "answer": answer,
        "sources": chunks,
        "metadata": {...}
    }
```

**Bottlenecks (what we'll cache):**
1. **Step 2:** `embed(query_text)` - 200ms + cost
2. **Step 4:** `build_context(chunks)` - DB queries + assembly
3. **Step 6:** `chat_completion(prompt)` - 3.5s + $0.00026

---

### 3.2 Token Budget Management

**What are tokens?**
Tokens ≈ words (roughly 1 token = 0.75 words)

**Our token limits:**
```python
MAX_QUERY_TOKENS = 150      # User's question
MAX_CONTEXT_TOKENS = 1200   # Retrieved sermon content
MAX_OUTPUT_TOKENS = 400     # AI's answer

TOTAL_BUDGET = 2048 tokens  # Model limit
```

**Why it matters for caching:**
- Longer queries = more expensive
- More context = higher LLM cost
- Cache key must include token counts

**Example:**
```python
# Short query (cheap)
query = "What is faith?"
tokens = 4
cost = 0.00020

# Long query (expensive)
query = "Can you explain the theological concept of faith..."
tokens = 150
cost = 0.00026

# Cache hit saves MORE for expensive queries!
```

---

### 3.3 Embedding Similarity

**How we measure similarity:**

**Cosine similarity:**
```python
import numpy as np

def cosine_similarity(vec1, vec2):
    """
    Returns: -1 (opposite) to 1 (identical)
    Typically: >0.85 = similar meaning
    """
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    return dot_product / (norm1 * norm2)

# Example
faith_vec = [0.2, 0.8, -0.1]
belief_vec = [0.21, 0.79, -0.09]
car_vec = [-0.5, 0.3, 0.6]

similarity(faith_vec, belief_vec)  # 0.98 (very similar!)
similarity(faith_vec, car_vec)     # 0.12 (not similar)
```

**Threshold for cache hit:**
```python
SIMILARITY_THRESHOLD = 0.85  # Adjustable

if similarity(new_query, cached_query) >= 0.85:
    return cached_response  # Close enough!
else:
    generate_new_response()
```

---

## 4. Caching Fundamentals

### 4.1 Cache Key Design

**What is a cache key?**
Unique identifier for cached data (like a dictionary key)

**Bad cache key (too specific):**
```python
# Every typo/variation = different key = cache miss
key = f"query:{query_text}"

"What is faith?" → cache miss
"What is faith" → cache miss (no question mark!)
"what is faith?" → cache miss (lowercase!)
```

**Good cache key (semantic):**
```python
# Based on meaning (embedding hash)
embedding = embed(query_text)
key = f"query:emb:{hash(embedding)}"

"What is faith?" → hash(emb) = "abc123"
"Define faith" → hash(emb) = "abc124" (similar!)
"Explain faith" → hash(emb) = "abc122" (similar!)

# Use similarity search to find close matches
```

**Cache key components:**
```python
# L1: Query result cache
key = f"ai:query:{user_id}:{query_hash}:{context_ids_hash}"
# Includes: user (personalized) + query + context used

# L2: Embedding cache
key = f"ai:embedding:{query_text_hash}"
# Only query text (same for all users)

# L3: Context cache
key = f"ai:context:{user_id}:{embedding_hash}"
# User + query meaning
```

---

### 4.2 TTL (Time To Live) Strategy

**What is TTL?**
How long data stays in cache before automatic deletion.

**TTL trade-offs:**

| TTL | Pros | Cons | Use Case |
|-----|------|------|----------|
| **Short (1h)** | Fresh data | More cache misses | Frequently changing data |
| **Medium (24h)** | Balanced | Some stale data | Semi-static data |
| **Long (7d)** | High hit rate | May be outdated | Expensive-to-compute data |

**Our TTL strategy:**
```python
# L1: Query result cache
TTL = 24 hours
Reasoning: Sermon content changes rarely, users repeat questions

# L2: Embedding cache  
TTL = 7 days
Reasoning: Embeddings never change (deterministic), very expensive

# L3: Context cache
TTL = 1 hour
Reasoning: Context is cheap to rebuild, user's notes may change
```

**Invalidation (when user adds/edits notes):**
```python
# When user creates/updates note:
async def on_note_change(user_id: int):
    # Clear user's cached contexts (L3)
    await cache.delete_pattern(f"ai:context:{user_id}:*")
    
    # Keep query results (L1) - still valid
    # Keep embeddings (L2) - unchanged
```

---

### 4.3 Cache Eviction Policies

**What is eviction?**
When cache is full, which items to remove?

**Common policies:**

1. **LRU (Least Recently Used)** - Remove oldest accessed item
   ```python
   # Good for: Items that are used together tend to be used again
   # Our use: L3 context cache (memory-based)
   ```

2. **LFU (Least Frequently Used)** - Remove least accessed item
   ```python
   # Good for: Popular items should stay
   # Our use: Not using (Redis handles this)
   ```

3. **TTL-based** - Remove expired items
   ```python
   # Good for: Time-sensitive data
   # Our use: L1 and L2 (Redis automatic)
   ```

**Redis eviction config:**
```python
# When Redis runs out of memory:
maxmemory_policy = "allkeys-lru"  # Remove any key, LRU order

# For our use case:
maxmemory_policy = "volatile-lru"  # Only remove keys with TTL
```

---

### 4.4 Cache Warming

**What is cache warming?**
Pre-populating cache before users request data.

**When to use:**
```python
# Scenario: You know users will ask certain questions

# Cold cache (user waits):
User asks "What is salvation?" → cache miss → 3.5s response

# Warm cache (pre-computed):
await warm_cache([
    "What is salvation?",
    "What is faith?",
    "What is grace?"
])
User asks "What is salvation?" → cache hit → 0.5s response ✅
```

**Our approach (Phase 2):**
- Start with cold cache (no warming)
- Let organic traffic warm it naturally
- Phase 3+: Consider warming popular queries

---

## 5. Semantic Similarity

### 5.1 What is an Embedding?

**Simple explanation:**
Text → List of numbers that capture meaning

**Visualization:**
```
2D space (simplified - actually 384 dimensions):

        faith (0.8, 0.6)
         ●
         
    belief (0.75, 0.65)
      ●

                           car (-0.3, 0.9)
                            ●

# Close points = similar meaning
# Far points = different meaning
```

**Actual embedding:**
```python
embedding = embed("What is faith?")
# Returns: numpy array of shape (384,)
# Example: [0.023, -0.456, 0.234, ..., 0.123]
#          384 numbers total
```

**Properties:**
- **Deterministic:** Same text → same embedding (always)
- **Semantic:** Similar meaning → similar vector
- **Dense:** Every dimension has meaning (not sparse)

---

### 5.2 Embedding Models

**What we use: `all-MiniLM-L6-v2`**

**Specs:**
- **Model size:** 80MB
- **Dimensions:** 384
- **Speed:** ~200ms per query (CPU)
- **Quality:** Good for semantic search
- **Context length:** 256 tokens (our queries are <150)

**Why this model?**
- Small enough to run in service
- Fast enough for real-time
- Good enough quality
- Free (no API costs)

**Alternative models:**
```python
# Smaller, faster, lower quality
'all-MiniLM-L12-v2'  # 120MB, 384 dim, faster

# Larger, slower, higher quality  
'all-mpnet-base-v2'  # 420MB, 768 dim, slower

# Our choice: Balance of speed/quality
'all-MiniLM-L6-v2'   # 80MB, 384 dim, balanced ✅
```

---

### 5.3 Similarity Metrics

**How to measure "how similar" two embeddings are:**

**1. Cosine Similarity (what we use)**
```python
def cosine_similarity(a, b):
    """Returns: -1 to 1 (1 = identical)"""
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

# Example thresholds:
0.95-1.0  → Almost identical ("faith" vs "Faith")
0.85-0.95 → Very similar ("faith" vs "belief")
0.70-0.85 → Related ("faith" vs "religion")
<0.70     → Different ("faith" vs "car")
```

**2. Euclidean Distance (not using)**
```python
def euclidean_distance(a, b):
    """Returns: 0 to infinity (0 = identical)"""
    return np.linalg.norm(a - b)

# Problem: Sensitive to vector magnitude
# Cosine better for text embeddings
```

**Our threshold:**
```python
SIMILARITY_THRESHOLD = 0.85  # Configurable

if cosine_similarity(new_embedding, cached_embedding) >= 0.85:
    # Close enough! Use cached response
    return cached_response
```

---

### 5.4 Embedding Cache Strategy

**Why cache embeddings?**

**Without cache:**
```python
# 10 similar queries per day per user
queries = [
    "What is faith?",
    "Define faith",
    "Explain faith to me",
    "What does faith mean?",
    ...
]

for query in queries:
    embed(query)  # 200ms each = 2 seconds total
```

**With cache:**
```python
for query in queries:
    key = hash(normalize(query))
    embedding = cache.get(key)
    
    if not embedding:
        embedding = embed(query)  # Only first time
        cache.set(key, embedding, ttl=7d)

# Result: 200ms + 9 cache hits (instant) = 200ms total
# Savings: 1.8 seconds (90% faster!)
```

**Cache key normalization:**
```python
def normalize_for_cache(text: str) -> str:
    """Make similar texts have same cache key"""
    text = text.lower()  # "Faith" → "faith"
    text = text.strip()  # Remove whitespace
    text = re.sub(r'[?.!,]', '', text)  # Remove punctuation
    return text

# Now these all hit same cache entry:
"What is faith?" → "what is faith"
"What is faith" → "what is faith" ✅ cache hit
"what is faith?" → "what is faith" ✅ cache hit
```

---

## 6. Redis Data Structures

### 6.1 Strings (Primary Use)

**What:** Store binary data or text

**Our use cases:**
```python
# Store JSON responses
await cache.set(
    "ai:query:123:abc",
    json.dumps({"answer": "...", "sources": [...]}),
    ttl=86400
)

# Store numpy embeddings (msgpack)
await cache.set(
    "ai:embedding:xyz",
    msgpack.packb(embedding_vector),
    ttl=604800
)

# Get
data = await cache.get("ai:query:123:abc")
response = json.loads(data)
```

---

### 6.2 Hashes (Structured Data)

**What:** Store dict-like data

**Our use case:** Metadata
```python
# Store query metadata
await redis.hset("ai:query:123:abc", mapping={
    "user_id": 123,
    "query": "What is faith?",
    "timestamp": 1703001234,
    "hit_count": 0,
    "cost_saved": 0.0
})

# Update hit count
await redis.hincrby("ai:query:123:abc", "hit_count", 1)
await redis.hincrbyfloat("ai:query:123:abc", "cost_saved", 0.00026)

# Get stats
stats = await redis.hgetall("ai:query:123:abc")
# {'hit_count': '5', 'cost_saved': '0.0013'}
```

---

### 6.3 Sorted Sets (Advanced - Phase 3+)

**What:** Store items with scores (for ranking)

**Future use:** Similarity search in Redis
```python
# Store embeddings with scores for similarity search
# (Advanced - not in Phase 2)

# Example: Find similar cached queries
await redis.zadd("ai:embeddings", {
    "query:abc": 0.95,  # Score = similarity to current query
    "query:def": 0.87,
    "query:ghi": 0.72
})

# Get most similar
similar = await redis.zrevrange("ai:embeddings", 0, 5)
# Returns: ['query:abc', 'query:def'] (top 2)
```

---

## 7. Implementation Patterns

### 7.1 Decorator Pattern (Easiest)

**What:** Use `@cached` decorator

**Example:**
```python
from aiocache import cached

@cached(
    ttl=86400,  # 24 hours
    key_builder=lambda f, *args, **kwargs: f"query:{kwargs['user_id']}:{hash(kwargs['query'])}"
)
async def expensive_ai_query(user_id: int, query: str):
    # This code only runs on cache miss
    embedding = await embed(query)
    context = await retrieve_context(embedding)
    answer = await generate_answer(context, query)
    return answer

# Usage (caching is automatic!)
result = await expensive_ai_query(user_id=123, query="What is faith?")
```

**Pros:** Simple, clean code  
**Cons:** Less control, harder to debug

---

### 7.2 Explicit Pattern (More Control)

**What:** Manually check cache

**Example:**
```python
async def query_with_cache(user_id: int, query: str):
    # Step 1: Check cache
    cache_key = f"query:{user_id}:{hash(query)}"
    cached = await cache.get(cache_key)
    
    if cached:
        logger.info(f"Cache HIT: {cache_key}")
        return cached  # Fast path!
    
    # Step 2: Cache miss - compute
    logger.info(f"Cache MISS: {cache_key}")
    
    embedding = await embed(query)
    context = await retrieve_context(embedding)
    answer = await generate_answer(context, query)
    
    result = {
        "answer": answer,
        "sources": context,
        "metadata": {...}
    }
    
    # Step 3: Store in cache
    await cache.set(cache_key, result, ttl=86400)
    
    return result
```

**Pros:** Full control, easy to debug  
**Cons:** More boilerplate code

---

### 7.3 Layered Pattern (Our Approach)

**What:** Multiple cache layers (L1, L2, L3)

**Example:**
```python
async def query_with_layered_cache(user_id: int, query: str):
    # L1: Check query result cache (fastest)
    cache_key = f"query:{user_id}:{hash(query)}"
    cached_result = await cache.get(cache_key)
    if cached_result:
        return cached_result  # Complete answer cached!
    
    # L2: Check embedding cache
    embedding_key = f"embedding:{hash(query)}"
    embedding = await cache.get(embedding_key)
    if not embedding:
        embedding = await embed(query)  # Expensive!
        await cache.set(embedding_key, embedding, ttl=604800)
    
    # L3: Check context cache
    context_key = f"context:{user_id}:{hash(embedding)}"
    context = await cache.get(context_key)
    if not context:
        context = await retrieve_context(embedding, user_id)  # DB query!
        await cache.set(context_key, context, ttl=3600)
    
    # Generate answer (always expensive)
    answer = await generate_answer(context, query)
    
    result = {"answer": answer, "sources": context}
    
    # Store complete result in L1
    await cache.set(cache_key, result, ttl=86400)
    
    return result
```

**Pros:** Maximum optimization  
**Cons:** Most complex

---

## 8. Performance Metrics

### 8.1 Cache Hit Rate

**Formula:**
```python
hit_rate = cache_hits / (cache_hits + cache_misses) * 100

# Example:
hits = 60
misses = 40
hit_rate = 60 / (60 + 40) * 100 = 60%
```

**Target by layer:**
- L1 (Query result): 40-50% (repeated exact questions)
- L2 (Embedding): 60-70% (similar questions)
- L3 (Context): 70-80% (recent searches)

**Combined:**
```python
# With 100 requests:
L1: 40 hits, 60 pass to L2
L2: 36 hits (60% of 60), 24 pass to L3
L3: 17 hits (70% of 24), 7 full computation

Total hits: 40 + 36 + 17 = 93
Hit rate: 93%
Only 7 requests hit LLM API (93% cost savings!)
```

---

### 8.2 Latency Metrics

**What to measure:**

```python
# Request latency breakdown
total_latency = (
    cache_check_time +      # <1ms (Redis)
    embedding_time +        # 0ms (cached) or 200ms (miss)
    context_retrieval_time + # 0ms (cached) or 100ms (miss)
    generation_time +       # 0ms (cached) or 3500ms (miss)
    serialization_time      # ~5ms
)

# Best case (full cache hit):
0.001 + 0 + 0 + 0 + 5 = ~5ms (700x faster!)

# Worst case (all cache miss):
0.001 + 200 + 100 + 3500 + 5 = ~3805ms (baseline)

# Average (60% hit rate):
weighted_average = 0.6 * 5ms + 0.4 * 3805ms = 1525ms (2.5x faster)
```

**Percentiles to track:**
```python
# P50 (median): 50% of requests faster than this
# P95: 95% of requests faster than this
# P99: 99% of requests faster than this

# Target with caching:
P50: <100ms (most requests cached)
P95: <2000ms (some cache misses)
P99: <4000ms (cold cache scenarios)
```

---

### 8.3 Cost Metrics

**Track these:**

```python
# Per request
request_cost = input_tokens * 0.0000002 + output_tokens * 0.0000006

# Daily
daily_requests = 1000
daily_cost = sum(request_costs)

# Savings
baseline_cost = daily_requests * avg_request_cost
actual_cost = cached_requests * 0 + uncached_requests * avg_request_cost
savings = baseline_cost - actual_cost
savings_percent = savings / baseline_cost * 100

# Example:
baseline = 1000 * 0.00026 = $0.26/day
actual = (600 * 0) + (400 * 0.00026) = $0.104/day
savings = $0.156/day (60% reduction)
```

---

### 8.4 Memory Usage

**Cache size calculation:**

```python
# Per embedding
embedding_size = 384 floats * 4 bytes = 1,536 bytes (~1.5KB)

# Per query result
result_size = json.dumps(response).encode('utf-8')
# Approximate: 2-5KB per response

# Redis memory estimate
total_items = 10000  # 10k cached queries
avg_item_size = 3KB
total_memory = 10000 * 3KB = 30MB

# Very manageable! Redis can easily handle gigabytes
```

**Memory monitoring:**
```python
# Check Redis memory usage
info = await redis.info('memory')
used_memory = info['used_memory_human']  # e.g., "30.5M"
maxmemory = info['maxmemory_human']      # e.g., "1G"
```

---

## 9. Testing Strategy

### 9.1 Unit Tests

**Test cache operations:**
```python
import pytest
from app.services.ai.caching import QueryCache

@pytest.mark.asyncio
async def test_cache_hit():
    cache = QueryCache()
    
    # Store
    await cache.set("test_key", {"answer": "test"}, ttl=3600)
    
    # Retrieve
    result = await cache.get("test_key")
    assert result["answer"] == "test"

@pytest.mark.asyncio
async def test_cache_miss():
    cache = QueryCache()
    result = await cache.get("nonexistent_key")
    assert result is None

@pytest.mark.asyncio
async def test_ttl_expiration():
    cache = QueryCache()
    await cache.set("short_ttl", "data", ttl=1)
    
    # Immediate get: should exist
    assert await cache.get("short_ttl") == "data"
    
    # Wait for expiration
    await asyncio.sleep(2)
    
    # Should be gone
    assert await cache.get("short_ttl") is None
```

---

### 9.2 Integration Tests

**Test with real AI pipeline:**
```python
@pytest.mark.asyncio
async def test_query_cache_integration():
    assistant = AssistantService()
    
    # First query (cache miss)
    start = time.time()
    result1 = await assistant.query(user_id=1, query="What is faith?")
    duration1 = time.time() - start
    
    assert duration1 > 3.0  # Should take full time (LLM call)
    
    # Second query (cache hit)
    start = time.time()
    result2 = await assistant.query(user_id=1, query="What is faith?")
    duration2 = time.time() - start
    
    assert duration2 < 0.1  # Should be instant (cached)
    assert result1["answer"] == result2["answer"]  # Same answer

@pytest.mark.asyncio  
async def test_semantic_similarity():
    assistant = AssistantService()
    
    # Query 1
    result1 = await assistant.query(user_id=1, query="What is faith?")
    
    # Similar query (should hit cache)
    result2 = await assistant.query(user_id=1, query="Define faith")
    
    # Should be similar (maybe not identical due to context)
    assert similarity(result1["answer"], result2["answer"]) > 0.8
```

---

### 9.3 Load Tests

**Test cache under load:**
```python
import asyncio
from locust import HttpUser, task

class AIAssistantUser(HttpUser):
    @task
    def query_assistant(self):
        self.client.post("/assistant/query", json={
            "query": random.choice([
                "What is faith?",
                "What is love?",
                "What is grace?",
                "What is salvation?"
            ])
        })

# Run: locust -f load_test.py --users 100 --spawn-rate 10
# Goal: Verify cache hit rate > 60% under realistic load
```

---

## 10. Glossary

**A-F:**
- **aiocache:** Python async caching library
- **Cache Hit:** Found in cache (fast, cheap)
- **Cache Miss:** Not in cache (slow, expensive)
- **Cache Key:** Unique identifier for cached data
- **Cache Warming:** Pre-populating cache
- **Cosine Similarity:** Metric for vector similarity (-1 to 1)
- **Embedding:** Text converted to vector (384 floats)
- **Eviction Policy:** Rule for what to remove when cache full

**H-M:**
- **Hit Rate:** Percentage of cache hits (target 60%+)
- **LRU:** Least Recently Used eviction policy
- **LLM:** Large Language Model (e.g., Llama-3.2-3B)
- **Msgpack:** Binary serialization format (faster than JSON)

**N-S:**
- **Namespace:** Redis key prefix (e.g., "ai:")
- **RAG:** Retrieval-Augmented Generation
- **Redis:** In-memory data store
- **Semantic Similarity:** Same meaning, different words
- **Serialization:** Converting Python object ↔ bytes
- **sentence-transformers:** Library for creating embeddings

**T-Z:**
- **Token:** Unit of text (~0.75 words)
- **TTL:** Time To Live (expiration time)
- **Vector:** Array of numbers representing text
- **Vector Database:** Database optimized for similarity search (pgvector)

---

## ✅ Knowledge Check

Before proceeding with Phase 2 implementation, you should be able to answer:

### Basic Understanding
1. ✓ What is the difference between cache hit and cache miss?
2. ✓ Why is semantic caching better than URL-based caching for AI?
3. ✓ What are embeddings and why do we cache them?
4. ✓ What is TTL and why does it matter?

### Technical Knowledge
5. ✓ How does Redis work and why is it fast?
6. ✓ What are the 3 cache layers (L1, L2, L3) and what does each cache?
7. ✓ How do we measure similarity between queries?
8. ✓ What's the expected hit rate for each layer?

### Implementation  
9. ✓ Where in the code will each cache layer go?
10. ✓ How will we test cache effectiveness?
11. ✓ What metrics will we track?
12. ✓ What happens when user updates their notes?

**If you can answer these, you're ready for Phase 2 planning!** 🚀

---

## 📚 Further Reading

**Essential:**
1. [Redis Documentation](https://redis.io/docs/) - Redis basics
2. [aiocache Documentation](https://aiocache.readthedocs.io/) - Python caching
3. [sentence-transformers](https://www.sbert.net/) - Embeddings

**Deep Dives:**
4. [Vector Similarity Search](https://www.pinecone.io/learn/vector-similarity/) - Understanding embeddings
5. [Cache Strategies](https://aws.amazon.com/caching/best-practices/) - Caching patterns

**Our Codebase:**
6. `app/services/ai/assistant_service.py` - Current implementation
7. `app/services/ai/hf_textgen_service.py` - LLM integration
8. `app/repositories/note_repository.py` - Vector search

---

**Next Steps:**
1. Read this guide thoroughly (45-60 minutes)
2. Try examples in Python REPL to internalize concepts
3. Review current RAG pipeline code
4. Ready for: Phase 2 implementation planning

**Questions?** Document them before we start planning!

---

**Document Version:** 1.0  
**Created:** December 20, 2024  
**Status:** Prerequisite guide complete  
**Next:** Phase 2 detailed implementation plan
