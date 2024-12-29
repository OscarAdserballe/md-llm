# LLM CLI

A powerful Command-Line Interface (CLI) tool for interacting with various Language Learning Models (LLMs) such as OpenAI's GPT, Gemini, and Perplexity. Manage sessions, handle context, parse files, and seamlessly integrate with your workflow to enhance productivity and leverage the capabilities of cutting-edge LLMs directly from your terminal.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
  - [Commands](#commands)
    - [`llm query <query>`](#llm-query-query)
    - [`llm ls`](#llm-ls)
    - [`llm create <session-name>`](#llm-create-session-name)
    - [`llm run_session <session-name>`](#llm-run_session-session-name)
    - [`llm terminal <query>`](#llm-terminal-query)
- [Folder Structure](#folder-structure)
- [Components](#components)
  - [LLM](#llm)
  - [ContextManager](#contextmanager)
  - [SessionManager](#sessionmanager)
- [Supported Models](#supported-models)
- [Logging](#logging)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

## Features

- **Multi-LLM Support**: Interact with various LLM providers like OpenAI, Gemini, and Perplexity.
- **Session Management**: Create, list, and manage multiple sessions to organize your interactions.
- **Context Handling**: Maintain conversation history and parse files to provide coherent and context-aware responses.
- **File Parsing**: Automatically parse and process supported file types, with OCR fallback for scanned documents.
- **Logging**: Comprehensive logging system for debugging and monitoring activities.
- **Extensible Architecture**: Easily add support for new models and extend functionalities as needed.
- **Secure Configuration**: Manage sensitive API keys and configurations using environment variables.

## Installation

### Prerequisites

- **Python 3.8+**: Ensure you have Python installed. You can download it from [python.org](https://www.python.org/downloads/).
- **Poetry**: This project uses Poetry for dependency management. Install it by following the instructions on [Poetry's official website](https://python-poetry.org/docs/#installation).

### Steps

1. **Clone the Repository**

   ```bash
   git clone https://github.com/yourusername/llm-cli.git
   cd llm-cli
   ```

2. **Install Dependencies**

   ```bash
   poetry install
   ```

3. **Activate Virtual Environment**

   ```bash
   poetry shell
   ```

## Configuration

The application relies on environment variables to manage sensitive information like API keys. Create a `.env` file in the root directory and add the necessary keys:

```env
OPENAI_API_KEY=your_openai_api_key
GEMINI_API_KEY=your_gemini_api_key
PERPLEXITY_API_KEY=your_perplexity_api_key
```

Ensure you replace the placeholders with your actual API keys. The `.env` file should **not** be committed to version control for security reasons.

## Usage

After installation and configuration, you can start using the `llm` CLI tool. Below are the available commands and their descriptions.

### Commands

#### `llm query <query>`

**Description:** Sends a query to the default LLM and outputs the response directly in the terminal.

**Usage:**

```bash
llm query "Explain the Theory of Relativity in simple terms."
```

**Output:**

```plaintext
The Theory of Relativity, developed by Albert Einstein, consists of two parts: Special Relativity and General Relativity. It describes how space and time are interconnected and how gravity affects the fabric of the universe...
```

#### `llm ls`

**Description:** Lists all available sessions.

**Usage:**

```bash
llm ls
```

**Output:**

```plaintext
- project_alpha
- research_session_2023
- daily_notes
```

#### `llm create <session-name>`

**Description:** Creates a new session with the specified name. Initializes the session directory and metadata.

**Usage:**

```bash
llm create project_alpha
```

**Output:**

```plaintext
Created new session: project_alpha
```

#### `llm run_session <session-name>`

**Description:** Executes a specific session, updating it with the latest interactions and responses from the LLM.

**Usage:**

```bash
llm run_session project_alpha
```

**Output:**

```plaintext
Updated project_alpha
```

#### `llm terminal <query>`

**Description:** Sends a query to the LLM with the context of the most recent terminal output. Useful for analyzing command results or errors.

**Usage:**

```bash
echo "Compilation error in module XYZ" | llm terminal "Can you explain this error?"
```

**Output:**

```plaintext
The compilation error in module XYZ indicates that there's a syntax issue in the code. Specifically, it might be missing a closing bracket or there's an unexpected indentation.
```

### Examples

1. **Basic Query**

   ```bash
   llm query "What's the weather like in New York today?"
   ```

2. **Creating and Running a Session**

   ```bash
   llm create work_session
   llm run_session work_session
   ```

3. **Using Terminal Context**

   ```bash
   ls -la | llm terminal "What does this directory listing tell me?"
   ```

## Folder Structure

```
llm_cli/
├── llm_sessions/
│   ├── project_alpha/
│   │   ├── project_alpha.md
│   │   ├── requirements_parsed.txt
│   │   └── ...
│   └── ...
├── src/
│   ├── llm.py
│   ├── context_manager.py
│   ├── session_manager.py
│   ├── session.py
│   └── ...
├── prompts/
│   ├── coding_prompt.txt
│   ├── study_prompt.txt
│   ├── math_prompt.txt
│   ├── writing_prompt.txt
│   ├── summary_prompt.txt
│   └── snip_prompt.txt
├── cli.py
├── config.py
├── config_logger.py
├── poetry.toml
└── poetry.lock
```

- **llm_sessions/**: Contains all session directories. Each session has its own Markdown file and parsed resources.
- **src/**: Core source code modules handling LLM interactions, context management, and session operations.
- **prompts/**: Predefined prompts for various tasks like coding, studying, mathematics, writing, summarization, and snippet generation.
- **cli.py**: Entry point for the CLI, defining available commands and their functionalities.
- **config.py**: Configuration settings, including supported models and default parameters.
- **config_logger.py**: Logging configuration for debugging and monitoring.
- **poetry.toml & poetry.lock**: Dependency management files.

## Components

### LLM

**Description:** The `LLM` class serves as an interface for interacting with different LLM APIs, such as OpenAI and Gemini. It abstracts the complexities of API calls, allowing seamless queries and response handling.

**Key Features:**

- **Multi-Provider Support:** Easily switch between different LLM providers.
- **Customizable Parameters:** Configure model name, temperature, token limits, and system prompts.
- **Unified Query Interface:** Send structured messages and receive coherent responses.

**Usage Example:**

```python
from config import SUPPORTED_MODELS, DEFAULT_MODEL
from src.llm import LLM

llm = LLM(llm_config=SUPPORTED_MODELS[DEFAULT_MODEL])
response = llm.query(messages=[{"role": "user", "content": "Tell me a joke."}])
print(response)
```

### ContextManager

**Description:** The `ContextManager` handles the conversation context, including conversation history and file parsing. It ensures that each query to the LLM is contextually aware, providing more accurate and relevant responses.

**Key Features:**

- **Conversation History:** Maintains a structured history of user and assistant messages.
- **File Parsing:** Automatically processes supported file types and incorporates their content into the context.
- **Search Integration:** Integrates search results to provide up-to-date information.

**Usage Example:**

```python
from src.context_manager import ContextManager
from pathlib import Path

context = ContextManager(
    location=Path("~/llm_sessions/project_alpha"),
    files=["requirements.txt", "README.md"],
    search=["latest Python features"],
    query="Explain the dependencies in requirements.txt."
)
messages = context.get_messages()
```

### SessionManager

**Description:** The `SessionManager` oversees the creation, listing, and deletion of sessions. It manages session metadata and ensures organized storage of session data.

**Key Features:**

- **Session Creation:** Initialize new sessions with structured metadata.
- **Session Listing:** Retrieve a list of all existing sessions.
- **Session Deletion:** Safely remove sessions and their associated data.

**Usage Example:**

```python
from src.session_manager import SessionManager
from pathlib import Path

session_manager = SessionManager(sessions_dir=Path("~/llm_sessions"))
session_manager.create_session("new_project")
sessions = session_manager.list_sessions()
print(sessions)
```

## Supported Models

The CLI currently supports the following LLM models:

- **Flash 2.0 Flash-Exp**
  - **Provider:** Gemini
  - **Model Name:** `gemini-2.0-flash-exp`
  - **API Base URL:** `https://generativelanguage.googleapis.com/v1beta/openai/`
  
- **O1 Mini**
  - **Provider:** OpenAI
  - **Model Name:** `o1-mini`
  
- **Perplexity**
  - **Provider:** Perplexity
  - **Model Name:** `llama-3.1-sonar-large-128k-online`
  - **API Base URL:** `https://api.perplexity.ai`

**Adding New Models:**

To add support for a new model, update the `SUPPORTED_MODELS` dictionary in `config.py` with the necessary configuration details.

```python
new_model = LLMConfig(
    model_name="new-model-name",
    api_key=os.environ['NEW_MODEL_API_KEY'],
    temperature=0.7,
    max_tokens=10000,
    system_prompt=PROMPTS[DEFAULT_SYSTEM_PROMPT_NAME],
    provider="new_provider",
    base_url="https://api.newprovider.com/v1/"
)

SUPPORTED_MODELS = {
    # existing models...
    "new-model": new_model,
}
```

## Logging

The CLI incorporates a robust logging system to facilitate debugging and monitoring.

- **Log Storage:** Logs are stored in the `~/cli_llm/logs/` directory.
- **Log Levels:** Configurable log levels (e.g., INFO, DEBUG, ERROR).
- **Log Format:** Standardized formatting with timestamps, log levels, and messages.

**Accessing Logs:**

```bash
cat ~/cli_llm/logs/llm_2023-10-01.log
```

## Contributing

Contributions are welcome! If you'd like to enhance the tool or fix bugs, follow these steps:

1. **Fork the Repository**

   Click the "Fork" button at the top right of this repository to create your own fork.

2. **Create a Feature Branch**

   ```bash
   git checkout -b feature/YourFeatureName
   ```

3. **Commit Your Changes**

   ```bash
   git commit -m "Add some feature"
   ```

4. **Push to the Branch**

   ```bash
   git push origin feature/YourFeatureName
   ```

5. **Open a Pull Request**

   Navigate to your fork on GitHub and click the "New pull request" button.

## License

This project is licensed under the [MIT License](LICENSE).
