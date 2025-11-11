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
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(EmbeddingGenerationError),
        reraise=True
    )
    def generate(self, text: str) -> List[float]:
        """
        Generate embedding vector from text with automatic retry logic.
        
        Args:
            text: Input text to embed
            
        Returns:
            List of floats representing the embedding vector (384 dimensions for all-MiniLM-L6-v2)
            
        Raises:
            EmbeddingGenerationError: If embedding generation fails after retries
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for embedding generation")
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
    
    def generate_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts efficiently.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors (native model dimensions)
        """
        if not texts:
            return []
        
        try:
            # Filter out empty texts but keep track of indices
            valid_texts = []
            valid_indices = []
            
            for i, text in enumerate(texts):
                if text and text.strip():
                    valid_texts.append(text)
                    valid_indices.append(i)
            
            if not valid_texts:
                # Return empty embeddings for all texts
                return [[0.0] * self.embedding_dimension for _ in range(len(texts))]
            
            # Generate embeddings in batch
            embeddings = self._model.encode(valid_texts, convert_to_numpy=True)
            
            # Prepare result array with zeros for all texts
            result = [[0.0] * self.embedding_dimension for _ in range(len(texts))]
            
            # Fill in valid embeddings (no padding needed - use native dimensions)
            for i, embedding in enumerate(embeddings):
                original_index = valid_indices[i]
                result[original_index] = embedding.tolist()
            
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
        
        return " ".join(parts)
    
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
