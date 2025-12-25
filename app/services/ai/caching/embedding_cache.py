"""
L2: Embedding Cache

Caches query embeddings (384-dim vectors) to avoid expensive recomputation.

Key Design:
- Cache key: hash(normalized_query_text)
- Normalization: lowercase, remove punctuation, strip whitespace
- TTL: 7 days (embeddings are deterministic, never change)
- Hit Rate Target: 60% (similar questions map to same embedding)
- Cost Savings: Computation time (200ms) + embedding API cost

Why cache embeddings?
- Embedding generation is expensive (~200ms CPU time)
- Same query variants ("faith" vs "Faith?" vs "what is faith") → same embedding
- Embeddings never change (deterministic for same text)

Cache Structure:
- Key: "embedding:v1:{hash(normalized_query)}"
- Value: numpy array (384 floats) serialized with msgpack
- No metadata needed (immutable data)
"""
from typing import Optional
import hashlib
import re
import numpy as np
import msgpack
import logging

from app.core.cache import RedisCacheManager
from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingCache:
    """Caches query embeddings (L2)."""
    
    def __init__(self, cache_manager: RedisCacheManager):
        """
        Initialize embedding cache.
        
        Args:
            cache_manager: Redis cache manager instance
        """
        self.client = cache_manager.client
        self.ttl = settings.cache_embedding_ttl
        self.enabled = settings.cache_enabled
    
    def _normalize_query(self, query: str) -> str:
        """
        Normalize query text for cache key consistency.
        
        Transformations:
        - Lowercase (case-insensitive)
        - Remove punctuation (keep alphanumeric + spaces)
        - Normalize whitespace (collapse multiple spaces)
        
        Examples:
            "What is faith?" → "what is faith"
            "What is faith" → "what is faith"  (same key!)
            "  What   is  faith?  " → "what is faith"
        
        Args:
            query: Raw query text
            
        Returns:
            str: Normalized query text
        """
        # Lowercase
        normalized = query.lower()
        
        # Remove punctuation (keep alphanumeric and spaces)
        normalized = re.sub(r'[^\w\s]', '', normalized)
        
        # Normalize whitespace (collapse multiple spaces, strip ends)
        normalized = ' '.join(normalized.split())
        
        return normalized
    
    def _build_cache_key(self, query: str) -> str:
        """
        Build cache key from normalized query.
        
        Args:
            query: Query text
            
        Returns:
            str: Cache key like "embedding:v1:abc123def456"
        """
        normalized = self._normalize_query(query)
        query_hash = hashlib.sha256(normalized.encode()).hexdigest()[:16]
        return f"embedding:v1:{query_hash}"
    
    async def get(self, query: str):
        """
        Retrieve cached embedding.
        
        Args:
            query: Query text
            
        Returns:
            list or None: Embedding vector (384 floats) if found, None otherwise
        """
        if not self.enabled:
            return None
        
        cache_key = self._build_cache_key(query)
        
        try:
            cached_bytes = await self.client.get(cache_key)
            
            if cached_bytes:
                logger.info(f"✅ L2 CACHE HIT: {cache_key}")
                
                # Deserialize numpy array from msgpack
                embedding_list = msgpack.unpackb(cached_bytes, raw=False)
                
                # Return as list (consistent with embedding_service.generate())
                return embedding_list
            else:
                logger.debug(f"❌ L2 CACHE MISS: {cache_key}")
                return None
                
        except Exception as e:
            logger.error(f"L2 cache get error: {e}")
            return None  # Graceful degradation
    
    async def set(self, query: str, embedding):
        """
        Store embedding in cache.
        
        Args:
            query: Query text
            embedding: Embedding vector (numpy array or list, 384 dimensions)
        """
        if not self.enabled:
            return
        
        cache_key = self._build_cache_key(query)
        
        try:
            # Convert to numpy array if it's a list
            if isinstance(embedding, list):
                embedding_array = np.array(embedding, dtype=np.float32)
            elif isinstance(embedding, np.ndarray):
                embedding_array = embedding
            else:
                logger.warning(f"Invalid embedding type: {type(embedding)}, expected list or numpy array")
                return
            
            # Validate embedding shape
            if embedding_array.shape != (384,):
                logger.warning(f"Invalid embedding shape: {embedding_array.shape}, expected (384,)")
                return
            
            # Serialize numpy array to msgpack (compact binary format)
            embedding_bytes = msgpack.packb(
                embedding_array.tolist(),
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
            # Don't fail request on cache error
    
    async def get_stats(self) -> dict:
        """
        Get L2 cache statistics.
        
        Returns:
            dict: Cache stats including entry count and TTL
        """
        try:
            # Count cached embeddings
            count = 0
            async for _ in self.client.scan_iter(match="embedding:v1:*"):
                count += 1
            
            return {
                "layer": "L2_embedding",
                "total_entries": count,
                "ttl_days": self.ttl / 86400,
                "note": "Embeddings are deterministic and never change"
            }
            
        except Exception as e:
            logger.error(f"Failed to get L2 stats: {e}")
            return {"error": str(e)}
    
    async def clear_all(self):
        """
        Clear all L2 cache entries (for testing/maintenance).
        
        WARNING: This deletes all cached embeddings!
        """
        try:
            deleted = 0
            
            async for key in self.client.scan_iter(match="embedding:v1:*"):
                await self.client.delete(key)
                deleted += 1
            
            logger.info(f"🗑️  Cleared L2 cache: {deleted} embeddings")
            
        except Exception as e:
            logger.error(f"Failed to clear L2 cache: {e}")
