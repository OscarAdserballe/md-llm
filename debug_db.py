#!/usr/bin/env python
import chromadb
from pathlib import Path
import json

# Set up data directory
data_dir = Path.home() / ".cli_llm" / "vector_db"
print(f"Looking for ChromaDB at: {data_dir}")

if not data_dir.exists():
    print(f"Data directory does not exist: {data_dir}")
    exit(1)

# Initialize ChromaDB client
client = chromadb.PersistentClient(path=str(data_dir))

try:
    # Get collection
    collection = client.get_collection("llm_responses")
    count = collection.count()
    print(f"Found collection with {count} items")
    
    # Query all items
    if count > 0:
        results = collection.get(limit=count)
        print(f"Retrieved {len(results['ids'])} items")
        
        print("\nCollection contents:")
        for i in range(len(results['ids'])):
            doc = json.loads(results['documents'][i])
            metadata = results['metadatas'][i]
            
            print(f"\n--- Item {i+1} ---")
            print(f"ID: {results['ids'][i]}")
            print(f"Query: {doc.get('query', 'N/A')}")
            print(f"Summary: {metadata.get('summary', 'N/A')}")
            print(f"Model: {metadata.get('model', 'N/A')}")
            print(f"Type: {metadata.get('query_type', 'N/A')}")
            print(f"Timestamp: {metadata.get('timestamp', 'N/A')}")
            
    else:
        print("Collection is empty")
        
except Exception as e:
    print(f"Error accessing collection: {e}")