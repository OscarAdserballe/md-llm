import os
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
import json
import chromadb
from chromadb.utils import embedding_functions
from datetime import datetime

from config_logger import logger
from config import SUPPORTED_MODELS
from src.embeddings import EmbeddingGenerator
from src.llm import LLM

class VectorStore:
    """Manages a ChromaDB collection for storing and retrieving embeddings"""
    
    def __init__(self, data_dir: Optional[Path] = None):
        self.logger = logger
        
        # Set up data directory
        if data_dir is None:
            self.data_dir = Path.home() / ".cli_llm" / "vector_db"
        else:
            self.data_dir = data_dir
            
        self.data_dir.mkdir(exist_ok=True, parents=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(path=str(self.data_dir))
        
        # Create collection (or get existing one)
        try:
            self.collection = self.client.get_collection("llm_responses")
            self.logger.info(f"Loaded existing vector collection with {self.collection.count()} records")
        except Exception:
            self.logger.info("Creating new vector collection")
            self.collection = self.client.create_collection("llm_responses")
        
        # Initialize embedding generator
        self.embedding_generator = EmbeddingGenerator(api_key=SUPPORTED_MODELS["flash"].api_key)
        
    def add_interaction(self, 
                       query: str, 
                       response: str, 
                       model_name: str, 
                       query_type: str = "question",
                       file_path: Optional[str] = None,
                       summary: Optional[str] = None) -> str:
        """Add a new interaction to the vector store"""
        # Generate a unique ID
        interaction_id = str(uuid.uuid4())
        
        # Create combined text for embedding
        combined_text = f"Query: {query}\nResponse: {response}"
        
        # Generate embedding
        embedding = self.embedding_generator.get_embedding(combined_text)
        
        # Generate summary if not provided
        if not summary:
            summary = self._generate_summary(query, response)
        
        # Prepare metadata
        metadata = {
            "timestamp": datetime.now().isoformat(),
            "model": model_name,
            "query_type": query_type,
            "summary": summary,
        }
        
        if file_path:
            metadata["file_path"] = str(file_path)
            
        # Prepare document
        document = {
            "query": query,
            "response": response
        }
        
        # Add to collection
        self.collection.add(
            ids=[interaction_id],
            embeddings=[embedding],
            metadatas=[metadata],
            documents=[json.dumps(document)]
        )
        
        self.logger.info(f"Added interaction {interaction_id} to vector store")
        return interaction_id
        
    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for similar interactions"""
        # Generate embedding for the query
        query_embedding = self.embedding_generator.get_embedding(query)
        
        # Since ChromaDB embeddings might not be accessible, recalculate them
        all_results = self.collection.get(limit=self.collection.count())
        
        # Process results with recalculated embeddings
        processed_results = []
        similarities = []
        
        # Process each item
        for i in range(len(all_results['ids'])):
            # Parse document and metadata
            doc = json.loads(all_results['documents'][i])
            metadata = all_results['metadatas'][i]
            
            # Recalculate embedding for document
            doc_text = f"Query: {doc.get('query', '')}\nResponse: {doc.get('response', '')}"
            doc_embedding = self.embedding_generator.get_embedding(doc_text)
            
            # Calculate cosine similarity directly
            similarity = self.embedding_generator.similarity(query_embedding, doc_embedding)
            similarities.append((i, similarity))
            self.logger.info(f"Item {i}: similarity={similarity:.4f}, summary={metadata.get('summary', 'N/A')}")
            
        # Sort by similarity (highest first)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Take top results based on limit
        top_indices = [idx for idx, _ in similarities[:limit]]
        
        # Create processed results
        for idx in top_indices:
            doc = json.loads(all_results['documents'][idx])
            metadata = all_results['metadatas'][idx]
            
            # Find the corresponding similarity score
            similarity = 0.0
            for i, sim_tuple in enumerate(similarities):
                if sim_tuple[0] == idx:
                    similarity = sim_tuple[1]
                    break
            
            processed_results.append({
                "id": all_results['ids'][idx],
                "query": doc.get("query", ""),
                "response": doc.get("response", ""),
                "summary": metadata.get("summary", ""),
                "model": metadata.get("model", ""),
                "timestamp": metadata.get("timestamp", ""),
                "file_path": metadata.get("file_path", ""),
                "similarity": similarity,
            })
            
        return processed_results
    
    def _generate_summary(self, query: str, response: str) -> str:
        """Generate a summary of the interaction using a small LLM"""
        try:
            # Use Flash model for summarization
            llm_config = SUPPORTED_MODELS["flash"]
            llm = LLM(llm_config=llm_config)
            
            summarize_prompt = f"""Below is a query and its response. Create a concise one-sentence summary (max 15 words) that captures the key insight or action from this interaction:

[QUERY]
{query}

[RESPONSE]
{response}

Summary: """
            
            messages = [{"role": "user", "content": summarize_prompt}]
            summary = llm.query(messages=messages)
            
            # Clean up the summary if needed
            summary = summary.strip()
            if summary.startswith("Summary:"):
                summary = summary[8:].strip()
                
            return summary
        except Exception as e:
            self.logger.error(f"Error generating summary: {e}")
            return "Interaction summary unavailable"
