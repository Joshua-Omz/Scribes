"""
AI Caching Module - Phase 2: Semantic Caching

Three-layer caching strategy for AI assistant:
- L1 (Query Result Cache): Complete AI responses (24h TTL, 40% hit rate target)
- L2 (Embedding Cache): Query embeddings (7d TTL, 60% hit rate target)
- L3 (Context Cache): Retrieved sermon chunks (1h TTL, 70% hit rate target)

Combined expected hit rate: 60-80% (cost reduction)
"""

from app.services.ai.caching.query_cache import QueryCache
from app.services.ai.caching.embedding_cache import EmbeddingCache
from app.services.ai.caching.context_cache import ContextCache

__all__ = ["QueryCache", "EmbeddingCache", "ContextCache"]
