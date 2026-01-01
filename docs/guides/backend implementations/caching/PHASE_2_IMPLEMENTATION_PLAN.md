  # Phase 2 Implementation Plan: AI-Specific Caching

**Status:** Ready to Implement  
**Priority:** HIGH  
**Estimated Effort:** 8 hours  
**Target Completion:** 1 week  
**Owner:** Backend Team

---

## 📋 Executive Summary

**Goal:** Implement three-layer semantic caching to reduce AI inference costs by 60-80% and improve response latency.

**Expected Outcomes:**
- ✅ 60%+ cache hit rate (combined L1/L2/L3)
- ✅ $65/month savings at 1k users (80% cost reduction)
- ✅ 2-3x faster response times (cached queries)
- ✅ Zero impact on answer quality

**Implementation Layers:**
1. **L1 (Query Result Cache):** Complete AI responses (24h TTL)
2. **L2 (Embedding Cache):** Query embeddings (7d TTL)
3. **L3 (Context Cache):** Retrieved sermon chunks (1h TTL)

---

## 🎯 Success Criteria

### Functional Requirements
- [ ] Cache hit rate >60% under realistic load (100 concurrent users)
- [ ] Response time <100ms for cached queries (P95)
- [ ] Cached responses identical to uncached (deterministic)
- [ ] Cache invalidation on user note changes (L3)
- [ ] Semantic similarity matching (threshold 0.85)

### Non-Functional Requirements
- [ ] Redis memory usage <100MB (10k cached queries)
- [ ] Zero impact on uncached query latency (<5ms overhead)
- [ ] Graceful degradation if Redis unavailable
- [ ] Comprehensive test coverage (>80%)
- [ ] Monitoring dashboard for hit rates and cost savings

---

## 🏗️ Architecture Overview

### Current Flow (No Caching)
```
User Query
    ↓
1. Validate (10ms)
    ↓
2. Embed Query (200ms + cost)
    ↓
3. Vector Search (100ms)
    ↓
4. Build Context (50ms)
    ↓
5. Generate Answer (3500ms + $0.00026)
    ↓
Response (Total: ~3860ms, $0.00026)
```

### Target Flow (With 3-Layer Caching)
```
User Query
    ↓
┌─────────────────────────────────────┐
│ L1: Check Query Result Cache        │
│ Key: hash(query + user + context)   │
│ TTL: 24h                             │
└─────────────────────────────────────┘
    │ HIT (40%)? → Return (5ms) ✅
    ↓ MISS (60%)
┌─────────────────────────────────────┐
│ L2: Check Embedding Cache            │
│ Key: hash(normalized_query)          │
│ TTL: 7d                               │
└─────────────────────────────────────┘
    │ HIT (60% of 60%)? → Use cached
    ↓ MISS (40% of 60%)
    Compute Embedding (200ms + cost)
    ↓
┌─────────────────────────────────────┐
│ L3: Check Context Cache              │
│ Key: hash(embedding + user)          │
│ TTL: 1h                               │
└─────────────────────────────────────┘
    │ HIT (70% of 24%)? → Use cached
    ↓ MISS (30% of 24%)
    Vector Search + Build Context (150ms)
    ↓
Generate Answer (3500ms + $0.00026)
    ↓
Store in all cache layers
    ↓
Response

Combined Hit Rate: 40% + (60% * 60%) + (40% * 70%) = 93%
Only 7% of requests hit LLM API (93% cost savings!)
```

---

## 📁 File Structure

### New Files to Create

```
app/
├── core/
│   └── cache.py                    # ✨ NEW: Redis cache manager
│
└── services/
    └── ai/
        ├── caching/                # ✨ NEW: Caching module
        │   ├── __init__.py
        │   ├── base.py            # Base cache interface
        │   ├── query_cache.py     # L1: Query result cache
        │   ├── embedding_cache.py # L2: Embedding cache
        │   ├── context_cache.py   # L3: Context cache
        │   └── metrics.py         # Cache metrics tracker
        │
        └── assistant_service.py    # 🔧 MODIFY: Add caching
```

### Files to Modify

```
Modified Files:
1. app/core/config.py              # Add Redis cache config
2. app/core/dependencies.py        # Add cache dependencies
3. app/services/ai/assistant_service.py  # Integrate caching
4. app/routes/assistant_routes.py  # Add cache stats endpoint
5. requirements.txt                 # Add Redis dependency (already present)
```

---

## 📝 Implementation Steps

### Phase 2.1: Foundation (2 hours)

**Goal:** Set up Redis cache infrastructure

#### Step 1.1: Configure Redis Cache Manager
**File:** `app/core/cache.py`

```python
"""
Redis cache manager for AI caching layers.
Provides async interface to Redis with connection pooling.
"""
from typing import Optional, Any
import redis.asyncio as redis
from aiocache import Cache
from aiocache.serializers import MsgPackSerializer
import msgpack
import numpy as np
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class RedisCacheManager:
    """Manages Redis connections and cache instances for AI services."""
    
    def __init__(self):
        self._redis_client: Optional[redis.Redis] = None
        self._cache: Optional[Cache] = None
    
    async def connect(self):
        """Initialize Redis connection pool."""
        try:
            self._redis_client = await redis.from_url(
                settings.REDIS_CACHE_URL,
                encoding="utf-8",
                decode_responses=False,  # Binary mode for msgpack
                max_connections=50,
                socket_timeout=5,
                socket_connect_timeout=5
            )
            
            # Test connection
            await self._redis_client.ping()
            logger.info("✅ Redis cache connected successfully")
            
            # Initialize aiocache wrapper
            self._cache = Cache(
                Cache.REDIS,
                endpoint=settings.REDIS_CACHE_HOST,
                port=settings.REDIS_CACHE_PORT,
                namespace="ai",
                serializer=MsgPackSerializer(),
                timeout=5
            )
            
        except Exception as e:
            logger.error(f"❌ Redis cache connection failed: {e}")
            self._redis_client = None
            self._cache = None
    
    async def disconnect(self):
        """Close Redis connection."""
        if self._redis_client:
            await self._redis_client.close()
            logger.info("Redis cache disconnected")
    
    @property
    def is_available(self) -> bool:
        """Check if Redis is connected."""
        return self._redis_client is not None
    
    @property
    def client(self) -> redis.Redis:
        """Get raw Redis client."""
        if not self._redis_client:
            raise RuntimeError("Redis cache not connected")
        return self._redis_client
    
    @property
    def cache(self) -> Cache:
        """Get aiocache instance."""
        if not self._cache:
            raise RuntimeError("Redis cache not connected")
        return self._cache


# Global cache manager instance
cache_manager = RedisCacheManager()


async def get_cache_manager() -> RedisCacheManager:
    """Dependency injection for cache manager."""
    if not cache_manager.is_available:
        await cache_manager.connect()
    return cache_manager
```

**Testing:**
```python
# Test Redis connection
pytest app/tests/unit/test_cache_manager.py -v
```

---

#### Step 1.2: Update Configuration
**File:** `app/core/config.py`

```python
# Add to Settings class:

# ============================================================================
# REDIS CACHE CONFIGURATION (Phase 2: AI Caching)
# ============================================================================
REDIS_CACHE_URL: str = Field(
    default="redis://localhost:6379/1",
    description="Redis URL for AI caching (L1/L2/L3)"
)
REDIS_CACHE_HOST: str = Field(
    default="localhost",
    description="Redis host for aiocache"
)
REDIS_CACHE_PORT: int = Field(
    default=6379,
    description="Redis port for aiocache"
)

# Cache TTL settings (seconds)
CACHE_QUERY_TTL: int = Field(
    default=86400,  # 24 hours
    description="L1: Query result cache TTL"
)
CACHE_EMBEDDING_TTL: int = Field(
    default=604800,  # 7 days
    description="L2: Embedding cache TTL"
)
CACHE_CONTEXT_TTL: int = Field(
    default=3600,  # 1 hour
    description="L3: Context cache TTL"
)

# Cache behavior
CACHE_SIMILARITY_THRESHOLD: float = Field(
    default=0.85,
    description="Cosine similarity threshold for semantic cache hits"
)
CACHE_ENABLED: bool = Field(
    default=True,
    description="Master switch for AI caching"
)
```

**Testing:**
```python
# Verify config loads correctly
python -c "from app.core.config import settings; print(settings.REDIS_CACHE_URL)"
```

---

#### Step 1.3: Update Dependencies
**File:** `app/core/dependencies.py`

```python
# Add cache manager dependency
from app.core.cache import get_cache_manager, RedisCacheManager

async def get_cache() -> RedisCacheManager:
    """Get cache manager for dependency injection."""
    return await get_cache_manager()
```

**Verify:**
```bash
# No syntax errors
python -m py_compile app/core/dependencies.py
```

---

### Phase 2.2: L1 - Query Result Cache (2 hours)

**Goal:** Cache complete AI responses

#### Step 2.1: Implement Query Cache
**File:** `app/services/ai/caching/query_cache.py`

```python
"""
L1: Query Result Cache
Caches complete AI responses to avoid expensive LLM calls.
TTL: 24 hours
Hit Rate Target: 40%
"""
from typing import Optional, Dict, Any
import hashlib
import json
from datetime import datetime
from app.core.cache import RedisCacheManager
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class QueryCache:
    """Caches complete query responses."""
    
    def __init__(self, cache_manager: RedisCacheManager):
        self.cache = cache_manager.cache
        self.client = cache_manager.client
        self.ttl = settings.CACHE_QUERY_TTL
    
    def _build_cache_key(
        self,
        user_id: int,
        query: str,
        context_ids: list[int]
    ) -> str:
        """
        Build cache key from query parameters.
        
        Key includes:
        - user_id: For personalization
        - query: The question
        - context_ids: Which chunks were used
        
        Returns: "query:v1:{hash}"
        """
        # Sort context_ids for consistency
        sorted_ids = sorted(context_ids)
        
        # Create composite key
        key_data = {
            "user_id": user_id,
            "query": query.strip().lower(),  # Normalize
            "context_ids": sorted_ids
        }
        
        # Hash it
        key_json = json.dumps(key_data, sort_keys=True)
        key_hash = hashlib.sha256(key_json.encode()).hexdigest()[:16]
        
        return f"query:v1:{key_hash}"
    
    async def get(
        self,
        user_id: int,
        query: str,
        context_ids: list[int]
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached query response.
        
        Returns: Cached response dict or None
        """
        if not settings.CACHE_ENABLED:
            return None
        
        cache_key = self._build_cache_key(user_id, query, context_ids)
        
        try:
            cached = await self.cache.get(cache_key)
            
            if cached:
                logger.info(f"✅ L1 CACHE HIT: {cache_key}")
                
                # Track hit in metadata
                await self._increment_hit_count(cache_key)
                
                return cached
            else:
                logger.debug(f"❌ L1 CACHE MISS: {cache_key}")
                return None
                
        except Exception as e:
            logger.error(f"L1 cache get error: {e}")
            return None  # Graceful degradation
    
    async def set(
        self,
        user_id: int,
        query: str,
        context_ids: list[int],
        response: Dict[str, Any]
    ):
        """Store query response in cache."""
        if not settings.CACHE_ENABLED:
            return
        
        cache_key = self._build_cache_key(user_id, query, context_ids)
        
        try:
            # Add metadata
            enriched_response = {
                **response,
                "_cache_metadata": {
                    "cached_at": datetime.utcnow().isoformat(),
                    "ttl": self.ttl,
                    "user_id": user_id
                }
            }
            
            # Store in cache
            await self.cache.set(cache_key, enriched_response, ttl=self.ttl)
            
            # Store hit counter metadata
            await self.client.hset(
                f"meta:{cache_key}",
                mapping={
                    "query": query[:100],  # Truncate
                    "user_id": user_id,
                    "created_at": datetime.utcnow().isoformat(),
                    "hit_count": 0,
                    "cost_saved": 0.0
                }
            )
            await self.client.expire(f"meta:{cache_key}", self.ttl)
            
            logger.info(f"💾 L1 CACHED: {cache_key}")
            
        except Exception as e:
            logger.error(f"L1 cache set error: {e}")
            # Don't fail request on cache error
    
    async def _increment_hit_count(self, cache_key: str):
        """Track cache hit statistics."""
        try:
            await self.client.hincrby(f"meta:{cache_key}", "hit_count", 1)
            
            # Estimate cost saved (average LLM call cost)
            avg_cost = 0.00026
            await self.client.hincrbyfloat(
                f"meta:{cache_key}",
                "cost_saved",
                avg_cost
            )
        except Exception as e:
            logger.warning(f"Failed to increment hit count: {e}")
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get L1 cache statistics."""
        try:
            # Get all metadata keys
            meta_keys = []
            async for key in self.client.scan_iter(match="meta:query:v1:*"):
                meta_keys.append(key)
            
            total_entries = len(meta_keys)
            total_hits = 0
            total_cost_saved = 0.0
            
            for key in meta_keys:
                meta = await self.client.hgetall(key)
                if meta:
                    total_hits += int(meta.get(b"hit_count", 0))
                    total_cost_saved += float(meta.get(b"cost_saved", 0.0))
            
            return {
                "layer": "L1_query_result",
                "total_entries": total_entries,
                "total_hits": total_hits,
                "total_cost_saved": round(total_cost_saved, 4),
                "avg_hits_per_entry": round(total_hits / total_entries, 2) if total_entries > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Failed to get L1 stats: {e}")
            return {"error": str(e)}
```

**Testing:**
```python
# Test L1 cache operations
pytest app/tests/unit/test_query_cache.py -v

# Test cases:
# - test_cache_hit_returns_cached_response
# - test_cache_miss_returns_none
# - test_cache_key_includes_user_id
# - test_cache_key_includes_context_ids
# - test_hit_count_increments
```

---

### Phase 2.3: L2 - Embedding Cache (2 hours)

**Goal:** Cache query embeddings to avoid recomputation

#### Step 3.1: Implement Embedding Cache
**File:** `app/services/ai/caching/embedding_cache.py`

```python
"""
L2: Embedding Cache
Caches query embeddings (384-dim vectors) to avoid expensive computation.
TTL: 7 days
Hit Rate Target: 60%
"""
from typing import Optional
import hashlib
import re
import numpy as np
import msgpack
from app.core.cache import RedisCacheManager
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class EmbeddingCache:
    """Caches query embeddings."""
    
    def __init__(self, cache_manager: RedisCacheManager):
        self.client = cache_manager.client
        self.ttl = settings.CACHE_EMBEDDING_TTL
    
    def _normalize_query(self, query: str) -> str:
        """
        Normalize query text for cache key consistency.
        
        Transformations:
        - Lowercase
        - Remove extra whitespace
        - Remove punctuation (keep alphanumeric + spaces)
        
        Example:
            "What is faith?" → "what is faith"
            "What is faith" → "what is faith"  (same key!)
        """
        # Lowercase
        normalized = query.lower()
        
        # Remove punctuation
        normalized = re.sub(r'[^\w\s]', '', normalized)
        
        # Normalize whitespace
        normalized = ' '.join(normalized.split())
        
        return normalized
    
    def _build_cache_key(self, query: str) -> str:
        """
        Build cache key from normalized query.
        
        Returns: "embedding:v1:{hash}"
        """
        normalized = self._normalize_query(query)
        query_hash = hashlib.sha256(normalized.encode()).hexdigest()[:16]
        return f"embedding:v1:{query_hash}"
    
    async def get(self, query: str) -> Optional[np.ndarray]:
        """
        Retrieve cached embedding.
        
        Returns: numpy array (384,) or None
        """
        if not settings.CACHE_ENABLED:
            return None
        
        cache_key = self._build_cache_key(query)
        
        try:
            cached_bytes = await self.client.get(cache_key)
            
            if cached_bytes:
                logger.info(f"✅ L2 CACHE HIT: {cache_key}")
                
                # Deserialize numpy array
                embedding = msgpack.unpackb(cached_bytes, raw=False)
                return np.array(embedding, dtype=np.float32)
            else:
                logger.debug(f"❌ L2 CACHE MISS: {cache_key}")
                return None
                
        except Exception as e:
            logger.error(f"L2 cache get error: {e}")
            return None
    
    async def set(self, query: str, embedding: np.ndarray):
        """Store embedding in cache."""
        if not settings.CACHE_ENABLED:
            return
        
        cache_key = self._build_cache_key(query)
        
        try:
            # Serialize numpy array
            embedding_bytes = msgpack.packb(
                embedding.tolist(),
                use_bin_type=True
            )
            
            # Store with TTL
            await self.client.setex(
                cache_key,
                self.ttl,
                embedding_bytes
            )
            
            logger.info(f"💾 L2 CACHED: {cache_key}")
            
        except Exception as e:
            logger.error(f"L2 cache set error: {e}")
    
    async def get_stats(self):
        """Get L2 cache statistics."""
        try:
            # Count cached embeddings
            count = 0
            async for _ in self.client.scan_iter(match="embedding:v1:*"):
                count += 1
            
            return {
                "layer": "L2_embedding",
                "total_entries": count,
                "ttl": self.ttl
            }
            
        except Exception as e:
            logger.error(f"Failed to get L2 stats: {e}")
            return {"error": str(e)}
```

**Testing:**
```python
# Test L2 cache operations
pytest app/tests/unit/test_embedding_cache.py -v

# Test cases:
# - test_normalization_consistency
# - test_cache_hit_returns_numpy_array
# - test_cache_miss_returns_none
# - test_similar_queries_same_key ("faith" vs "Faith")
# - test_numpy_array_serialization
```

---

### Phase 2.4: L3 - Context Cache (1 hour)

**Goal:** Cache retrieved sermon chunks

#### Step 4.1: Implement Context Cache
**File:** `app/services/ai/caching/context_cache.py`

```python
"""
L3: Context Cache
Caches retrieved sermon chunks to avoid DB queries.
TTL: 1 hour (short - user notes may change)
Hit Rate Target: 70%
"""
from typing import Optional, List, Dict, Any
import hashlib
import json
from app.core.cache import RedisCacheManager
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class ContextCache:
    """Caches retrieved context chunks."""
    
    def __init__(self, cache_manager: RedisCacheManager):
        self.cache = cache_manager.cache
        self.client = cache_manager.client
        self.ttl = settings.CACHE_CONTEXT_TTL
    
    def _build_cache_key(
        self,
        user_id: int,
        embedding_hash: str
    ) -> str:
        """
        Build cache key from user and embedding.
        
        Returns: "context:v1:{user_id}:{embedding_hash}"
        """
        return f"context:v1:{user_id}:{embedding_hash[:16]}"
    
    async def get(
        self,
        user_id: int,
        embedding_hash: str
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Retrieve cached context chunks.
        
        Returns: List of chunk dicts or None
        """
        if not settings.CACHE_ENABLED:
            return None
        
        cache_key = self._build_cache_key(user_id, embedding_hash)
        
        try:
            cached = await self.cache.get(cache_key)
            
            if cached:
                logger.info(f"✅ L3 CACHE HIT: {cache_key}")
                return cached
            else:
                logger.debug(f"❌ L3 CACHE MISS: {cache_key}")
                return None
                
        except Exception as e:
            logger.error(f"L3 cache get error: {e}")
            return None
    
    async def set(
        self,
        user_id: int,
        embedding_hash: str,
        chunks: List[Dict[str, Any]]
    ):
        """Store context chunks in cache."""
        if not settings.CACHE_ENABLED:
            return
        
        cache_key = self._build_cache_key(user_id, embedding_hash)
        
        try:
            await self.cache.set(cache_key, chunks, ttl=self.ttl)
            logger.info(f"💾 L3 CACHED: {cache_key}")
            
        except Exception as e:
            logger.error(f"L3 cache set error: {e}")
    
    async def invalidate_user(self, user_id: int):
        """
        Invalidate all cached contexts for a user.
        
        Called when user creates/updates/deletes notes.
        """
        try:
            pattern = f"context:v1:{user_id}:*"
            deleted = 0
            
            async for key in self.client.scan_iter(match=pattern):
                await self.client.delete(key)
                deleted += 1
            
            if deleted > 0:
                logger.info(f"🗑️  Invalidated {deleted} L3 cache entries for user {user_id}")
            
        except Exception as e:
            logger.error(f"L3 cache invalidation error: {e}")
    
    async def get_stats(self):
        """Get L3 cache statistics."""
        try:
            count = 0
            async for _ in self.client.scan_iter(match="context:v1:*"):
                count += 1
            
            return {
                "layer": "L3_context",
                "total_entries": count,
                "ttl": self.ttl
            }
            
        except Exception as e:
            logger.error(f"Failed to get L3 stats: {e}")
            return {"error": str(e)}
```

**Testing:**
```python
# Test L3 cache operations
pytest app/tests/unit/test_context_cache.py -v

# Test cases:
# - test_cache_hit_returns_chunks
# - test_cache_miss_returns_none
# - test_invalidate_user_clears_cache
# - test_different_users_different_cache
```

---

### Phase 2.5: Integration (2 hours)

**Goal:** Integrate caching into assistant service

#### Step 5.1: Modify Assistant Service
**File:** `app/services/ai/assistant_service.py`

```python
# Add to imports:
from app.services.ai.caching.query_cache import QueryCache
from app.services.ai.caching.embedding_cache import EmbeddingCache
from app.services.ai.caching.context_cache import ContextCache
from app.core.cache import RedisCacheManager
import hashlib

# Modify AssistantService class:

class AssistantService:
    def __init__(
        self,
        embedding_service: EmbeddingService,
        hf_service: HFTextGenService,
        note_repo: NoteRepository,
        cache_manager: Optional[RedisCacheManager] = None  # NEW
    ):
        self.embedding_service = embedding_service
        self.hf_service = hf_service
        self.note_repo = note_repo
        
        # Initialize cache layers
        if cache_manager and cache_manager.is_available:
            self.query_cache = QueryCache(cache_manager)
            self.embedding_cache = EmbeddingCache(cache_manager)
            self.context_cache = ContextCache(cache_manager)
            self.caching_enabled = True
        else:
            self.query_cache = None
            self.embedding_cache = None
            self.context_cache = None
            self.caching_enabled = False
    
    async def query(
        self,
        user_id: int,
        query_text: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Process user query with three-layer caching.
        
        Cache Layers:
        - L1: Complete response (if context IDs match)
        - L2: Query embedding
        - L3: Retrieved context chunks
        """
        # Step 1: Validate & truncate query
        if len(query_text) > 500:
            query_text = self._truncate_query(query_text, max_tokens=150)
        
        # Step 2: Embed query (with L2 caching)
        query_embedding = await self._get_embedding_cached(query_text)
        embedding_hash = hashlib.sha256(query_embedding.tobytes()).hexdigest()
        
        # Step 3: Vector search (with L3 caching)
        chunks = await self._get_context_cached(
            user_id=user_id,
            embedding=query_embedding,
            embedding_hash=embedding_hash,
            db=db
        )
        
        # Extract context IDs for L1 key
        context_ids = [chunk["chunk_id"] for chunk in chunks] if chunks else []
        
        # Step 4: Check L1 cache (complete response)
        if self.caching_enabled and self.query_cache:
            cached_response = await self.query_cache.get(
                user_id=user_id,
                query=query_text,
                context_ids=context_ids
            )
            if cached_response:
                # Full cache hit! Return immediately
                return cached_response
        
        # L1 cache miss - generate answer
        
        # Step 5: Build context
        if not chunks:
            return self._no_context_response(query_text)
        
        context_text = self._build_context(chunks, max_tokens=1200)
        
        # Step 6: Assemble prompt
        prompt = self._assemble_prompt(
            system_prompt=SYSTEM_PROMPT,
            context=context_text,
            query=query_text
        )
        
        # Step 7: Generate answer (EXPENSIVE!)
        response = await self.hf_service.chat_completion(prompt)
        
        # Step 8: Post-process
        answer = self._clean_response(response)
        
        result = {
            "answer": answer,
            "sources": chunks,
            "metadata": {
                "query": query_text,
                "cached": False,  # New response
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        # Step 9: Store in L1 cache
        if self.caching_enabled and self.query_cache:
            await self.query_cache.set(
                user_id=user_id,
                query=query_text,
                context_ids=context_ids,
                response=result
            )
        
        return result
    
    async def _get_embedding_cached(self, query: str) -> np.ndarray:
        """Get embedding with L2 caching."""
        # Try L2 cache first
        if self.caching_enabled and self.embedding_cache:
            cached_embedding = await self.embedding_cache.get(query)
            if cached_embedding is not None:
                return cached_embedding
        
        # L2 miss - compute embedding
        embedding = await self.embedding_service.embed(query)
        
        # Store in L2 cache
        if self.caching_enabled and self.embedding_cache:
            await self.embedding_cache.set(query, embedding)
        
        return embedding
    
    async def _get_context_cached(
        self,
        user_id: int,
        embedding: np.ndarray,
        embedding_hash: str,
        db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """Get context chunks with L3 caching."""
        # Try L3 cache first
        if self.caching_enabled and self.context_cache:
            cached_chunks = await self.context_cache.get(
                user_id=user_id,
                embedding_hash=embedding_hash
            )
            if cached_chunks is not None:
                return cached_chunks
        
        # L3 miss - do vector search
        chunks = await self.note_repo.search_by_embedding(
            embedding=embedding,
            user_id=user_id,
            limit=5,
            db=db
        )
        
        # Convert to dict format
        chunk_dicts = [
            {
                "chunk_id": chunk.id,
                "content": chunk.content,
                "note_id": chunk.note_id,
                "similarity": chunk.similarity
            }
            for chunk in chunks
        ]
        
        # Store in L3 cache
        if self.caching_enabled and self.context_cache:
            await self.context_cache.set(
                user_id=user_id,
                embedding_hash=embedding_hash,
                chunks=chunk_dicts
            )
        
        return chunk_dicts
    
    async def invalidate_user_cache(self, user_id: int):
        """
        Invalidate cached data when user modifies notes.
        
        Called by note CRUD endpoints.
        """
        if self.caching_enabled and self.context_cache:
            await self.context_cache.invalidate_user(user_id)
```

**Testing:**
```python
# Integration tests
pytest app/tests/integration/test_assistant_caching.py -v

# Test cases:
# - test_l1_cache_hit_returns_immediately
# - test_l2_cache_hit_skips_embedding
# - test_l3_cache_hit_skips_vector_search
# - test_full_miss_generates_new_response
# - test_cache_invalidation_on_note_update
```

---

#### Step 5.2: Add Cache Stats Endpoint
**File:** `app/routes/assistant_routes.py`

```python
@router.get("/cache-stats")
async def get_cache_stats(
    current_user: User = Depends(get_current_user),
    cache_manager: RedisCacheManager = Depends(get_cache)
):
    """
    Get AI cache performance statistics.
    
    Returns:
    - Hit rates by layer (L1, L2, L3)
    - Cost savings
    - Cache sizes
    """
    if not cache_manager.is_available:
        raise HTTPException(
            status_code=503,
            detail="Cache not available"
        )
    
    # Get stats from each layer
    query_cache = QueryCache(cache_manager)
    embedding_cache = EmbeddingCache(cache_manager)
    context_cache = ContextCache(cache_manager)
    
    stats = {
        "l1_query": await query_cache.get_stats(),
        "l2_embedding": await embedding_cache.get_stats(),
        "l3_context": await context_cache.get_stats(),
        "combined": {
            "total_cost_saved": 0.0,  # Sum from L1
            "cache_enabled": settings.CACHE_ENABLED
        }
    }
    
    # Calculate combined cost savings
    if "total_cost_saved" in stats["l1_query"]:
        stats["combined"]["total_cost_saved"] = stats["l1_query"]["total_cost_saved"]
    
    return stats
```

---

### Phase 2.6: Testing & Validation (1 hour)

#### Step 6.1: Unit Tests
```bash
# Run all cache unit tests
pytest app/tests/unit/test_*cache*.py -v --cov=app/services/ai/caching

# Expected coverage: >80%
```

#### Step 6.2: Integration Tests
```python
# File: app/tests/integration/test_assistant_caching.py

@pytest.mark.asyncio
async def test_cache_hit_rate_realistic_load():
    """
    Simulate realistic user behavior:
    - 40% repeated exact queries
    - 30% similar queries (semantic)
    - 30% unique queries
    
    Expected: 60%+ combined hit rate
    """
    queries = [
        # Repeated (40% - L1 hits)
        "What is faith?",
        "What is faith?",
        "What is grace?",
        "What is grace?",
        
        # Similar (30% - L2 hits)
        "Define faith",
        "Explain faith to me",
        "What does grace mean?",
        
        # Unique (30% - all misses)
        "What is salvation?",
        "Explain forgiveness",
        "What is repentance?"
    ]
    
    hits = 0
    misses = 0
    
    for query in queries:
        start = time.time()
        result = await assistant.query(user_id=1, query=query)
        duration = time.time() - start
        
        # Cached responses should be <100ms
        if duration < 0.1:
            hits += 1
        else:
            misses += 1
    
    hit_rate = hits / len(queries) * 100
    
    assert hit_rate >= 60, f"Hit rate {hit_rate}% below target 60%"
```

#### Step 6.3: Load Tests
```python
# File: tests/load/locustfile.py

from locust import HttpUser, task, between

class AIAssistantUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        # Login
        response = self.client.post("/auth/login", json={
            "username": "test_user",
            "password": "test_pass"
        })
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    @task(4)  # 40% repeated
    def query_repeated(self):
        self.client.post(
            "/assistant/query",
            json={"query": "What is faith?"},
            headers=self.headers
        )
    
    @task(3)  # 30% similar
    def query_similar(self):
        import random
        queries = ["Define faith", "Explain faith", "What does faith mean?"]
        self.client.post(
            "/assistant/query",
            json={"query": random.choice(queries)},
            headers=self.headers
        )
    
    @task(3)  # 30% unique
    def query_unique(self):
        import random
        queries = [
            "What is salvation?",
            "Explain grace",
            "What is repentance?",
            "What is forgiveness?"
        ]
        self.client.post(
            "/assistant/query",
            json={"query": random.choice(queries)},
            headers=self.headers
        )

# Run: locust -f locustfile.py --users 100 --spawn-rate 10
# Goal: Verify 60%+ hit rate under load
```

---

## 📊 Monitoring & Metrics

### Dashboard Endpoints

```python
# 1. Cache Statistics
GET /assistant/cache-stats
Response:
{
    "l1_query": {
        "total_entries": 150,
        "total_hits": 240,
        "total_cost_saved": 0.0624,
        "avg_hits_per_entry": 1.6
    },
    "l2_embedding": {
        "total_entries": 300,
        "ttl": 604800
    },
    "l3_context": {
        "total_entries": 200,
        "ttl": 3600
    },
    "combined": {
        "total_cost_saved": 0.0624,
        "cache_enabled": true
    }
}

# 2. Health Check (with cache status)
GET /health
Response:
{
    "status": "healthy",
    "cache_available": true,
    "redis_ping": "OK"
}
```

### Logging

```python
# Cache operations logged at INFO level:
INFO: ✅ L1 CACHE HIT: query:v1:abc123
INFO: ❌ L1 CACHE MISS: query:v1:def456
INFO: 💾 L2 CACHED: embedding:v1:xyz789
INFO: 🗑️  Invalidated 5 L3 cache entries for user 123

# Errors logged at ERROR level (graceful degradation):
ERROR: L1 cache get error: Redis connection timeout
ERROR: L2 cache set error: Serialization failed
```

---

## 🚀 Deployment Checklist

### Pre-Deployment

- [ ] All unit tests pass (>80% coverage)
- [ ] Integration tests pass
- [ ] Load tests show 60%+ hit rate
- [ ] Redis configured in production
- [ ] Environment variables set (REDIS_CACHE_URL)
- [ ] Cache warming script ready (optional)

### Deployment Steps

1. **Deploy Redis (if not exists)**
   ```bash
   # Azure Cache for Redis (or equivalent)
   # Minimum: Standard C1 (1GB, $75/month)
   ```

2. **Update Environment Variables**
   ```bash
   REDIS_CACHE_URL=redis://prod-redis:6379/1
   CACHE_ENABLED=true
   CACHE_QUERY_TTL=86400
   CACHE_EMBEDDING_TTL=604800
   CACHE_CONTEXT_TTL=3600
   ```

3. **Deploy Application**
   ```bash
   # Zero-downtime deployment
   # Old pods still serve requests
   # New pods connect to Redis
   ```

4. **Monitor Metrics**
   ```bash
   # Watch for:
   # - Cache hit rate >60%
   # - Redis memory usage <100MB
   # - Response latency improvement
   # - Cost reduction tracking
   ```

### Post-Deployment

- [ ] Verify cache hit rate (after 1 hour of traffic)
- [ ] Check Redis memory usage
- [ ] Validate cost savings dashboard
- [ ] Monitor error logs (cache failures should not break app)
- [ ] Document learnings

---

## ⚠️ Risk Mitigation

### Risk 1: Redis Unavailable
**Impact:** Cache misses, slower responses, higher costs  
**Mitigation:** Graceful degradation built-in (cache errors don't break requests)  
**Monitoring:** Alert if Redis connection fails

### Risk 2: Cache Stampede
**Problem:** Many requests miss cache simultaneously, overload LLM  
**Mitigation:** Request coalescing (future Phase 3+)  
**Workaround:** Circuit breaker (Phase 4)

### Risk 3: Stale Cache Data
**Problem:** Cached responses outdated after user note changes  
**Mitigation:** L3 invalidation on note CRUD operations  
**Monitoring:** Track invalidation events

### Risk 4: Memory Overflow
**Problem:** Redis runs out of memory  
**Mitigation:** 
- TTL on all keys (automatic eviction)
- Memory limit on Redis (1GB max)
- LRU eviction policy
**Monitoring:** Alert at 80% memory usage

---

## 📈 Success Metrics (Week 1)

**Target Metrics:**
- ✅ Cache hit rate: >60% (combined L1+L2+L3)
- ✅ Cost reduction: >60% ($0.26/day → $0.10/day at 1k requests)
- ✅ Latency improvement: 2-3x faster (cached queries <100ms P95)
- ✅ Zero production incidents related to caching
- ✅ Redis memory usage: <100MB

**Data Collection:**
```python
# Daily metrics to track:
{
    "date": "2024-12-27",
    "total_requests": 1000,
    "cache_hits": {
        "l1": 400,
        "l2": 360,
        "l3": 168
    },
    "combined_hit_rate": 0.928,  # 92.8%
    "cost_baseline": 0.26,
    "cost_actual": 0.019,
    "cost_saved": 0.241,  # 92.8% savings!
    "avg_latency_cached_ms": 45,
    "avg_latency_uncached_ms": 3805,
    "redis_memory_mb": 32
}
```

---

## 🔄 Next Steps (After Phase 2)

### Phase 3+: Advanced Optimizations (Future)
- Request coalescing (prevent cache stampede)
- Similarity search in Redis (find similar cached queries)
- Adaptive TTL (longer TTL for popular queries)
- Cache warming (pre-populate popular queries)

### Phase 4: Circuit Breakers (Next Priority)
- Protect against HuggingFace API failures
- Fallback to cached responses when LLM unavailable
- Estimated: 4 hours

### Phase 6: Request Tracing
- OpenTelemetry spans for cache operations
- Trace cache hit/miss in distributed tracing
- Estimated: 4 hours

---

## 📝 Implementation Timeline

**Week 1 (8 hours total):**

| Day | Phase | Duration | Deliverable |
|-----|-------|----------|-------------|
| Day 1 | 2.1 Foundation | 2h | Redis cache manager, config |
| Day 2 | 2.2 L1 Query Cache | 2h | Query result caching |
| Day 3 | 2.3 L2 Embedding Cache | 2h | Embedding caching |
| Day 4 | 2.4 L3 Context Cache | 1h | Context caching |
| Day 4 | 2.5 Integration | 2h | Assistant service integration |
| Day 5 | 2.6 Testing | 1h | Unit + integration tests |

**Day 6-7:** Load testing, monitoring, documentation

**Total:** 8 hours development + 2 hours testing/validation = **10 hours**

---

## ✅ Definition of Done

Phase 2 is complete when:

- [ ] All three cache layers implemented (L1, L2, L3)
- [ ] Assistant service integrated with caching
- [ ] Cache stats endpoint functional
- [ ] Unit tests pass (>80% coverage)
- [ ] Integration tests pass
- [ ] Load tests show 60%+ hit rate
- [ ] Documentation updated
- [ ] Deployed to production
- [ ] Monitoring dashboard showing metrics
- [ ] Week 1 success metrics achieved

---

**Document Version:** 1.0  
**Created:** December 20, 2024  
**Status:** Ready to Implement  
**Approved By:** [Pending]  
**Start Date:** [TBD]  
**Target Completion:** [Start Date + 1 week]
