"""
Redis Connection Pool Manager

Provides centralized Redis client management for:
- Rate limiting
- Caching
- Session storage
- Background job queues
"""

import logging
from typing import Optional
from redis import Redis, ConnectionPool
from app.core.config import settings

logger = logging.getLogger(__name__)

# Global connection pool
_redis_pool: Optional[ConnectionPool] = None
_redis_client: Optional[Redis] = None


def get_redis_pool() -> ConnectionPool:
    """
    Get or create Redis connection pool.
    
    Returns:
        ConnectionPool instance
    """
    global _redis_pool
    
    if _redis_pool is None:
        logger.info(f"Creating Redis connection pool: {settings.redis_host}:{settings.redis_port}")
        
        _redis_pool = ConnectionPool(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            password=settings.redis_password if hasattr(settings, 'redis_password') else None,
            decode_responses=True,  # Auto-decode bytes to strings
            max_connections=settings.redis_max_connections,
            socket_timeout=5,
            socket_connect_timeout=5,
            retry_on_timeout=True
        )
        
        logger.info("Redis connection pool created")
    
    return _redis_pool


def get_redis_client() -> Redis:
    """
    Get or create Redis client.
    
    Returns:
        Redis client instance
        
    Raises:
        ConnectionError: If Redis is unavailable
    """
    global _redis_client
    
    if _redis_client is None:
        pool = get_redis_pool()
        _redis_client = Redis(connection_pool=pool)
        
        # Test connection
        try:
            _redis_client.ping()
            logger.info("Redis client connected successfully")
        except Exception as e:
            logger.error(f"Redis connection failed: {e}", exc_info=True)
            raise ConnectionError(f"Failed to connect to Redis: {e}")
    
    return _redis_client


def close_redis():
    """Close Redis connections (call on app shutdown)."""
    global _redis_client, _redis_pool
    
    if _redis_client:
        _redis_client.close()
        _redis_client = None
        logger.info("Redis client closed")
    
    if _redis_pool:
        _redis_pool.disconnect()
        _redis_pool = None
        logger.info("Redis connection pool closed")
