"""
Circuit Breaker for HuggingFace API Protection.

Minimal implementation using PyBreaker library.
"""
import logging
from pybreaker import CircuitBreaker, CircuitBreakerError

from app.core.config import settings

logger = logging.getLogger(__name__)

_hf_circuit_breaker = None


def get_huggingface_circuit_breaker() -> CircuitBreaker:
    """Get or create singleton circuit breaker."""
    global _hf_circuit_breaker
    
    if _hf_circuit_breaker is None:
        logger.info(f"Creating circuit breaker: {settings.circuit_breaker_name}")
        
        _hf_circuit_breaker = CircuitBreaker(
            fail_max=settings.circuit_breaker_fail_threshold,
            reset_timeout=settings.circuit_breaker_reset_timeout,
            name=settings.circuit_breaker_name,
            exclude=[ValueError, TypeError]
        )
    
    return _hf_circuit_breaker


def get_circuit_status() -> dict:
    """Get current circuit breaker status."""
    if not settings.circuit_breaker_enabled:
        return {"enabled": False, "state": "disabled"}
    
    breaker = get_huggingface_circuit_breaker()
    
    return {
        "enabled": True,
        "name": breaker.name,
        "state": breaker.current_state,
        "fail_count": breaker.fail_counter,
        "fail_max": breaker.fail_max,
        "reset_timeout": breaker.reset_timeout,
        "is_healthy": breaker.current_state == "closed"
    }


class ServiceUnavailableError(Exception):
    """Raised when circuit breaker is open."""
    pass
