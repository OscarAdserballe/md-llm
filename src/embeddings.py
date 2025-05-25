import time
from typing import List, Optional, Dict, Any
import numpy as np
from sentence_transformers import SentenceTransformer
from config_logger import logger
from config import LLMConfig

class EmbeddingGenerator:
    """Handles generating embeddings using sentence-transformers library"""
    
    def __init__(self, api_key: str = None):
        self.logger = logger
        # api_key is ignored but kept for backward compatibility
        
        # Load a lightweight multilingual model
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.logger.info("Initialized sentence-transformers embedding model")
        
    def get_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text input"""
        try:
            # Generate embedding
            embedding = self.model.encode(text)
            return embedding.tolist()  # Convert numpy array to list
        except Exception as e:
            self.logger.error(f"Error generating embedding: {e}")
            raise
        
    def get_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        embeddings = []
        for text in texts:
            embedding = self.get_embedding(text)
            embeddings.append(embedding)
        return embeddings
        
    def similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings"""
        if not embedding1 or not embedding2:
            return 0.0
            
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
            
        return dot_product / (norm1 * norm2)
