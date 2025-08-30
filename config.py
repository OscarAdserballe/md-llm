import os
from pathlib import Path
import logging
from dataclasses import dataclass   
from datetime import datetime
from dotenv import load_dotenv
import yaml
from pydantic import BaseModel
from prompts.prompts import PROMPTS

load_dotenv()
# Load config from YAML
with open(Path('~/Projects/cli_llm/config.yaml').expanduser().resolve(), 'r') as f:
    yaml_config = yaml.safe_load(f)

LOGGING_DIR = Path(yaml_config['logging']['dir']).expanduser().resolve()
LOGGING_LEVEL = getattr(logging, yaml_config['logging']['level'])
DEFAULT_PAPERS_OUTPUT_DIR = Path("~/Google Drive/My Drive/Obsidian/Papers/").expanduser().resolve()

SESSIONS_DIR = Path(yaml_config['sessions']['dir']).expanduser().resolve()

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

# Supported image extensions
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'}

DEFAULT_METADATA = {
    "created_at": datetime.now().isoformat(),
    "llm_config": "flash",
    "files": [],
    "search": [],
    "current_tokens": 0,
    "prompt": "default"
}

DEFAULT_MODEL = 'flash'
DEFAULT_SYSTEM_PROMPT_NAME = "default" 

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
    response_format: type[BaseModel] | None = None
    extended_thinking: bool | None = None 
    budget_tokens: int | None = None # budget for thinking tokens

flash = LLMConfig(
    model_name="gemini-2.5-flash",
    api_key=os.environ['GEMINI_API_KEY'],
    temperature=0.5,
    max_tokens=8000,
    system_prompt=PROMPTS["default"],
    provider="gemini",
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)
claude = LLMConfig(
    model_name="claude-sonnet-4-20250514",
    api_key=os.environ['ANTHROPIC_API_KEY'],
    temperature=0.5,
    max_tokens=8000,
    system_prompt=PROMPTS[DEFAULT_SYSTEM_PROMPT_NAME],
    provider="anthropic",
    base_url="https://api.anthropic.com/v1/",
)
pro = LLMConfig(
    model_name="gemini-2.5-pro",
    api_key=os.environ['GEMINI_API_KEY'],
    temperature=0.5,
    max_tokens=32000,
    system_prompt=PROMPTS["default"],
    provider="gemini",
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)
report = LLMConfig(
    model_name="gemini-exp-1206",
    api_key=os.environ['GEMINI_API_KEY'],
    temperature=0.5,
    max_tokens=8000,
    system_prompt=PROMPTS["report"],
    provider="gemini",
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)
explainer = LLMConfig(
    model_name="gemini-2.5-pro",
    api_key=os.environ['GEMINI_API_KEY'],
    temperature=0.5,
    max_tokens=8000,
    system_prompt=PROMPTS['explain'],
    provider="gemini",
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)
o4_mini = LLMConfig(
    model_name="o4-mini",
    api_key=os.environ['OPENAI_API_KEY'],
    temperature=0.5,
    max_tokens=100000,
    system_prompt=PROMPTS[DEFAULT_SYSTEM_PROMPT_NAME],
    provider="openai"
)
visualise = LLMConfig(
    model_name="gemini-2.0-flash",
    api_key=os.environ['GEMINI_API_KEY'],
    temperature=0.0,
    max_tokens=8000,
    system_prompt=PROMPTS['visualise'],
    provider="gemini",
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)
o3 = LLMConfig(
    model_name="o3",
    api_key=os.environ['OPENAI_API_KEY'],
    temperature=0.5,
    max_tokens=65536,
    system_prompt=PROMPTS[DEFAULT_SYSTEM_PROMPT_NAME],
    provider="openai"
)
perplexity = LLMConfig(
    model_name="sonar",  
    api_key=os.environ['PERPLEXITY_API_KEY'],
    temperature=0.5,
    max_tokens=8000,
    system_prompt="",
    provider="perplexity",
    base_url="https://api.perplexity.ai"
)

SUPPORTED_MODELS = {
    "flash" : flash,
    "o4-mini" : o4_mini,
    "o3" : o3,
    "perplexity" : perplexity,
    "explainer" : explainer,
    "pro" : pro,
    "report": report,
    "visualise": visualise,
    "claude": claude,
}
