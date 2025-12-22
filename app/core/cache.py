"""
Redis cache manager for AI caching layers.
Provides async interface to Redis with connection pooling and graceful degradation.

Phase 2: AI-Specific Caching
- L1: Query result cache (complete AI responses)
- L2: Embedding cache (query embeddings)
- L3: Context cache (retrieved sermon chunks)
"""
from typing import Optional
import redis.asyncio as redis
from aiocache import Cache
from aiocache.serializers import MsgPackSerializer
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisCacheManager:
    """
    Manages Redis connections and cache instances for AI services.
    
    Features:
    - Connection pooling for async operations
    - Graceful degradation (cache failures don't break app)
    - Health checking
    - Supports both raw Redis client and aiocache wrapper
    """
    
    def __init__(self):
        self._redis_client: Optional[redis.Redis] = None
        self._cache: Optional[Cache] = None
        self._is_connected: bool = False
    
    async def connect(self):
        """
        Initialize Redis connection pool.
        
        Establishes connection with:
        - Async Redis client (for raw operations)
        - aiocache wrapper (for simplified caching)
        - Connection pooling (max 50 connections)
        - Binary mode for msgpack serialization
        """
        try:
            # Create async Redis client with connection pool
            self._redis_client = await redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=False,  # Binary mode for msgpack
                max_connections=settings.redis_max_connections * 5,  # Higher pool for cache
                socket_timeout=5,
                socket_connect_timeout=5,
                health_check_interval=30
            )
            
            # Test connection with ping
            await self._redis_client.ping()
            logger.info("✅ Redis cache connected successfully")
            
            # Initialize aiocache wrapper for simplified operations
            self._cache = Cache(
                Cache.REDIS,
                endpoint=settings.redis_host,
                port=settings.redis_port,
                namespace="ai",  # Prefix all keys with "ai:"
                serializer=MsgPackSerializer(),
                timeout=5
            )
            
            self._is_connected = True
            
        except Exception as e:
            logger.error(f"❌ Redis cache connection failed: {e}")
            logger.warning("⚠️  Running in degraded mode (no caching)")
            self._redis_client = None
            self._cache = None
            self._is_connected = False
    
    async def disconnect(self):
        """Close Redis connection gracefully."""
        if self._redis_client:
            try:
                await self._redis_client.aclose()
                logger.info("Redis cache disconnected")
            except Exception as e:
                logger.error(f"Error disconnecting Redis: {e}")
            finally:
                self._redis_client = None
                self._cache = None
                self._is_connected = False
    
    async def health_check(self) -> bool:
        """
        Check if Redis is healthy and responsive.
        
        Returns:
            bool: True if Redis responds to ping, False otherwise
        """
        if not self._redis_client:
            return False
        
        try:
            await self._redis_client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False
    
    @property
    def is_available(self) -> bool:
        """Check if Redis cache is connected and available."""
        return self._is_connected and self._redis_client is not None
    
    @property
    def client(self) -> redis.Redis:
        """
        Get raw Redis client for advanced operations.
        
        Returns:
            redis.Redis: Async Redis client
            
        Raises:
            RuntimeError: If Redis is not connected
        """
        if not self._redis_client:
            raise RuntimeError("Redis cache not connected. Call connect() first.")
        return self._redis_client
    
    @property
    def cache(self) -> Cache:
        """
        Get aiocache instance for simplified caching operations.
        
        Returns:
            Cache: aiocache wrapper with msgpack serialization
            
        Raises:
            RuntimeError: If Redis is not connected
        """
        if not self._cache:
            raise RuntimeError("Redis cache not connected. Call connect() first.")
        return self._cache
    
    async def get_info(self) -> dict:
        """
        Get Redis server information.
        
        Returns:
            dict: Redis info including memory usage, keys, etc.
        """
        if not self.is_available:
            return {"error": "Redis not available"}
        
        try:
            info = await self._redis_client.info("memory")
            keyspace = await self._redis_client.info("keyspace")
            
            return {
                "status": "connected",
                "memory_used": info.get("used_memory_human", "unknown"),
                "memory_peak": info.get("used_memory_peak_human", "unknown"),
                "keys": keyspace.get("db0", {}).get("keys", 0) if keyspace else 0,
                "uptime_days": info.get("uptime_in_days", 0)
            }
        except Exception as e:
            logger.error(f"Failed to get Redis info: {e}")
            return {"error": str(e)}


# Global cache manager instance (singleton)
cache_manager = RedisCacheManager()


async def get_cache_manager() -> RedisCacheManager:
    """
    Dependency injection function for FastAPI.
    
    Returns:
        RedisCacheManager: Global cache manager instance
        
    Usage:
        @app.get("/endpoint")
        async def endpoint(cache: RedisCacheManager = Depends(get_cache_manager)):
            if cache.is_available:
                await cache.cache.set("key", "value")
    """
    if not cache_manager.is_available:
        # Attempt connection if not already connected
        await cache_manager.connect()
    
    return cache_manager


async def init_cache():
    """Initialize cache on application startup."""
    await cache_manager.connect()


async def close_cache():
    """Close cache on application shutdown."""
    await cache_manager.disconnect()
