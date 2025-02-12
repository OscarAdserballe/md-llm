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
with open(Path('~/cli_llm/config.yaml').expanduser().resolve(), 'r') as f:
    yaml_config = yaml.safe_load(f)

LOGGING_DIR = Path(yaml_config['logging']['dir']).expanduser().resolve()
LOGGING_LEVEL = getattr(logging, yaml_config['logging']['level'])

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

DEFAULT_METADATA = {
    "created_at": datetime.now().isoformat(),
    "llm_config": "flash",
    "files": [],
    "search": [],
    "current_tokens": 0,
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

flash = LLMConfig(
    model_name="gemini-2.0-flash-exp",
    api_key=os.environ['GEMINI_API_KEY'],
    temperature=0.5,
    max_tokens=8000,
    system_prompt=PROMPTS[DEFAULT_SYSTEM_PROMPT_NAME],
    provider="gemini",
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)
pro = LLMConfig(
    model_name="gemini-exp-1206",
    api_key=os.environ['GEMINI_API_KEY'],
    temperature=0.5,
    max_tokens=8000,
    system_prompt=PROMPTS[DEFAULT_SYSTEM_PROMPT_NAME],
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
learn = LLMConfig(
    model_name="learnlm-1.5-pro-experimental",
    api_key=os.environ['GEMINI_API_KEY'],
    temperature=0.5,
    max_tokens=8000,
    system_prompt="",
    provider="gemini",
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)
explainer = LLMConfig(
    model_name="learnlm-1.5-pro-experimental",
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
o3_mini = LLMConfig(
    model_name="o3-mini",
    api_key=os.environ['OPENAI_API_KEY'],
    temperature=0.5,
    max_tokens=100000,
    system_prompt=PROMPTS[DEFAULT_SYSTEM_PROMPT_NAME],
    provider="openai"
)

o1 = LLMConfig(
    model_name="o1",
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

from pydantic import BaseModel

class QuestionnaireResponse(BaseModel):
    q1_subscription_duration: int
    q2_delivery_days: int
    q3_reading_methods: list[int]
    q4_time_spent: int
    q5_preferred_subscription: int
    q6_format_preference: int
    q7_subscription_reasons: list[int]
    q8_overall_satisfaction: int
    q9_miss_if_not_read_agreement: int
    q10_recommendation_likelihood: int
    q11_renewal_likelihood: int
    q12_website_visit_frequency: int
    q13_trust_level: int
    q14_new_app_usage: int
    q15_listening_habits: int
    q16_games_familiarity: int
    q17_games_in_paper: int
    q18_culture_best: list[int]
    q19_existence_best: list[int]
    q20_news_media_best: list[int]
    q21_church_calendar_usage: int
    q22_new_section: int
    q23_new_section_desired: str
    q24_member_advantages: int
    q25_radio_tv_usage_daily: int
    q26_radio_tv_usage_weekly: int
    q27_digital_radio_tv_access: int
    q28_gender: int
    q29_age_group: int
    q30_occupation: int
    q31_occupation_field: str
    q32_postcode: int
    q33_share_reader_experience: int
    q34_name: str
    q35_address: str
    q36_city: str
    q37_email: str
    q38_phone_number: str
    q39_want_to_receive_offers: bool
    q40_improvement_suggestions: str


marketing_survey_object = LLMConfig(
    model_name="gemini-2.0-flash-exp",
    api_key=os.environ['GEMINI_API_KEY'],
    temperature=0.5,
    max_tokens=8000,
    system_prompt="""
    You are tasked with extracting content from unstructed pictures to structured output.
    It is IMPERATIVE that,
        1) You always fill out an answer - if you're unsure, just put 99 if an int field, or 'UNSURE' if string field,
        2) Instead of giving the answer choice they circled, instead put the number corresponding to which option they choose. I.e. if they answer 3-5 years which is the third option for the first question, you should put down 3.
        3) If they don't fill out an answer choice, just put in "UNFILLED" or 100. NEVER return a null value 

    Be ABSOLUTELY SURE, that you do not fill out the content of the choices in multiple choice settings - ONLY AN INTEGER OR A LIST.

    """,
    provider="gemini",
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    response_format=QuestionnaireResponse
)
marketing_survey_object_openai = LLMConfig(
    model_name="gpt-4o",
    api_key=os.environ['OPENAI_API_KEY'],
    temperature=0.5,
    max_tokens=8000,
    system_prompt="""
    You are tasked with extracting content from unstructed pictures to structured output.
    It is IMPERATIVE that,
        1) You always fill out an answer - if you're unsure, just put 99 if an int field, or 'UNSURE' if string field,
        2) Instead of giving the answer choice they circled, instead put the number corresponding to which option they choose. I.e. if they answer 3-5 years which is the third option for the first question, you should put down 3.
        3) If they don't fill out an answer choice, just put in "UNFILLED" or 100    

    Be ABSOLUTELY SURE, that you do not fill out the content of the choices in multiple choice settings - ONLY AN INTEGER OR A LIST.
    Take a chain of thought approach. For each option, count the number of options. Then, find the one that's somehow been marked by a pen and then note that number.

    """,
    provider="openai",
    # base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    response_format=QuestionnaireResponse
)

# llm --vision="/home/adserballe@kd3.int/Documents/GitHub/analysis/analysis/01-2025_marketing_survey/Læserundersøgelse/IMG_6530.HEIC" "what's contained in this image"

SUPPORTED_MODELS = {
    "flash" : flash,
    "flash2" : flash,
    "o3-mini" : o3_mini,
    "o1" : o1,
    "perplexity" : perplexity,
    "preprocess" : preprocess,
    "explainer" : explainer,
    "pro" : pro,
    "learn" : learn,
    "marketing" : marketing_survey_object,
    "marketing_openai" : marketing_survey_object_openai,
    "report": report,
}




