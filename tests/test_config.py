import os
import pytest
from config import LLMConfig, SUPPORTED_MODELS, DEFAULT_MODEL, PROMPTS

def test_llm_config_defaults():
    config = LLMConfig(
        model_name="test-model",
        api_key="test-api-key"
    )
    assert config.model_name == "test-model"
    assert config.api_key == "test-api-key"
    assert config.temperature == 0.5  # Default value
    assert config.max_tokens == 8000   # Default value
    assert config.system_prompt == PROMPTS["default"]
    assert config.provider == "openai"  # Default value
    assert config.base_url is None
    assert config.tools is None

def test_supported_models():
    assert "flash2" in SUPPORTED_MODELS
    assert "o1-mini" in SUPPORTED_MODELS
    assert "perplexity" in SUPPORTED_MODELS
    assert "preprocess" in SUPPORTED_MODELS
    assert "explainer" in SUPPORTED_MODELS

    flash2 = SUPPORTED_MODELS["flash2"]
    assert flash2.model_name == "gemini-2.0-flash-exp"
    assert flash2.provider == "gemini"
    assert flash2.base_url == "https://generativelanguage.googleapis.com/v1beta/openai/"

