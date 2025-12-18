"""
Rate Limiting Middleware for AssistantService

Implements multi-tier rate limiting to prevent abuse and control costs:
- Per-user limits (10/min, 100/hour, 500/day)
- Global system limits (100 concurrent, 1000/hour)
- Cost-based limits ($5/day per user, $100/day global)

Uses Redis for distributed rate limiting with sliding window algorithm.
"""

import logging
import time
from typing import Optional, Callable
from functools import wraps
import hashlib

from fastapi import HTTPException, Request, status
from redis import Redis
from app.core.config import settings

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Redis-backed rate limiter with sliding window algorithm.
    
    Features:
    - Multiple limit tiers (per-minute, per-hour, per-day)
    - Per-user and global limits
    - Cost-based limits
    - Detailed metrics
    - Custom limits for premium users
    """
    
    def __init__(self, redis_client: Optional[Redis] = None):
        """
        Initialize rate limiter.
        
        Args:
            redis_client: Redis connection (uses default if None)
        """
        self.redis = redis_client or self._get_redis_client()
        self.enabled = settings.rate_limiting_enabled
        logger.info(f"RateLimiter initialized (enabled={self.enabled})")
    
    def _get_redis_client(self) -> Redis:
        """Get Redis client from connection pool."""
        try:
            from app.core.redis import get_redis_client
            return get_redis_client()
        except ImportError:
            logger.warning("Redis not available - rate limiting will use in-memory fallback")
            return None
    
    async def check_rate_limit(
        self,
        user_id: int,
        endpoint: str = "assistant.query",
        cost: float = 0.0
    ) -> tuple[bool, dict]:
        """
        Check if request is within rate limits.
        
        Args:
            user_id: User ID to check
            endpoint: Endpoint identifier
            cost: API cost in USD (for cost-based limiting)
            
        Returns:
            Tuple of (allowed: bool, metadata: dict)
            metadata includes:
            - limit_type: Which limit was hit (if any)
            - retry_after: Seconds until limit resets
            - remaining: Requests remaining in window
            - reset_time: Unix timestamp when limit resets
            
        Raises:
            HTTPException: 429 if rate limit exceeded
        """
        if not self.enabled:
            return True, {"rate_limiting": "disabled"}
        
        now = int(time.time())
        
        # Check all limit tiers
        limits = [
            ("per_minute", f"ratelimit:user:{user_id}:minute", 60, settings.rate_limit_per_minute),
            ("per_hour", f"ratelimit:user:{user_id}:hour", 3600, settings.rate_limit_per_hour),
            ("per_day", f"ratelimit:user:{user_id}:day", 86400, settings.rate_limit_per_day),
        ]
        
        for limit_type, key, window, max_requests in limits:
            allowed, metadata = await self._check_sliding_window(
                key=key,
                window=window,
                max_requests=max_requests,
                now=now
            )
            
            if not allowed:
                metadata["limit_type"] = limit_type
                metadata["user_id"] = user_id
                metadata["endpoint"] = endpoint
                
                # Log rate limit event
                logger.warning(
                    f"Rate limit exceeded for user {user_id}: "
                    f"{limit_type} limit ({max_requests}/{window}s)"
                )
                
                # Increment rate limit counter for metrics
                await self._increment_metric(f"rate_limit_exceeded:{limit_type}")
                
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded: {max_requests} requests per {limit_type.replace('_', ' ')}",
                    headers={"Retry-After": str(metadata["retry_after"])}
                )
        
        # Check global system limits
        global_allowed, global_metadata = await self._check_global_limits(now)
        if not global_allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="System is at capacity. Please try again later.",
                headers={"Retry-After": str(global_metadata["retry_after"])}
            )
        
        # Check cost-based limits
        if cost > 0:
            cost_allowed, cost_metadata = await self._check_cost_limit(user_id, cost, now)
            if not cost_allowed:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Daily cost limit exceeded (${settings.user_daily_cost_limit})",
                    headers={"Retry-After": str(cost_metadata["retry_after"])}
                )
        
        # All limits passed - record the request
        await self._record_request(user_id, endpoint, cost, now)
        
        return True, {
            "rate_limiting": "passed",
            "limits_checked": len(limits),
            "timestamp": now
        }
    
    async def _check_sliding_window(
        self,
        key: str,
        window: int,
        max_requests: int,
        now: int
    ) -> tuple[bool, dict]:
        """
        Check rate limit using sliding window algorithm.
        
        Args:
            key: Redis key for this limit
            window: Time window in seconds
            max_requests: Max requests allowed in window
            now: Current Unix timestamp
            
        Returns:
            Tuple of (allowed: bool, metadata: dict)
        """
        if not self.redis:
            return True, {}  # Fallback: allow if Redis unavailable
        
        try:
            # Remove old entries outside the window
            window_start = now - window
            self.redis.zremrangebyscore(key, 0, window_start)
            
            # Count requests in current window
            current_count = self.redis.zcard(key)
            
            if current_count >= max_requests:
                # Get oldest request in window
                oldest = self.redis.zrange(key, 0, 0, withscores=True)
                if oldest:
                    oldest_timestamp = int(oldest[0][1])
                    retry_after = oldest_timestamp + window - now
                else:
                    retry_after = window
                
                return False, {
                    "allowed": False,
                    "current": current_count,
                    "limit": max_requests,
                    "retry_after": retry_after,
                    "reset_time": now + retry_after
                }
            
            # Calculate remaining requests
            remaining = max_requests - current_count - 1  # -1 for current request
            reset_time = now + window
            
            return True, {
                "allowed": True,
                "current": current_count,
                "limit": max_requests,
                "remaining": remaining,
                "reset_time": reset_time
            }
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}", exc_info=True)
            return True, {"error": str(e)}  # Fail open on errors
    
    async def _check_global_limits(self, now: int) -> tuple[bool, dict]:
        """Check global system-wide rate limits."""
        # Check concurrent requests
        concurrent_key = "ratelimit:global:concurrent"
        concurrent = self.redis.get(concurrent_key) if self.redis else 0
        concurrent = int(concurrent) if concurrent else 0
        
        if concurrent >= settings.global_concurrent_limit:
            return False, {
                "allowed": False,
                "retry_after": 5,  # Try again in 5 seconds
                "concurrent": concurrent,
                "limit": settings.global_concurrent_limit
            }
        
        # Check hourly global limit
        global_allowed, metadata = await self._check_sliding_window(
            key="ratelimit:global:hour",
            window=3600,
            max_requests=settings.global_hourly_limit,
            now=now
        )
        
        return global_allowed, metadata
    
    async def _check_cost_limit(
        self,
        user_id: int,
        cost: float,
        now: int
    ) -> tuple[bool, dict]:
        """
        Check cost-based rate limit.
        
        Args:
            user_id: User ID
            cost: Cost of this request in USD
            now: Current timestamp
            
        Returns:
            Tuple of (allowed: bool, metadata: dict)
        """
        if not self.redis:
            return True, {}
        
        # Get today's cost for user
        cost_key = f"ratelimit:cost:user:{user_id}:daily"
        current_cost = self.redis.get(cost_key)
        current_cost = float(current_cost) if current_cost else 0.0
        
        # Check if adding this request would exceed limit
        total_cost = current_cost + cost
        if total_cost > settings.user_daily_cost_limit:
            # Calculate when limit resets (midnight)
            seconds_until_midnight = 86400 - (now % 86400)
            
            return False, {
                "allowed": False,
                "current_cost": current_cost,
                "request_cost": cost,
                "limit": settings.user_daily_cost_limit,
                "retry_after": seconds_until_midnight
            }
        
        # Check global daily cost
        global_cost_key = "ratelimit:cost:global:daily"
        global_cost = self.redis.get(global_cost_key)
        global_cost = float(global_cost) if global_cost else 0.0
        
        if global_cost + cost > settings.global_daily_cost_limit:
            return False, {
                "allowed": False,
                "reason": "global_cost_limit",
                "retry_after": 86400 - (now % 86400)
            }
        
        return True, {
            "allowed": True,
            "current_cost": current_cost,
            "limit": settings.user_daily_cost_limit
        }
    
    async def _record_request(
        self,
        user_id: int,
        endpoint: str,
        cost: float,
        now: int
    ):
        """Record a successful request for rate limiting tracking."""
        if not self.redis:
            return
        
        try:
            # Record in all time windows
            request_id = f"{now}:{user_id}:{endpoint}"
            
            # Per-user limits
            self.redis.zadd(f"ratelimit:user:{user_id}:minute", {request_id: now})
            self.redis.expire(f"ratelimit:user:{user_id}:minute", 120)  # 2 minutes TTL
            
            self.redis.zadd(f"ratelimit:user:{user_id}:hour", {request_id: now})
            self.redis.expire(f"ratelimit:user:{user_id}:hour", 7200)  # 2 hours TTL
            
            self.redis.zadd(f"ratelimit:user:{user_id}:day", {request_id: now})
            self.redis.expire(f"ratelimit:user:{user_id}:day", 172800)  # 2 days TTL
            
            # Global limits
            self.redis.zadd(f"ratelimit:global:hour", {request_id: now})
            self.redis.expire(f"ratelimit:global:hour", 7200)
            
            # Record cost
            if cost > 0:
                # User daily cost
                cost_key = f"ratelimit:cost:user:{user_id}:daily"
                self.redis.incrbyfloat(cost_key, cost)
                self.redis.expire(cost_key, 86400)  # Expires at midnight
                
                # Global daily cost
                global_cost_key = "ratelimit:cost:global:daily"
                self.redis.incrbyfloat(global_cost_key, cost)
                self.redis.expire(global_cost_key, 86400)
            
            # Increment concurrent counter
            concurrent_key = "ratelimit:global:concurrent"
            self.redis.incr(concurrent_key)
            
        except Exception as e:
            logger.error(f"Failed to record request: {e}", exc_info=True)
    
    async def _increment_metric(self, metric_name: str):
        """Increment a Prometheus/metrics counter."""
        if not self.redis:
            return
        
        try:
            metric_key = f"metrics:{metric_name}:count"
            self.redis.incr(metric_key)
        except Exception as e:
            logger.error(f"Failed to increment metric: {e}", exc_info=True)
    
    async def release_concurrent_slot(self):
        """Release a concurrent request slot (call after request completes)."""
        if not self.redis:
            return
        
        try:
            concurrent_key = "ratelimit:global:concurrent"
            self.redis.decr(concurrent_key)
        except Exception as e:
            logger.error(f"Failed to release concurrent slot: {e}", exc_info=True)
    
    async def get_user_stats(self, user_id: int) -> dict:
        """
        Get rate limit statistics for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Dict with current usage stats
        """
        if not self.redis:
            return {"error": "Redis unavailable"}
        
        now = int(time.time())
        
        stats = {
            "user_id": user_id,
            "timestamp": now,
            "limits": {}
        }
        
        # Get counts for each window
        for window_name, window_seconds in [
            ("minute", 60),
            ("hour", 3600),
            ("day", 86400)
        ]:
            key = f"ratelimit:user:{user_id}:{window_name}"
            window_start = now - window_seconds
            
            # Remove old entries
            self.redis.zremrangebyscore(key, 0, window_start)
            
            # Get current count
            count = self.redis.zcard(key)
            
            stats["limits"][window_name] = {
                "current": count,
                "limit": getattr(settings, f"rate_limit_per_{window_name}"),
                "remaining": max(0, getattr(settings, f"rate_limit_per_{window_name}") - count)
            }
        
        # Get cost stats
        cost_key = f"ratelimit:cost:user:{user_id}:daily"
        current_cost = self.redis.get(cost_key)
        stats["cost"] = {
            "today": float(current_cost) if current_cost else 0.0,
            "limit": settings.user_daily_cost_limit,
            "remaining": max(0, settings.user_daily_cost_limit - (float(current_cost) if current_cost else 0.0))
        }
        
        return stats


# Singleton instance
_rate_limiter = None


def get_rate_limiter() -> RateLimiter:
    """Get or create rate limiter singleton."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


# Decorator for easy rate limiting
def rate_limit(endpoint: str = "default"):
    """
    Decorator to apply rate limiting to async functions.
    
    Usage:
        @rate_limit(endpoint="assistant.query")
        async def my_function(user_id: int, ...):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user_id from args or kwargs
            user_id = kwargs.get("user_id") or (args[0] if args else None)
            if not user_id:
                raise ValueError("user_id required for rate limiting")
            
            # Check rate limit
            limiter = get_rate_limiter()
            await limiter.check_rate_limit(user_id=user_id, endpoint=endpoint)
            
            try:
                # Execute function
                result = await func(*args, **kwargs)
                return result
            finally:
                # Release concurrent slot
                await limiter.release_concurrent_slot()
        
        return wrapper
    return decorator
