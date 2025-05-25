#!/usr/bin/env python
import click
from termcolor import colored
import json
from src.search_service import SearchService

@click.command()
@click.argument('search_query')
@click.option('--limit', '-l', type=int, default=5, help='Maximum number of results to return')
@click.option('--detailed', '-d', is_flag=True, help='Show detailed results including full responses')
@click.option('--min-similarity', type=float, default=0.3, help='Minimum similarity score (0.0-1.0)')
@click.option('--debug', is_flag=True, help='Show detailed debug information')
def search(search_query, limit, detailed, min_similarity, debug):
    """Search previous interactions for similar queries or content"""
    try:
        # Initialize search service
        search_service = SearchService()
        
        print(colored(f"Searching for: {search_query}", "cyan"))
        
        if debug:
            # Get vector store directly
            from src.vector_store import VectorStore
            vector_store = VectorStore()
            
            # Count items
            count = vector_store.collection.count()
            print(f"Database contains {count} items")
            
            # Get embedding for query
            from src.embeddings import EmbeddingGenerator
            generator = EmbeddingGenerator()
            query_embedding = generator.get_embedding(search_query)
            print(f"Generated embedding for query with {len(query_embedding)} dimensions")
            
            # Get all items
            items = vector_store.collection.get()
            print(f"Retrieved {len(items['ids'])} items from database")
            print(f"Fields: {list(items.keys())}")
            
            # Calculate similarities directly
            for i in range(len(items['ids'])):
                if 'embeddings' in items and items['embeddings'] is not None:
                    embedding = items['embeddings'][i]
                    similarity = generator.similarity(query_embedding, embedding)
                    doc = json.loads(items['documents'][i])
                    print(f"Item {i}: similarity={similarity:.4f}, query={doc.get('query', '')[:30]}...")
                else:
                    print("No embeddings field in results")
        
        # Normal search
        results = search_service.search(
            query=search_query,
            limit=limit,
            min_similarity=min_similarity
        )
        
        # Format and display results
        formatted_results = search_service.format_results(results, detailed=detailed)
        print(formatted_results)
        
    except Exception as e:
        import traceback
        print(colored(f"Error during search: {e}", "red"))
        if debug:
            traceback.print_exc()
        if "ChromaDB" in str(e):
            print(colored("Tip: You may need to install chromadb with 'pip install chromadb'", "yellow"))

if __name__ == "__main__":
    search()