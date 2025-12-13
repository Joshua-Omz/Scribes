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
import warnings

from transformers import AutoTokenizer
from transformers.utils import logging as transformers_logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# Suppress transformers warnings for cleaner logs
transformers_logging.set_verbosity_error()
warnings.filterwarnings("ignore", category=FutureWarning, module="transformers")


class TokenizerService:
    """
    Service for tokenizing text using Hugging Face transformers.
    
    Uses the same tokenizer as the generation model to ensure consistent
    token counting across chunking, context building, and generation.
    
    The tokenizer is loaded once and cached for performance.
    """
    tokenizer = AutoTokenizer.from_pretrained(settings.hf_embedding_model, trust_remote_code=True, use_fast=True)   
    def __init__(self, model_name: Optional[str] = settings.hf_embedding_model, tokenizer: Optional[AutoTokenizer] = tokenizer) -> None:
        """
        Initialize tokenizer service.
        
        Args:
            model_name: HuggingFace model name. Defaults to embedding model from config.
        """
        self.model_name = model_name  
        self._tokenizer = tokenizer
        logger.info(f"TokenizerService initialized for model: {self.model_name}")
    
    @property
    def tokenizer(self) -> AutoTokenizer:
        """
        Lazy-load the tokenizer (only loads when first accessed).
        
        Returns:
            AutoTokenizer instance
            
        Raises:
            Exception: If tokenizer fails to load
        """
        return self._tokenizer
    
    def count_tokens(self, text: str) -> int:
        """
        Count the number of tokens in text.
        
        Args:
            text: Input text to tokenize
            
        Returns:
            Number of tokens (minimum 0)
            
        Example:
            >>> tokenizer_service.count_tokens("Hello, world!")
            4
        """
        if not text or not isinstance(text, str):
            return 0
        
        try:
            tokens = self.tokenizer.encode(text, add_special_tokens=True)
            return len(tokens)
        except Exception as e:
            logger.warning(f"Error counting tokens: {e}. Falling back to estimate.")
            return self.estimate_tokens(text)
    
    def encode(self, text: str, add_special_tokens: bool = True) -> List[int]:
        """
        Encode text to token IDs.
        
        Args:
            text: Input text
            add_special_tokens: Whether to add special tokens (BOS, EOS, etc.)
            
        Returns:
            List of token IDs (empty list if text is empty)
            
        Raises:
            ValueError: If text is not a string
        """
        if not text:
            return []
        
        if not isinstance(text, str):
            raise ValueError(f"Text must be a string, got {type(text)}")
        
        return self.tokenizer.encode(text, add_special_tokens=add_special_tokens)
    
    def decode(self, token_ids: List[int], skip_special_tokens: bool = True) -> str:
        """
        Decode token IDs back to text.
        
        Args:
            token_ids: List of token IDs
            skip_special_tokens: Whether to remove special tokens from output
            
        Returns:
            Decoded text string (empty string if token_ids is empty)
            
        Raises:
            ValueError: If token_ids is not a list
        """
        if not token_ids:
            return ""
        
        if not isinstance(token_ids, list):
            raise ValueError(f"token_ids must be a list, got {type(token_ids)}")
        
        return self.tokenizer.decode(token_ids, skip_special_tokens=skip_special_tokens)
    
    def truncate_to_tokens(self, text: str, max_tokens: int) -> str:
        """
        Truncate text to fit within token limit.
        
        Args:
            text: Input text
            max_tokens: Maximum number of tokens allowed (must be > 0)
            
        Returns:
            Truncated text that fits within token limit
            
        Raises:
            ValueError: If max_tokens <= 0
            
        Example:
            >>> long_text = "This is a very long sermon note..."
            >>> truncated = tokenizer_service.truncate_to_tokens(long_text, 100)
            >>> tokenizer_service.count_tokens(truncated) <= 100
            True
        """
        if not text:
            return ""
        
        if max_tokens <= 0:
            raise ValueError(f"max_tokens must be > 0, got {max_tokens}")
        
        # Check if already within limit
        current_tokens = self.count_tokens(text)
        if current_tokens <= max_tokens:
            return text
        
        logger.debug(f"Truncating text from {current_tokens} to {max_tokens} tokens")
        
        # Encode and truncate
        token_ids = self.tokenizer.encode(
            text,
            truncation=True,
            max_length=max_tokens,
            add_special_tokens=True
        )
        
        # Decode back to text
        truncated = self.tokenizer.decode(token_ids, skip_special_tokens=True)
        
        # Verify truncation worked
        final_count = self.count_tokens(truncated)
        if final_count > max_tokens:
            logger.warning(
                f"Truncation resulted in {final_count} tokens (target: {max_tokens}). "
                f"This may happen with special tokens."
            )
        
        return truncated
    
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
            chunk_size: Target size of each chunk in tokens (must be > overlap)
            overlap: Number of tokens to overlap between chunks (must be >= 0)
            
        Returns:
            List of text chunks (empty list if text is empty)
            
        Raises:
            ValueError: If chunk_size <= overlap or invalid parameters
            
        Example:
            >>> text = "Very long sermon note about faith..."
            >>> chunks = tokenizer_service.chunk_text(text, chunk_size=384, overlap=64)
            >>> # Each chunk is ~384 tokens, with 64 token overlap
            >>> for chunk in chunks:
            ...     assert tokenizer_service.count_tokens(chunk) <= 384
        """
        if not text:
            return []
        
        # Validate parameters
        if chunk_size <= 0:
            raise ValueError(f"chunk_size must be > 0, got {chunk_size}")
        
        if overlap < 0:
            raise ValueError(f"overlap must be >= 0, got {overlap}")
        
        if overlap >= chunk_size:
            raise ValueError(
                f"overlap ({overlap}) must be less than chunk_size ({chunk_size})"
            )
        
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
            
            # Skip empty chunks (shouldn't happen, but safety check)
            if not chunk_token_ids:
                continue
            
            # Decode chunk back to text
            chunk_text = self.tokenizer.decode(chunk_token_ids, skip_special_tokens=True)
            
            # Skip whitespace-only chunks
            if chunk_text.strip():
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
            Estimated token count (minimum 0)
        """
        if not text or not isinstance(text, str):
            return 0
        return max(0, len(text) // 4)
    
    def get_vocab_size(self) -> int:
        """
        Get the vocabulary size of the tokenizer.
        
        Returns:
            Number of tokens in vocabulary
        """
        return len(self.tokenizer)
    
    def batch_count_tokens(self, texts: List[str]) -> List[int]:
        """
        Count tokens for multiple texts efficiently.
        
        Args:
            texts: List of text strings
            
        Returns:
            List of token counts corresponding to each text
        """
        if not texts:
            return []
        
        return [self.count_tokens(text) for text in texts]
    
    def get_model_name(self) -> str:
        """
        Get the name of the model being used for tokenization.
        
        Returns:
            Model name string
        """
        return self.model_name


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

