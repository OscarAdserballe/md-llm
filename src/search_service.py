from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
from termcolor import colored

from config_logger import logger
from src.vector_store import VectorStore

class SearchService:
    """Service for searching through past interactions"""
    
    def __init__(self):
        self.logger = logger
        self.vector_store = VectorStore()
        
    def search(self, query: str, limit: int = 5, min_similarity: float = 0.7) -> List[Dict[str, Any]]:
        """Search for similar past interactions"""
        self.logger.info(f"Searching for: {query}")
        results = self.vector_store.search(query, limit=limit)
        
        # Debug information
        self.logger.info(f"Raw results: {len(results)} items")
        for i, result in enumerate(results):
            self.logger.info(f"Result {i+1}: similarity={result['similarity']:.4f}, summary={result.get('summary', 'N/A')}")
        
        # Filter by minimum similarity
        filtered_results = [r for r in results if r["similarity"] >= min_similarity]
        
        self.logger.info(f"Found {len(filtered_results)} relevant results after filtering (min_similarity={min_similarity})")
        return filtered_results
    
    def format_results(self, results: List[Dict[str, Any]], detailed: bool = False) -> str:
        """Format search results for display"""
        if not results:
            return "No matching results found."
            
        output = "\n" + "=" * 80 + "\n"
        output += f"FOUND {len(results)} RELEVANT PAST INTERACTIONS\n"
        output += "=" * 80 + "\n\n"
        
        for i, result in enumerate(results):
            # Parse timestamp into human-readable format
            timestamp = datetime.fromisoformat(result["timestamp"]) if result.get("timestamp") else "Unknown date"
            formatted_date = timestamp.strftime("%Y-%m-%d %H:%M") if isinstance(timestamp, datetime) else str(timestamp)
            
            similarity_pct = int(result["similarity"] * 100)
            
            output += f"{i+1}. [{similarity_pct}% match] "
            output += colored(result["summary"], "cyan") + "\n"
            output += f"   Model: {result['model']} | Date: {formatted_date}\n"
            
            if result.get("file_path"):
                output += f"   File: {result['file_path']}\n"
                
            output += f"   Query: {result['query']}\n"
            
            if detailed:
                # Show full response in detailed mode
                output += "   " + "-" * 40 + "\n"
                output += f"   Response:\n{result['response']}\n"
            else:
                # Truncate response in summary mode
                max_len = 100
                response = result['response']
                if len(response) > max_len:
                    response = response[:max_len] + "..."
                output += f"   Preview: {response}\n"
                
            output += "\n"
            
        return output
