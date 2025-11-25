"""
Tokenizer service for token-aware text processing.

This service provides tokenization utilities using Hugging Face transformers.
It's critical for the AI assistant to stay within token budgets for embeddings
and generation models.

Key responsibilities:
- Count tokens in text
- Truncate text to fit token limits
- Chunk text with token-aware sliding windows
- Ensure consistency between embedding and generation tokenizers
"""

from typing import List, Optional
from functools import lru_cache
import logging

from transformers import AutoTokenizer

from app.core.config import settings

logger = logging.getLogger(__name__)


class TokenizerService:
    """
    Service for tokenizing text using Hugging Face transformers.
    
    Uses the same tokenizer as the generation model to ensure consistent
    token counting across chunking, context building, and generation.
    
    The tokenizer is loaded once and cached for performance.
    """
    
    def __init__(self, model_name: Optional[str] = None):
        """
        Initialize tokenizer service.
        
        Args:
            model_name: HuggingFace model name. Defaults to embedding model from config.
        """
        self.model_name = model_name or settings.hf_embedding_model  # Use embedding model tokenizer
        self._tokenizer = None
        logger.info(f"TokenizerService initialized for model: {self.model_name}")
    
    @property
    def tokenizer(self) -> AutoTokenizer:
        """
        Lazy-load the tokenizer (only loads when first accessed).
        
        Returns:
            AutoTokenizer instance
        """
        if self._tokenizer is None:
            logger.info(f"Loading tokenizer: {self.model_name}")
            self._tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=True,
                use_fast=True  # Use fast tokenizer if available
            )
            logger.info(f"Tokenizer loaded successfully. Vocab size: {len(self._tokenizer)}")
        return self._tokenizer
    
    def count_tokens(self, text: str) -> int:
        """
        Count the number of tokens in text.
        
        Args:
            text: Input text to tokenize
            
        Returns:
            Number of tokens
            
        Example:
            >>> tokenizer_service.count_tokens("Hello, world!")
            4
        """
        if not text:
            return 0
        
        tokens = self.tokenizer.encode(text, add_special_tokens=True)
        return len(tokens)
    
    def encode(self, text: str, add_special_tokens: bool = True) -> List[int]:
        """
        Encode text to token IDs.
        
        Args:
            text: Input text
            add_special_tokens: Whether to add special tokens (BOS, EOS, etc.)
            
        Returns:
            List of token IDs
        """
        return self.tokenizer.encode(text, add_special_tokens=add_special_tokens)
    
    def decode(self, token_ids: List[int], skip_special_tokens: bool = True) -> str:
        """
        Decode token IDs back to text.
        
        Args:
            token_ids: List of token IDs
            skip_special_tokens: Whether to remove special tokens from output
            
        Returns:
            Decoded text string
        """
        return self.tokenizer.decode(token_ids, skip_special_tokens=skip_special_tokens)
    
    def truncate_to_tokens(self, text: str, max_tokens: int) -> str:
        """
        Truncate text to fit within token limit.
        
        Args:
            text: Input text
            max_tokens: Maximum number of tokens allowed
            
        Returns:
            Truncated text that fits within token limit
            
        Example:
            >>> long_text = "This is a very long sermon note..."
            >>> truncated = tokenizer_service.truncate_to_tokens(long_text, 100)
            >>> tokenizer_service.count_tokens(truncated) <= 100
            True
        """
        if not text:
            return ""
        
        # Check if already within limit
        current_tokens = self.count_tokens(text)
        if current_tokens <= max_tokens:
            return text
        
        # Encode and truncate
        token_ids = self.tokenizer.encode(
            text,
            truncation=True,
            max_length=max_tokens,
            add_special_tokens=True
        )
        
        # Decode back to text
        return self.tokenizer.decode(token_ids, skip_special_tokens=True)
    
    def chunk_text(
        self,
        text: str,
        chunk_size: int = 384,
        overlap: int = 64
    ) -> List[str]:
        """
        Split text into overlapping chunks with token-aware boundaries.
        
        Uses a sliding window approach where each chunk has `chunk_size` tokens
        and overlaps with the next chunk by `overlap` tokens. This ensures:
        - Chunks stay within token limits for embeddings
        - Context is preserved across chunk boundaries
        - No information loss at boundaries
        
        Args:
            text: Input text to chunk
            chunk_size: Target size of each chunk in tokens
            overlap: Number of tokens to overlap between chunks
            
        Returns:
            List of text chunks
            
        Example:
            >>> text = "Very long sermon note about faith..."
            >>> chunks = tokenizer_service.chunk_text(text, chunk_size=384, overlap=64)
            >>> # Each chunk is ~384 tokens, with 64 token overlap
            >>> for chunk in chunks:
            ...     assert tokenizer_service.count_tokens(chunk) <= 384
        """
        if not text:
            return []
        
        # Encode full text
        token_ids = self.tokenizer.encode(text, add_special_tokens=False)
        
        # If text is shorter than chunk_size, return as single chunk
        if len(token_ids) <= chunk_size:
            return [text]
        
        chunks = []
        stride = chunk_size - overlap
        
        # Create overlapping windows
        for i in range(0, len(token_ids), stride):
            chunk_token_ids = token_ids[i:i + chunk_size]
            
            # Decode chunk back to text
            chunk_text = self.tokenizer.decode(chunk_token_ids, skip_special_tokens=True)
            chunks.append(chunk_text)
            
            # Stop if we've covered the entire text
            if i + chunk_size >= len(token_ids):
                break
        
        logger.debug(
            f"Chunked text into {len(chunks)} chunks "
            f"(original: {len(token_ids)} tokens, "
            f"chunk_size: {chunk_size}, overlap: {overlap})"
        )
        
        return chunks
    
    def estimate_tokens(self, text: str) -> int:
        """
        Fast token estimate without loading tokenizer (uses heuristic).
        
        Useful for quick checks. For accurate counts, use count_tokens().
        
        Heuristic: ~1 token per 4 characters (common for English text)
        
        Args:
            text: Input text
            
        Returns:
            Estimated token count
        """
        return len(text) // 4


# Global singleton instance
_tokenizer_service: Optional[TokenizerService] = None


@lru_cache(maxsize=1)
def get_tokenizer_service() -> TokenizerService:
    """
    Get or create global TokenizerService instance.
    
    This function is cached to ensure only one tokenizer is loaded
    throughout the application lifecycle.
    
    Returns:
        TokenizerService singleton instance
    """
    global _tokenizer_service
    if _tokenizer_service is None:
        _tokenizer_service = TokenizerService()
    return _tokenizer_service

