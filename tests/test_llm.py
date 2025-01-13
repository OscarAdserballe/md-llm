import pytest
from unittest.mock import MagicMock, patch
from config import LLMConfig
from src.llm import LLM

@pytest.fixture
def mock_openai():
    with patch('src.llm.OpenAI') as MockOpenAI:
        yield MockOpenAI

def test_llm_initialization_openai(mock_openai):
    config = LLMConfig(
        model_name="o1-mini",
        api_key="test-openai-key",
        provider="openai"
    )
    llm = LLM(llm_config=config)
    mock_openai.assert_called_with(api_key="test-openai-key")
    assert llm.llm_config == config

def test_llm_initialization_other_provider(mock_openai):
    config = LLMConfig(
        model_name="custom-model",
        api_key="test-custom-key",
        provider="custom_provider",
        base_url="https://api.customprovider.com/v1/"
    )
    llm = LLM(llm_config=config)
    mock_openai.assert_called_with(api_key="test-custom-key", base_url="https://api.customprovider.com/v1/")
    assert llm.llm_config == config

def test_llm_query_openai(mock_openai):
    # Setup mock
    mock_instance = mock_openai.return_value
    mock_instance.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="Test response"))]
    )
    
    config = LLMConfig(
        model_name="o1-mini",
        api_key="test-openai-key",
        provider="openai"
    )
    llm = LLM(llm_config=config)

    messages = [{"role": "user", "content": "Hello"}]
    response = llm.query(messages)

    mock_instance.chat.completions.create.assert_called_with(
        model="o1-mini",
        n=1,
        messages=messages  # o1-mini uses messages as is
    )
    assert response == "Test response"

def test_llm_query_with_system_prompt(mock_openai):
    # Setup mock
    mock_instance = mock_openai.return_value
    mock_instance.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="System prompt response"))]
    )
    
    config = LLMConfig(
        model_name="gemini-2.0-flash-exp",
        api_key="test-gemini-key",
        provider="gemini",
        system_prompt="Test system prompt",
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
    )
    llm = LLM(llm_config=config)

    messages = [{"role": "user", "content": "Hello"}]
    response = llm.query(messages)

    expected_messages = [
        {"role": "system", "content": "Test system prompt"},
        {"role": "user", "content": "Hello"}
    ]

    mock_instance.chat.completions.create.assert_called_with(
        model="gemini-2.0-flash-exp",
        n=1,
        messages=expected_messages,
        max_tokens=8000,
        temperature=0.5
    )
    assert response == "System prompt response"
