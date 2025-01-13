import os
from pathlib import Path
import logging
from dataclasses import dataclass   
from datetime import datetime
from dotenv import load_dotenv

from prompts.prompts import PROMPTS

load_dotenv()

DEFAULT_SYSTEM_PROMPT_NAME = "explain"

@dataclass
class LLMConfig:
    model_name: str
    api_key: str
    temperature: float=0.5
    max_tokens: int=8000
    system_prompt: str= PROMPTS[DEFAULT_SYSTEM_PROMPT_NAME]
    provider: str = "openai"
    base_url: str | None = None
    tools: list[dict] | None = None 

flash2 = LLMConfig(
    model_name="gemini-2.0-flash-exp",
    api_key=os.environ['GEMINI_API_KEY'],
    temperature=0.5,
    max_tokens=8000,
    system_prompt=PROMPTS[DEFAULT_SYSTEM_PROMPT_NAME],
    provider="gemini",
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)
explainer = LLMConfig(
    model_name="gemini-2.0-flash-exp",
    api_key=os.environ['GEMINI_API_KEY'],
    temperature=0.5,
    max_tokens=8000,
    system_prompt=PROMPTS['explain'],
    provider="gemini",
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)
preprocess = LLMConfig(
    model_name="gemini-2.0-flash-exp",
    api_key=os.environ['GEMINI_API_KEY'],
    temperature=0.0,
    max_tokens=8000,
    system_prompt=PROMPTS['preprocess'],
    provider="gemini",
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

o1_mini = LLMConfig(
    model_name="o1-mini",
    api_key=os.environ['OPENAI_API_KEY'],
    temperature=0.5,
    max_tokens=65536,
    system_prompt=PROMPTS[DEFAULT_SYSTEM_PROMPT_NAME],
    provider="openai"
)

perplexity = LLMConfig(
    model_name="llama-3.1-sonar-large-128k-online",  
    api_key=os.environ['PERPLEXITY_API_KEY'],
    temperature=0.5,
    max_tokens=8000,
    system_prompt="",
    provider="perplexity",
    base_url="https://api.perplexity.ai"
)

SUPPORTED_MODELS = {
    "flash2" : flash2,
    "o1-mini" : o1_mini,
    "perplexity" : perplexity,
    "preprocess" : preprocess,
    "explainer" : explainer
}

DEFAULT_MODEL = 'flash2'

LOGGING_DIR = Path("~/cli_llm/logs/").expanduser().resolve()
LOGGING_LEVEL = logging.INFO

SESSIONS_DIR = Path("~/Google Drive/My Drive/llm_sessions/").expanduser().resolve()

# between sets of queries-and-responses
DELIMITER = "=" * 20

INTERNAL_CHAT_DELIMITER = "*ChatBot*: "

ALLOWED_EXTENSIONS = {
    '.txt', '.md', '.py', '.js', '.jsx', '.ts', '.tsx', 
    '.html', '.css', '.json', '.yaml', '.yml', 
    '.pdf', '.doc', '.docx', '.rtf', '.sql', '.sh', '.bash', '.zsh', '.fish',
}
EXCLUDED_DIRS = {'.git', '.venv', '__pycache__', 'node_modules', 'build', 'dist', 'env', 'bin', 'lib', 'include', 'share', 'tmp', 'temp', 'cache'}

# Maximum tokens per file
MAX_TOKENS = 100_000

DEFAULT_METADATA = {
    "created_at": datetime.now().isoformat(),
    "llm_config": "flash2",
    "files": [],
    "search": [],
    "current_tokens": 0,
}

