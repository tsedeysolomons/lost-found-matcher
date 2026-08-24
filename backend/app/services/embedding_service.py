"""
Embedding service using Sentence Transformers for semantic similarity.
"""
from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List
from app.config import EMBEDDING_MODEL, EMBEDDING_DIMENSION

class EmbeddingService:
    """
    Service for generating semantic embeddings using Sentence Transformers.
    Model: all-MiniLM-L6-v2 (384 dimensions, ~90MB)
    """
    
    def __init__(self, model_name: str = EMBEDDING_MODEL):
        """Initialize the embedding service with specified model."""
        self.model = SentenceTransformer(model_name)
        self.dimension = EMBEDDING_DIMENSION
    
    def generate_embedding(self, text: str) -> np.ndarray:
        """
        Generate embedding vector for input text.
        
        Args:
            text: Input text to encode
        
        Returns:
            Normalized embedding vector of shape (384,) for all-MiniLM-L6-v2
        """
        if not text or not text.strip():
            # Return zero vector for empty text
            return np.zeros(self.dimension, dtype=np.float32)
        
        # Generate embedding
        embedding = self.model.encode(text, convert_to_numpy=True)
        
        # Ensure it's the right shape
        if embedding.shape[0] != self.dimension:
            raise ValueError(
                f"Expected embedding dimension {self.dimension}, "
                f"got {embedding.shape[0]}"
            )
        
        return embedding.astype(np.float32)
    
    def compute_similarity(
        self, 
        embedding1: np.ndarray, 
        embedding2: np.ndarray
    ) -> float:
        """
        Compute cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
        
        Returns:
            Cosine similarity in range [0, 1]
        """
        # Handle None or invalid embeddings
        if embedding1 is None or embedding2 is None:
            return 0.0
        
        if len(embedding1) == 0 or len(embedding2) == 0:
            return 0.0
        
        # Compute cosine similarity
        dot_product = np.dot(embedding1, embedding2)
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        similarity = dot_product / (norm1 * norm2)
        
        # Clamp to [0, 1] range (handle floating point errors)
        return max(0.0, min(1.0, float(similarity)))
    
    def batch_generate_embeddings(self, texts: List[str]) -> List[np.ndarray]:
        """
        Generate embeddings for multiple texts efficiently.
        
        Args:
            texts: List of input texts
        
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        # Filter out empty texts
        valid_texts = [t if t and t.strip() else " " for t in texts]
        
        # Generate embeddings in batch
        embeddings = self.model.encode(
            valid_texts,
            convert_to_numpy=True,
            show_progress_bar=False
        )
        
        return [emb.astype(np.float32) for emb in embeddings]

# Global instance (initialized once)
_embedding_service = None

def get_embedding_service() -> EmbeddingService:
    """Get or create the global embedding service instance."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
