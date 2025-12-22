"""
AI Core Module

AI-specific core components and infrastructure.

Components:
- PromptEngine: Manages prompt templates and assembly for LLM interactions

Usage:
    from app.core.ai import PromptEngine
    
    engine = PromptEngine()
    prompt = engine.assemble_prompt(system_msg, user_query, context)
"""

from app.core.ai.prompt_engine import PromptEngine

__all__ = ["PromptEngine"]
