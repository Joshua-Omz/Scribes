"""
Prompt engine for assembling final prompts with token budget enforcement.

🔴 SAFETY-CRITICAL: YOU MUST IMPLEMENT THIS

This module handles prompt construction with:
- System instructions (defines assistant behavior)
- Context insertion (retrieved chunks)
- User query integration
- Token budget enforcement
- Prompt injection defenses

Key responsibilities:
- Define system prompt templates
- Format context blocks
- Enforce total token limits
- Detect and mitigate prompt injection
- Handle edge cases (empty context, long queries)

Implementation decisions YOU must make:
1. System instruction tone and boundaries
2. Citation format for sources
3. How to handle empty context (no relevant notes)
4. Refusal strategies (off-topic queries)
5. Prompt injection defenses

DO NOT implement until you've designed prompts!
"""

from typing import Dict, Any, Optional
import logging

from app.services.tokenizer_service import get_tokenizer_service
from app.core.config import settings

logger = logging.getLogger(__name__)


class PromptEngine:
    """
    Engine for constructing prompts with token awareness and safety.
    
    ⚠️  PLACEHOLDER - YOU MUST IMPLEMENT THIS WITH SAFETY IN MIND
    """
    
    def __init__(self):
        """Initialize prompt engine."""
        self.tokenizer = get_tokenizer_service()
        self.model_context_window = settings.assistant_model_context_window
        logger.warning("PromptEngine initialized - PLACEHOLDER ONLY")
    
    def build_prompt(
        self,
        user_query: str,
        context_chunks: list,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Build final prompt for generation.
        
        ⚠️  YOU MUST IMPLEMENT THIS
        
        Safety requirements:
        - MUST enforce total token limit (system + context + query + output)
        - MUST sanitize user input for prompt injection
        - MUST handle empty context gracefully
        - SHOULD detect off-topic queries
        
        Args:
            user_query: User's question
            context_chunks: Selected chunks from context builder
            system_prompt: Optional override for system instructions
            
        Returns:
            Dictionary with structure:
            {
                "prompt": str (full assembled prompt),
                "token_breakdown": {
                    "system_tokens": int,
                    "context_tokens": int,
                    "query_tokens": int,
                    "reserved_output_tokens": int,
                    "total_tokens": int
                },
                "within_budget": bool
            }
            
        Raises:
            ValueError: If inputs invalid or exceed budget
        """
        raise NotImplementedError(
            "PromptEngine.build_prompt() MUST be implemented by YOU. "
            "This is safety-critical - design prompts carefully!"
        )
    
    def get_default_system_prompt(self) -> str:
        """
        Get default system instructions.
        
        ⚠️  YOU MUST IMPLEMENT THIS
        
        Should define:
        - Assistant role and capabilities
        - How to use context
        - Citation requirements
        - Boundaries (what NOT to do)
        - Tone and style
        """
        raise NotImplementedError("System prompt not defined")
    
    def detect_prompt_injection(self, user_query: str) -> bool:
        """
        Detect potential prompt injection attempts.
        
        ⚠️  YOU MUST IMPLEMENT THIS
        
        Look for:
        - Instructions to ignore previous context
        - Role-playing attempts
        - System prompt leakage attempts
        - Malicious instructions
        """
        raise NotImplementedError("Prompt injection detection not implemented")


# Singleton
_prompt_engine = None


def get_prompt_engine() -> PromptEngine:
    """Get or create prompt engine singleton."""
    global _prompt_engine
    if _prompt_engine is None:
        _prompt_engine = PromptEngine()
    return _prompt_engine

