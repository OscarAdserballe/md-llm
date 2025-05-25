#!/usr/bin/env python
from src.vector_store import VectorStore
from src.search_service import SearchService

print("Populating vector database with sample entries...")

# Sample data
sample_data = [
    {
        "query": "How do I process PDF files in the CLI?",
        "response": "To process PDF files, use the -f option followed by the path to your PDF file. For example: 'llm -f /path/to/document.pdf'. The system will extract text from the PDF and analyze it. For large PDFs, the claude_thinking model is automatically used, which provides better handling of long documents.",
        "model_name": "flash",
        "query_type": "question"
    },
    {
        "query": "Can I search for files in a directory?",
        "response": "Yes, you can process entire directories using the -f flag followed by the directory path. For example: 'llm -f /path/to/directory'. The system will recursively process all supported files in the directory. File size limits apply to each individual file (150,000 tokens maximum).",
        "model_name": "claude",
        "query_type": "question"
    },
    {
        "query": "How to customize output formats?",
        "response": "You can customize output formats using the -o option. There are several destinations available: 'terminal' (default), 'file' (saves to current directory), 'obsidian_papers' (saves to Obsidian vault), or specify a custom directory path. Use it like this: 'llm -o obsidian_papers -f your_file.pdf'.",
        "model_name": "flash",
        "query_type": "question"
    },
    {
        "query": "Tell me about token limits",
        "response": "The CLI has a default token limit of 100,000 tokens per file to prevent excessive API usage. Files exceeding this limit will be skipped with a warning. For directory processing, each file is checked individually. The token counting is done using the tiktoken library with the cl100k_base encoding.",
        "model_name": "flash",
        "query_type": "question"
    },
    {
        "query": "This is a test entry for the vector database",
        "response": "This is a sample response that's already in the database. It should match semantic searches related to testing or samples.",
        "model_name": "flash",
        "query_type": "test"
    }
]

# Initialize vector store
vector_store = VectorStore()

# Add all sample data
for item in sample_data:
    interaction_id = vector_store.add_interaction(
        query=item["query"],
        response=item["response"],
        model_name=item["model_name"],
        query_type=item["query_type"]
    )
    print(f"Added interaction {interaction_id}")

print("Database populated successfully!")
print("Try searching with: python search_cli.py \"your search query\"")

# Example search
search_query = "token limit exceeded"
print(f"\nExample search for: '{search_query}'")
search_service = SearchService()
results = search_service.search(search_query, limit=2)
formatted_results = search_service.format_results(results)
print(formatted_results)