"""
L1: Query Result Cache

Caches complete AI responses to avoid expensive LLM calls.

Key Design:
- Cache key includes: user_id (personalized) + query + context_ids (which chunks were used)
- TTL: 24 hours (sermon content changes rarely)
- Hit Rate Target: 40% (repeated exact questions)
- Cost Savings: Full LLM call avoided (~$0.00026 per hit)

Cache Structure:
- Key: "query:v1:{hash(user_id + query + context_ids)}"
- Value: Complete response dict (answer, sources, metadata)
- Metadata: Hit tracking for analytics (stored in Redis hash)
"""
from typing import Optional, Dict, Any, List
import hashlib
import json
from datetime import datetime
import logging

from app.core.cache import RedisCacheManager
from app.core.config import settings

logger = logging.getLogger(__name__)


class QueryCache:
    """Caches complete AI query responses (L1)."""
    
    def __init__(self, cache_manager: RedisCacheManager):
        """
        Initialize query cache.
        
        Args:
            cache_manager: Redis cache manager instance
        """
        self.cache = cache_manager.cache
        self.client = cache_manager.client
        self.ttl = settings.cache_query_ttl
        self.enabled = settings.cache_enabled
    
    def _build_cache_key(
        self,
        user_id: int,
        query: str,
        context_ids: List[int]
    ) -> str:
        """
        Build cache key from query parameters.
        
        Key components:
        - user_id: Personalized responses (user's own notes)
        - query: The question text (normalized)
        - context_ids: Which chunks were used (sorted for consistency)
        
        Args:
            user_id: User ID requesting the query
            query: Query text
            context_ids: List of note chunk IDs used in context
            
        Returns:
            str: Cache key like "query:v1:abc123def456"
        """
        # Sort context_ids for consistent hashing
        sorted_ids = sorted(context_ids)
        
        # Create composite key data
        key_data = {
            "user_id": user_id,
            "query": query.strip().lower(),  # Normalize whitespace and case
            "context_ids": sorted_ids
        }
        
        # Hash for compact key
        key_json = json.dumps(key_data, sort_keys=True)
        key_hash = hashlib.sha256(key_json.encode()).hexdigest()[:16]
        
        return f"query:v1:{key_hash}"
    
    async def get(
        self,
        user_id: int,
        query: str,
        context_ids: List[int]
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached query response.
        
        Args:
            user_id: User ID requesting the query
            query: Query text
            context_ids: List of note chunk IDs used in context
            
        Returns:
            Dict or None: Cached response if found, None otherwise
        """
        if not self.enabled:
            return None
        
        cache_key = self._build_cache_key(user_id, query, context_ids)
        
        try:
            cached = await self.cache.get(cache_key)
            
            if cached:
                logger.info(f"✅ L1 CACHE HIT: {cache_key}")
                
                # Track hit in metadata
                await self._increment_hit_count(cache_key)
                
                # Mark as cached in metadata
                if "_cache_metadata" in cached:
                    cached["_cache_metadata"]["from_cache"] = True
                
                return cached
            else:
                logger.debug(f"❌ L1 CACHE MISS: {cache_key}")
                return None
                
        except Exception as e:
            logger.error(f"L1 cache get error: {e}")
            return None  # Graceful degradation - don't break request
    
    async def set(
        self,
        user_id: int,
        query: str,
        context_ids: List[int],
        response: Dict[str, Any]
    ):
        """
        Store query response in cache.
        
        Args:
            user_id: User ID requesting the query
            query: Query text
            context_ids: List of note chunk IDs used in context
            response: Complete response dict to cache
        """
        if not self.enabled:
            return
        
        cache_key = self._build_cache_key(user_id, query, context_ids)
        
        try:
            # Add cache metadata
            enriched_response = {
                **response,
                "_cache_metadata": {
                    "cached_at": datetime.utcnow().isoformat(),
                    "ttl": self.ttl,
                    "user_id": user_id,
                    "layer": "L1_query_result",
                    "from_cache": False  # Will be True when retrieved
                }
            }
            
            # Store in cache with TTL
            await self.cache.set(cache_key, enriched_response, ttl=self.ttl)
            
            # Store hit counter metadata (separate from cached data)
            await self.client.hset(
                f"meta:{cache_key}",
                mapping={
                    "query": query[:100],  # Truncate long queries
                    "user_id": str(user_id),
                    "created_at": datetime.utcnow().isoformat(),
                    "hit_count": "0",
                    "cost_saved": "0.0"
                }
            )
            # Metadata expires with cache entry
            await self.client.expire(f"meta:{cache_key}", self.ttl)
            
            logger.info(f"💾 L1 CACHED: {cache_key}")
            
        except Exception as e:
            logger.error(f"L1 cache set error: {e}")
            # Don't fail request on cache error
    
    async def _increment_hit_count(self, cache_key: str):
        """
        Track cache hit statistics.
        
        Updates:
        - hit_count: Number of times this cache entry was used
        - cost_saved: Estimated cost savings (avg LLM call cost * hits)
        
        Args:
            cache_key: Cache key to update stats for
        """
        try:
            await self.client.hincrby(f"meta:{cache_key}", "hit_count", 1)
            
            # Estimate cost saved (average LLM call cost)
            # Based on typical query: 150 input + 1200 context + 400 output tokens
            avg_cost = 0.00026
            await self.client.hincrbyfloat(
                f"meta:{cache_key}",
                "cost_saved",
                avg_cost
            )
        except Exception as e:
            logger.warning(f"Failed to increment hit count: {e}")
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get L1 cache statistics.
        
        Returns:
            dict: Cache stats including entries, hits, cost saved
        """
        try:
            # Scan for all metadata keys
            meta_keys = []
            async for key in self.client.scan_iter(match="meta:query:v1:*"):
                meta_keys.append(key)
            
            total_entries = len(meta_keys)
            total_hits = 0
            total_cost_saved = 0.0
            
            # Aggregate stats
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
                "avg_hits_per_entry": round(total_hits / total_entries, 2) if total_entries > 0 else 0,
                "ttl_hours": self.ttl / 3600
            }
            
        except Exception as e:
            logger.error(f"Failed to get L1 stats: {e}")
            return {"error": str(e)}
    
    async def clear_all(self):
        """
        Clear all L1 cache entries (for testing/maintenance).
        
        WARNING: This deletes all cached query responses!
        """
        try:
            deleted_data = 0
            deleted_meta = 0
            
            # Delete cache data
            async for key in self.client.scan_iter(match="ai:query:v1:*"):
                await self.client.delete(key)
                deleted_data += 1
            
            # Delete metadata
            async for key in self.client.scan_iter(match="meta:query:v1:*"):
                await self.client.delete(key)
                deleted_meta += 1
            
            logger.info(f"🗑️  Cleared L1 cache: {deleted_data} entries, {deleted_meta} metadata")
            
        except Exception as e:
            logger.error(f"Failed to clear L1 cache: {e}")
