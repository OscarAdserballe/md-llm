# LLM CLI

A powerful CLI tool for interacting with various LLMs (OpenAI, Gemini, Claude, Perplexity). Process files, handle context, and integrate LLMs into your terminal workflow.

## Key Features

- **Multi-LLM Support**: Switch between different LLM providers
- **File Processing**: Process text files, PDFs, and directories
- **Vector Database**: Store and search past interactions semantically
- **Flexible Output**: Terminal, files, or Obsidian vault
- **Token Limit Handling**: Skip or truncate oversized files
- **Vision Support**: Process images with vision-capable models

## Quick Start

```bash
# Install dependencies
poetry install

# Set up API keys in .env
# OPENAI_API_KEY=...
# GEMINI_API_KEY=...
# PERPLEXITY_API_KEY=...
# ANTHROPIC_API_KEY=...

# Basic query
llm "What is the theory of relativity?"

# Process a file
llm -f path/to/document.pdf

# Process directory
llm -f path/to/directory/

# Save output to destination
llm -f document.pdf -o obsidian_papers

# Use image with query
llm -v path/to/image.jpg "What's in this image?"

# Search past interactions
llm search "token limits"
```

## Commands

| Command | Description | Example |
|---------|-------------|---------|
| `llm <query>` | Basic query to LLM | `llm "Explain quantum physics"` |
| `llm -f <path>` | Process file/directory | `llm -f research.pdf` |
| `llm -m <model>` | Select model | `llm -m claude "Write a story"` |
| `llm -o <output>` | Set output destination | `llm -o file "Generate report"` |
| `llm -v <image>` | Include image | `llm -v diagram.jpg "Explain"` |
| `llm search <query>` | Search past interactions | `llm search "PDF processing"` |
| `llm supported-models` | List available models | `llm supported-models` |

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `-m, --model` | LLM model to use | `flash` |
| `-p, --prompt` | System prompt template | `default` |
| `-t, --temperature` | Response creativity | `0.5` |
| `-o, --output` | Output destination | Terminal |
| `-f, --file` | File/directory to process | None |
| `-v, --vision` | Image to include | None |
| `--force` | Overwrite existing files | False |
| `--no-store` | Skip vector DB storage | False |

## Vector Database Search

The CLI stores interactions in a local vector database for semantic search:

```bash
# Search past interactions with minimum similarity of 0.4
llm search "How do I process PDFs?" --min-similarity 0.4

# Get detailed results including full responses
llm search "token limits" --detailed

# Limit number of results
llm search "output formats" --limit 3
```

## Installation

Install dependencies:
```bash
pip install -r requirements.txt
pip install -r vector_db_requirements.txt  # For search functionality
```

## Supported Models

- **Flash**: Gemini 2.0 Flash (default)
- **O1-Mini**: OpenAI o1-mini
- **Claude**: Anthropic Claude 3.7 Sonnet
- **Claude-Thinking**: Claude with extended thinking
- **Perplexity**: Perplexity Sonar
- **ChatGPT**: OpenAI GPT-4.5 Preview

## Architecture

- **LLM**: Handles model interaction via provider-specific adapters
- **ContextManager**: Manages conversation history and file parsing
- **FileProcessor**: Processes files with token limit handling
- **ResponseHandler**: Formats and routes responses
- **VectorStore**: Stores and retrieves past interactions
- **SearchService**: Provides semantic search functionality

## Additional Notes

- Files exceeding 100,000 tokens are skipped (configurable)
- Directory processing is recursive
- New output files won't overwrite existing ones unless `--force` is used
- Terminal input can be piped to the CLI