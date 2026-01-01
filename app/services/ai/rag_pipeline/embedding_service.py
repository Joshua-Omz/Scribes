"""
Embedding service for generating and comparing semantic embeddings.
Handles text-to-vector transformation for semantic search and AI features.
"""

import logging
from typing import List, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)


class EmbeddingGenerationError(Exception):
    """Custom exception for embedding generation failures."""
    pass


class EmbeddingService:
    """
    Service for generating embeddings from text using SentenceTransformers.
    
    The default model 'all-MiniLM-L6-v2' produces 384-dimensional embeddings.
    Database should use VECTOR(384) to match the model's native dimension.
    
    Embeddings focus on content similarity (sermon teachings/topics) rather than
    metadata like preacher names or titles, ensuring true semantic search.
    """
    
    # Singleton pattern for model caching
    _instance = None
    _model = None
    
    def __new__(cls, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        if cls._instance is None:
            cls._instance = super(EmbeddingService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """Initialize the embedding service with a specific model."""
        if self._initialized:
            return
            
        self.model_name = model_name
        
        
        try:
            logger.info(f"Loading embedding model: {model_name}")
            self._model = SentenceTransformer(model_name)
            self.embedding_dimension = self._model.get_sentence_embedding_dimension()
            logger.info(f"Model loaded. Embedding dimension: {self.embedding_dimension}")
            self._initialized = True
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
    
    def _generate_single(self, text: str) -> List[float]:
        """
        Internal method to generate embedding for a single text chunk.
        No retry logic - handled by the public generate() method.
        
        Args:
            text: Input text to embed
            
        Returns:
            List of floats representing the embedding vector
            
        Raises:
            EmbeddingGenerationError: If embedding generation fails
        """
        if not text or not text.strip():
            raise EmbeddingGenerationError("Cannot generate embedding for empty text")
        
        try:
            # Generate embedding using the model
            embedding = self._model.encode(text, convert_to_numpy=True)
            
            # Validate the embedding
            if embedding is None or len(embedding) == 0:
                raise EmbeddingGenerationError("Model returned empty embedding")
            
            # Check for all-zero embedding (indicates failure)
            if np.all(embedding == 0):
                raise EmbeddingGenerationError("Model returned all-zero embedding")
            
            return embedding.tolist()
            
        except EmbeddingGenerationError:
            raise
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise EmbeddingGenerationError(f"Failed to generate embedding: {str(e)}")
    
    def _generate_with_chunking(self, text: str, chunk_size_tokens: int = 384) -> List[float]:
        """
        Generate embedding for long text using chunking and averaging strategy.
        
        Splits text into chunks, generates embeddings for each, then averages them
        to create a single representative embedding that captures the full content.
        
        Args:
            text: Input text to embed (should be long text requiring chunking)
            chunk_size_tokens: Maximum tokens per chunk (default: 384)
            
        Returns:
            List of floats representing the averaged embedding vector
            
        Raises:
            EmbeddingGenerationError: If chunking or embedding generation fails
        """
        try:
            # Split text into chunks based on character count (conservative estimation)
            # Using ~3.5 chars per token for safety (vs 4)
            chars_per_chunk = chunk_size_tokens * 3.5
            chunks = []
            
            # Split by sentences first to avoid breaking mid-sentence
            sentences = text.replace('\n', ' ').split('. ')
            
            current_chunk = ""
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                    
                # Add period back if it was removed
                if not sentence.endswith('.'):
                    sentence += '.'
                
                # Check if adding this sentence exceeds chunk size
                if len(current_chunk) + len(sentence) > chars_per_chunk and current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = sentence
                else:
                    current_chunk += " " + sentence if current_chunk else sentence
            
            # Add the last chunk
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
            
            # Fallback: if no chunks were created (no sentence delimiters), split by character count
            if not chunks:
                chunks = [text[i:i+int(chars_per_chunk)] for i in range(0, len(text), int(chars_per_chunk))]
            
            logger.info(f"Split text into {len(chunks)} chunks for embedding")
            
            # Generate embeddings for each chunk
            chunk_embeddings = []
            for i, chunk in enumerate(chunks):
                try:
                    embedding = self._generate_single(chunk)
                    chunk_embeddings.append(np.array(embedding))
                except Exception as e:
                    logger.warning(f"Failed to embed chunk {i+1}/{len(chunks)}: {e}")
                    # Continue with other chunks - partial coverage is better than none
            
            if not chunk_embeddings:
                raise EmbeddingGenerationError("Failed to generate embeddings for any chunks")
            
            # Average the embeddings
            avg_embedding = np.mean(chunk_embeddings, axis=0)
            
            # Normalize the averaged embedding (important for cosine similarity)
            norm = np.linalg.norm(avg_embedding)
            if norm > 0:
                avg_embedding = avg_embedding / norm
            
            logger.info(f"Successfully averaged {len(chunk_embeddings)} chunk embeddings")
            
            return avg_embedding.tolist()
            
        except EmbeddingGenerationError:
            raise
        except Exception as e:
            logger.error(f"Error in chunking strategy: {e}")
            raise EmbeddingGenerationError(f"Failed to generate embedding with chunking: {str(e)}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(EmbeddingGenerationError),
        reraise=True
    )
    def generate(self, text: str, enable_chunking: bool = True, chunk_size_tokens: int = 384) -> List[float]:
        """
        Generate embedding vector from text with automatic retry logic and chunking support.
        
        For long texts, automatically chunks the content and averages embeddings to prevent
        truncation and information loss.
        
        Args:
            text: Input text to embed
            enable_chunking: Whether to chunk long text (default: True for production)
            chunk_size_tokens: Maximum tokens per chunk (default: 384, conservative for 512 token limit)
            
        Returns:
            List of floats representing the embedding vector (384 dimensions for all-MiniLM-L6-v2)
            
        Raises:
            EmbeddingGenerationError: If embedding generation fails after retries
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for embedding generation")
            raise EmbeddingGenerationError("Cannot generate embedding for empty text")
        
        # Estimate tokens (rough: 4 chars ≈ 1 token for English)
        estimated_tokens = len(text) // 4
        
        # If text is short enough or chunking disabled, process directly
        if not enable_chunking or estimated_tokens <= chunk_size_tokens:
            return self._generate_single(text)
        
        # Text is too long - use chunking with averaging
        logger.info(f"Text length {estimated_tokens} tokens exceeds limit {chunk_size_tokens}. Using chunking strategy.")
        return self._generate_with_chunking(text, chunk_size_tokens)
    
    def generate_batch(self, texts: List[str], enable_chunking: bool = True, chunk_size_tokens: int = 384) -> List[List[float]]:
        """
        Generate embeddings for multiple texts efficiently with chunking support.
        
        Args:
            texts: List of texts to embed
            enable_chunking: Whether to chunk long texts (default: True)
            chunk_size_tokens: Maximum tokens per chunk (default: 384)
            
        Returns:
            List of embedding vectors (native model dimensions)
        """
        if not texts:
            return []
        
        try:
            # Process each text individually to handle chunking properly
            result = []
            for text in texts:
                if not text or not text.strip():
                    # Empty text gets zero embedding
                    result.append([0.0] * self.embedding_dimension)
                else:
                    # Use the generate method which handles chunking
                    embedding = self.generate(text, enable_chunking, chunk_size_tokens)
                    result.append(embedding)
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            return [[0.0] * self.embedding_dimension for _ in range(len(texts))]
    
    def similarity(self, vec_a: List[float], vec_b: List[float]) -> float:
        """
        Calculate cosine similarity between two embedding vectors.
        
        Args:
            vec_a: First embedding vector
            vec_b: Second embedding vector
            
        Returns:
            Similarity score between -1 and 1 (higher is more similar)
        """
        if not vec_a or not vec_b:
            return 0.0
        
        try:
            a = np.array(vec_a)
            b = np.array(vec_b)
            
            # Cosine similarity
            norm_a = np.linalg.norm(a)
            norm_b = np.linalg.norm(b)
            
            if norm_a == 0 or norm_b == 0:
                return 0.0
            
            similarity = np.dot(a, b) / (norm_a * norm_b)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            return 0.0
    
    def combine_text_for_embedding(
        self,
        content: str,
        scripture_refs: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> str:
        """
        Combine note fields into a single text for embedding generation.
        
        Focuses on content similarity - what the sermon is about, not who preached it.
        This ensures semantic search finds notes with similar teachings/topics,
        regardless of preacher or title.
        
        Args:
            content: Note content (main sermon text)
            scripture_refs: Scripture references mentioned
            tags: List of topic tags
            
        Returns:
            Combined text string for embedding
        """
        parts = []
        
        # Main content - the primary signal for semantic similarity
        if content:
            parts.append(content)
        
        # Scripture references - important for theological context
        if scripture_refs:
            parts.append(f"Scripture: {scripture_refs}.")
        
        # Tags - topic categorization
        if tags:
            tags_text = ", ".join(tags)
            parts.append(f"Topics: {tags_text}.")
        
        combined = " ".join(parts)
        
        # Log text length for monitoring chunking usage
        char_count = len(combined)
        estimated_tokens = char_count // 4
        if estimated_tokens > 384:
            logger.info(f"Combined text is {char_count} chars (~{estimated_tokens} tokens) - will use chunking")
        
        return combined
    
    def get_model_info(self) -> dict:
        """Get information about the current embedding model."""
        return {
            "model_name": self.model_name,
            "embedding_dimension": self.embedding_dimension,
    
        }


# Global instance for easy access
_embedding_service_instance = None


def get_embedding_service() -> EmbeddingService:
    """Get or create the global embedding service instance."""
    global _embedding_service_instance
    if _embedding_service_instance is None:
        _embedding_service_instance = EmbeddingService()
    return _embedding_service_instance
