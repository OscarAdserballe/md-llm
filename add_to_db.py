#!/usr/bin/env python
from src.vector_store import VectorStore
from config import SUPPORTED_MODELS

# Simple script to add an entry directly to the vector database
query = "This is a test entry for the vector database"
response = "This is a sample response about testing the vector database functionality"
model_name = "flash"

# Initialize vector store
vector_store = VectorStore()

# Add interaction
interaction_id = vector_store.add_interaction(
    query=query,
    response=response,
    model_name=model_name,
    query_type="test"
)

print(f"Added interaction {interaction_id} to database")