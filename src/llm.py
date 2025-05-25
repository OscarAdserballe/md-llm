from openai import OpenAI
from typing import List, Dict, Optional, Any, Union
from config_logger import logger
from pathlib import Path
from config import LLMConfig
import google.generativeai as genai
import base64
import anthropic

REASONING_MODELS = ["o1-mini", "o1", "o1-preview", "o3-mini"]

class LLMProvider:
    """Base class for different LLM providers"""
    def __init__(self, llm_config: LLMConfig):
        self.llm_config = llm_config
        self.logger = logger

    def query(self, messages: List[Dict[str, Any]], stream: bool = False) -> Optional[Union[str, Any]]:
        raise NotImplementedError("Subclasses must implement query method")

    def prepare_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prepare messages in the format expected by the provider"""
        full_messages = []
        
        # Add system prompt if needed for this model
        if self.llm_config.model_name not in REASONING_MODELS:
            full_messages.append({"role": "system", "content": self.llm_config.system_prompt})
            
        full_messages.extend(messages)
        return full_messages

class OpenAIProvider(LLMProvider):
    def __init__(self, llm_config: LLMConfig):
        super().__init__(llm_config)
        if self.llm_config.base_url:
            self.client = OpenAI(
                api_key=self.llm_config.api_key,
                base_url=self.llm_config.base_url,
            )
        else:
           self.client = OpenAI(api_key=self.llm_config.api_key)

    def query(self, messages: List[Dict[str, Any]], stream: bool = False) -> Optional[Union[str, Any]]:
        full_messages = self.prepare_messages(messages)
        
        response_params = {
            "model": self.llm_config.model_name,
            "n": 1,
            "messages": full_messages,
        }

        if stream:
            response_params["stream"] = True

        if self.llm_config.model_name not in REASONING_MODELS:
            response_params["max_tokens"] = self.llm_config.max_tokens
            response_params["temperature"] = self.llm_config.temperature

        if self.llm_config.model_name == "o3-mini":
            response_params["reasoning_effort"] = "high"

        if self.llm_config.tools:
            response_params["tools"] = self.llm_config.tools
            response_params["tool_choice"] = "auto"

        if self.llm_config.response_format:
            response_params["response_format"] = self.llm_config.response_format

        try:
            # If structured output, calling different method
            if self.llm_config.response_format:
                response = self.client.beta.chat.completions.parse(**response_params)
                return response.choices[0].message.parsed.model_dump_json(indent=2)
            
            # every other case
            else:
                response = self.client.chat.completions.create(**response_params)

                # 1. Streaming case
                if stream:
                    return response
                
                # 2. Base case
                return response.choices[0].message.content

        except Exception as e:
            self.logger.error(f"Error querying OpenAI: {e}")
            return None

class GeminiProvider(LLMProvider):
    def __init__(self, llm_config: LLMConfig):
        super().__init__(llm_config)
        genai.configure(api_key=self.llm_config.api_key)
        self.client = OpenAI(
            api_key=self.llm_config.api_key,
            base_url=self.llm_config.base_url,
        )

    def query(self, messages: List[Dict[str, Any]], stream: bool = False) -> Optional[Union[str, Any]]:
        full_messages = self.prepare_messages(messages)
        
        response_params = {
            "model": self.llm_config.model_name,
            "n": 1,
            "messages": full_messages,
        }

        if stream:
            response_params["stream"] = True

        if self.llm_config.model_name not in REASONING_MODELS:
            response_params["max_tokens"] = self.llm_config.max_tokens
            response_params["temperature"] = self.llm_config.temperature

        if self.llm_config.tools:
            response_params["tools"] = self.llm_config.tools
            response_params["tool_choice"] = "auto"

        if self.llm_config.response_format:
            response_params["response_format"] = self.llm_config.response_format

        try:
            # If structured output, calling different method
            if self.llm_config.response_format:
                response = self.client.beta.chat.completions.parse(**response_params)
                return response.choices[0].message.parsed.model_dump_json(indent=2)
            
            # every other case
            else:
                response = self.client.chat.completions.create(**response_params)

                # 1. Streaming case
                if stream:
                    return response
                
                # 2. Base case
                return response.choices[0].message.content

        except Exception as e:
            self.logger.error(f"Error querying Gemini: {e}")
            return None

class AnthropicProvider(LLMProvider):
    def __init__(self, llm_config: LLMConfig):
        super().__init__(llm_config)
        self.client = anthropic.Anthropic(api_key=self.llm_config.api_key)
    
    def prepare_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert messages to Anthropic format"""
        anthropic_messages = []
        
        # Process user messages
        for message in messages:

            if message["role"] == "user":
                content_items = []

                if isinstance(message["content"], list):
                    # Handle multimodal content
                    for item in message["content"]:

                        if isinstance(item, dict):

                            if item.get("type") == "image_url":

                                # Handle image
                                image_url = item["image_url"]["url"]
                                if image_url.startswith("data:image"):
                                    # Extract base64 data
                                    base64_data = image_url.split(",")[1]
                                    content_items.append({
                                        "type": "image",
                                        "source": {
                                            "type": "base64",
                                            "media_type": "image/jpeg",
                                            "data": base64_data
                                        }
                                    })

                            elif item.get("type") == "text":
                                content_items.append({
                                    "type": "text",
                                    "text": item["text"]
                                })
                else:

                    # Simple text message
                    content_items.append({
                        "type": "text",
                        "text": message["content"]
                    })
                
                anthropic_messages.append({
                    "role": "user",
                    "content": content_items
                })
            elif message["role"] == "assistant":

                anthropic_messages.append({
                    "role": "assistant",
                    "content": message["content"]
                })
        
        return anthropic_messages
    
    def query(self, messages: List[Dict[str, Any]], stream: bool = False) -> Optional[str]:
        anthropic_messages = self.prepare_messages(messages)
        
        response_params = {
            "model": self.llm_config.model_name,
            "max_tokens": self.llm_config.max_tokens,
            "temperature": self.llm_config.temperature,
            "messages": anthropic_messages,
        }
        
        if self.llm_config.system_prompt:
            response_params["system"] = self.llm_config.system_prompt
            
        # Add extended thinking parameters if enabled
        if self.llm_config.extended_thinking:
            response_params['temperature'] = 1 # must be set to 1 for extended thinking
            response_params["thinking"] = {
                "type": "enabled",
                "budget_tokens": self.llm_config.budget_tokens, 
            }
            
        if stream:
            response = self.client.messages.stream(**response_params)
            return response
        else:
            response = self.client.messages.create(**response_params)
            
            # Extract text content from response
            for block in response.content:
                if block.type == "text":
                    return block.text
                
                if block.type == "thinking":
                    print("Thinking Block...")
                    print(block.thinking)
            
            return None

class LLM:
    def __init__(self, llm_config: LLMConfig):
        self.llm_config = llm_config
        self.logger = logger
        
        # Initialize the appropriate provider based on config
        if self.llm_config.provider == "openai":
            self.provider = OpenAIProvider(llm_config)
        elif self.llm_config.provider == "gemini":
            self.provider = GeminiProvider(llm_config)
        elif self.llm_config.provider == "anthropic":
            self.provider = AnthropicProvider(llm_config)
        elif self.llm_config.provider == "perplexity":
            # Default to OpenAI provider since perplexity uses OpenAI-compatible API
            self.provider = OpenAIProvider(llm_config)
        else:
            # Default to OpenAI for unknown providers
            self.logger.warning(f"Unknown provider {self.llm_config.provider}, using OpenAI provider")
            self.provider = OpenAIProvider(llm_config)

    def query(self, messages: List[Dict[str, Any]], stream: bool = False) -> Optional[Union[str, Any]]:
        """Query the LLM using the appropriate provider"""
        return self.provider.query(messages, stream)
    
    def process_pdf(self, pdf_path: Path, prompt: str) -> Optional[str]:
        """Process a PDF file and generate a response based on its content"""
        try:
            # Import file processor here to avoid circular imports
            from src.file_processor import FileProcessor
            processor = FileProcessor()
            
            # Extract text from PDF
            pdf_text = processor.extract_pdf_text(pdf_path)
            if not pdf_text:
                self.logger.error(f"Failed to extract text from PDF: {pdf_path}")
                return None
                
            # Check if we got a token limit error message
            if pdf_text.startswith("[PDF too large"):
                self.logger.warning(f"PDF {pdf_path} skipped due to token limit")
                return f"Could not process {pdf_path.name}: {pdf_text}"
                
            # Create message with PDF content
            response = self.query([
                {
                    "role": "user",
                    "content": f"PDF Content:\n\n{pdf_text}\n\n{prompt}"
                }
            ])
            
            return response
        except Exception as e:
            self.logger.error(f"Error processing PDF: {e}")
            return None