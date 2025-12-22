"""
L3: Context Cache

Caches retrieved sermon chunks to avoid expensive vector search and DB queries.

Key Design:
- Cache key: hash(user_id + embedding)
- TTL: 1 hour (short - user notes may change)
- Hit Rate Target: 70% (users repeat searches within sessions)
- Cost Savings: DB vector search (~100ms) + context assembly

Why short TTL?
- User may add/edit/delete notes
- Vector search results may change
- Recent searches are most valuable to cache

Cache Structure:
- Key: "context:v1:{user_id}:{embedding_hash}"
- Value: List of chunk dicts (content, note_id, similarity)
- Invalidation: Clear on note create/update/delete

Cache Invalidation:
When user modifies notes (create/update/delete), we invalidate their L3 cache
to ensure fresh search results. L1 and L2 remain valid (unchanged).
"""
from typing import Optional, List, Dict, Any
import hashlib
import logging

from app.core.cache import RedisCacheManager
from app.core.config import settings

logger = logging.getLogger(__name__)


class ContextCache:
    """Caches retrieved context chunks (L3)."""
    
    def __init__(self, cache_manager: RedisCacheManager):
        """
        Initialize context cache.
        
        Args:
            cache_manager: Redis cache manager instance
        """
        self.cache = cache_manager.cache
        self.client = cache_manager.client
        self.ttl = settings.cache_context_ttl
        self.enabled = settings.cache_enabled
    
    def _build_cache_key(
        self,
        user_id: int,
        embedding_hash: str
    ) -> str:
        """
        Build cache key from user and embedding.
        
        Args:
            user_id: User ID (context is user-specific)
            embedding_hash: Hash of query embedding (first 16 chars)
            
        Returns:
            str: Cache key like "context:v1:123:abc123def456"
        """
        return f"context:v1:{user_id}:{embedding_hash[:16]}"
    
    async def get(
        self,
        user_id: int,
        embedding_hash: str
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Retrieve cached context chunks.
        
        Args:
            user_id: User ID requesting context
            embedding_hash: Hash of query embedding
            
        Returns:
            List[Dict] or None: Cached chunks if found, None otherwise
        """
        if not self.enabled:
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
            return None  # Graceful degradation
    
    async def set(
        self,
        user_id: int,
        embedding_hash: str,
        chunks: List[Dict[str, Any]]
    ):
        """
        Store context chunks in cache.
        
        Args:
            user_id: User ID requesting context
            embedding_hash: Hash of query embedding
            chunks: List of chunk dicts to cache
        """
        if not self.enabled:
            return
        
        cache_key = self._build_cache_key(user_id, embedding_hash)
        
        try:
            # Store with short TTL (user notes may change)
            await self.cache.set(cache_key, chunks, ttl=self.ttl)
            logger.info(f"💾 L3 CACHED: {cache_key}")
            
        except Exception as e:
            logger.error(f"L3 cache set error: {e}")
            # Don't fail request on cache error
    
    async def invalidate_user(self, user_id: int):
        """
        Invalidate all cached contexts for a user.
        
        Called when user creates/updates/deletes notes to ensure
        fresh search results.
        
        Args:
            user_id: User ID to invalidate cache for
        """
        if not self.enabled:
            return
        
        try:
            pattern = f"context:v1:{user_id}:*"
            deleted = 0
            
            # Use raw Redis client for pattern deletion
            async for key in self.client.scan_iter(match=pattern):
                await self.client.delete(key)
                deleted += 1
            
            if deleted > 0:
                logger.info(f"🗑️  Invalidated {deleted} L3 cache entries for user {user_id}")
            
        except Exception as e:
            logger.error(f"L3 cache invalidation error: {e}")
    
    async def get_stats(self) -> dict:
        """
        Get L3 cache statistics.
        
        Returns:
            dict: Cache stats including entry count and TTL
        """
        try:
            # Count cached contexts
            count = 0
            async for _ in self.client.scan_iter(match="context:v1:*"):
                count += 1
            
            return {
                "layer": "L3_context",
                "total_entries": count,
                "ttl_minutes": self.ttl / 60,
                "note": "Invalidated on note changes"
            }
            
        except Exception as e:
            logger.error(f"Failed to get L3 stats: {e}")
            return {"error": str(e)}
    
    async def clear_all(self):
        """
        Clear all L3 cache entries (for testing/maintenance).
        
        WARNING: This deletes all cached contexts!
        """
        try:
            deleted = 0
            
            async for key in self.client.scan_iter(match="context:v1:*"):
                await self.client.delete(key)
                deleted += 1
            
            logger.info(f"🗑️  Cleared L3 cache: {deleted} contexts")
            
        except Exception as e:
            logger.error(f"Failed to clear L3 cache: {e}")
