"""
AI Services Module

This module contains all AI and ML-related services for the Scribes application.

Services:
- AssistantService: RAG pipeline orchestrator for AI-powered Q&A
- EmbeddingService: Generates 384-dim semantic embeddings
- RetrievalService: Semantic search with pgvector
- TokenizerService: Token-aware text processing
- ChunkingService: Text chunking with configurable overlap
- ContextBuilder: Smart context assembly for LLM prompts
- HFTextGenService: Hugging Face API integration for text generation

Usage:
    from app.services.ai import AssistantService, EmbeddingService
    
    assistant = AssistantService()
    response = await assistant.query("What is grace?", user_id=1, db=session)
"""

from app.services.ai.assistant_service import AssistantService
from app.services.ai.embedding_service import EmbeddingService, EmbeddingGenerationError
from app.services.ai.retrieval_service import RetrievalService
from app.services.ai.tokenizer_service import TokenizerService
from app.services.ai.chunking_service import ChunkingService
from app.services.ai.context_builder import ContextBuilder
from app.services.ai.hf_textgen_service import HFTextGenService, GenerationError

__all__ = [
    "AssistantService",
    "EmbeddingService",
    "EmbeddingGenerationError",
    "RetrievalService",
    "TokenizerService",
    "ChunkingService",
    "ContextBuilder",
    "HFTextGenService",
    "GenerationError",
]
