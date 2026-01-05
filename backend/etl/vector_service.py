"""
Vector Embedding Service
Generates vector embeddings for semantic search using SentenceTransformers
Creates TWO types of embeddings:
1. Label-level embeddings (for dashboard search)
2. Section-level embeddings (for RAG chatbot)
"""

from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional
import numpy as np
import logging

logger = logging.getLogger(__name__)


class VectorService:
    """
    Vector embedding service using SentenceTransformers
    Model: all-MiniLM-L6-v2 (384 dimensions, fast, good quality)
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the embedding model
        
        Args:
            model_name: HuggingFace SentenceTransformer model
        """
        self.model_name = model_name
        self.model = None
        self._initialized = False
        self.dimensions = 384  # Model output dimensions
    
    def initialize(self):
        """
        Lazy initialization - load model only when needed
        Downloads ~80MB on first run
        """
        if self._initialized:
            return
        
        try:
            logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            self._initialized = True
            logger.info(f"✅ Embedding model loaded (dimensions: {self.dimensions})")
            
        except Exception as e:
            logger.error(f"Failed to initialize embedding model: {e}")
            raise
    
    def generate_label_embedding(self, drug_data: Dict) -> np.ndarray:
        """
        Generate a single embedding for an entire drug label
        Used for dashboard search/filtering
        
        Args:
            drug_data: Dictionary with drug metadata
                - name: Drug name
                - generic_name: Generic/active ingredient
                - manufacturer: Company name
                - indications: What it treats (optional)
                - summary: Brief description (optional)
        
        Returns:
            384-dimensional numpy array
        """
        if not self._initialized:
            self.initialize()
        
        # Create a comprehensive text representation of the drug
        text_parts = []
        
        # Add drug names (highest importance)
        if drug_data.get('name'):
            text_parts.append(f"Drug: {drug_data['name']}")
        
        if drug_data.get('generic_name'):
            text_parts.append(f"Generic name: {drug_data['generic_name']}")
        
        # Add manufacturer
        if drug_data.get('manufacturer'):
            text_parts.append(f"Manufacturer: {drug_data['manufacturer']}")
        
        # Add indications (what it treats)
        if drug_data.get('indications'):
            text_parts.append(f"Used for: {drug_data['indications']}")
        
        # Add any summary text
        if drug_data.get('summary'):
            text_parts.append(drug_data['summary'])
        
        # Combine into single text
        combined_text = ". ".join(text_parts)
        
        # Generate embedding
        embedding = self.model.encode(
            combined_text,
            convert_to_numpy=True,
            normalize_embeddings=True  # L2 normalization for cosine similarity
        )
        
        logger.debug(f"Generated label embedding for: {drug_data.get('name', 'Unknown')}")
        return embedding
    
    def generate_section_embedding(self, section_text: str, section_title: str = None) -> np.ndarray:
        """
        Generate embedding for a single section of a drug label
        Used for RAG chatbot retrieval
        
        Args:
            section_text: The section content (e.g., "INDICATIONS AND USAGE: ...")
            section_title: Optional section title to prepend
        
        Returns:
            384-dimensional numpy array
        """
        if not self._initialized:
            self.initialize()
        
        # Optionally prepend title for better context
        if section_title:
            text = f"{section_title}: {section_text}"
        else:
            text = section_text
        
        # Truncate if too long (model has 512 token limit)
        # ~1 token = 4 chars, so limit to ~2000 chars
        if len(text) > 2000:
            text = text[:2000]
        
        # Generate embedding
        embedding = self.model.encode(
            text,
            convert_to_numpy=True,
            normalize_embeddings=True
        )
        
        logger.debug(f"Generated section embedding for: {section_title or 'Unknown section'}")
        return embedding
    
    def generate_embedding(self, text: str) -> np.ndarray:
        """
        Generate embedding for any text (generic method for API queries)
        Alias for generate_section_embedding without title
        
        Args:
            text: Any text string (query, document, etc.)
        
        Returns:
            384-dimensional numpy array
        """
        return self.generate_section_embedding(text, section_title=None)
    
    def generate_batch_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for multiple texts at once (more efficient)
        
        Args:
            texts: List of text strings
        
        Returns:
            numpy array of shape (len(texts), 384)
        """
        if not self._initialized:
            self.initialize()
        
        if not texts:
            return np.array([])
        
        # Batch encoding for efficiency
        embeddings = self.model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            batch_size=32,
            show_progress_bar=len(texts) > 50
        )
        
        logger.info(f"Generated {len(texts)} embeddings in batch")
        return embeddings
    
    def compute_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Compute cosine similarity between two embeddings
        
        Returns:
            Similarity score between 0 and 1 (1 = identical)
        """
        # Cosine similarity (since embeddings are normalized)
        similarity = np.dot(embedding1, embedding2)
        return float(similarity)
    
    def search_similar_labels(self, query: str, label_embeddings: List[tuple]) -> List[tuple]:
        """
        Find most similar drug labels to a query
        
        Args:
            query: Search query (e.g., "GLP-1 for weight loss")
            label_embeddings: List of (label_id, embedding) tuples
        
        Returns:
            Sorted list of (label_id, similarity_score) tuples
        """
        if not self._initialized:
            self.initialize()
        
        # Generate query embedding
        query_embedding = self.model.encode(
            query,
            convert_to_numpy=True,
            normalize_embeddings=True
        )
        
        # Compute similarities
        results = []
        for label_id, embedding in label_embeddings:
            similarity = self.compute_similarity(query_embedding, embedding)
            results.append((label_id, similarity))
        
        # Sort by similarity (descending)
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results


# Global instance (singleton pattern)
_vector_service = None


def get_vector_service() -> VectorService:
    """
    Get or create global vector service instance
    Singleton to avoid loading model multiple times
    """
    global _vector_service
    
    if _vector_service is None:
        _vector_service = VectorService()
        _vector_service.initialize()
    
    return _vector_service
