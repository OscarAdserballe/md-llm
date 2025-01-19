from openai import OpenAI

from config_logger import logger
from config import LLMConfig

class LLM:
    def __init__(
            self,
            llm_config: LLMConfig, 
            logger = logger,
        ):
        self.llm_config = llm_config
        self.logger = logger

        # using OpenAI wrapper
        if self.llm_config.provider == "openai":
            self.model = OpenAI(
                api_key=self.llm_config.api_key
            )
        else: # for any other provider, we need a base_url
            self.model = OpenAI(
                api_key=self.llm_config.api_key,
                base_url=self.llm_config.base_url,
            )

    def query(self, messages: list[dict], stream: bool=False) -> str:
        if self.llm_config.model_name in ["o1-mini", "o1", "o1-preview"]:
            full_messages = messages
        else: 
            full_messages = [{"role": "system", "content": self.llm_config.system_prompt}] + messages
        
        response_params ={
            "model": self.llm_config.model_name,
            "n": 1,
            "messages": full_messages,
        }

        if stream:
            response_params["stream"] = True

        # o1-mini does not support these parameters
        if self.llm_config.model_name not in ["o1-mini", "o1", "o1-preview"]:
            response_params["max_tokens"] = self.llm_config.max_tokens
            response_params["temperature"] = self.llm_config.temperature

        # e.g. search for gemini models
        if self.llm_config.tools is not None:
            response_params["tools"] = [self.llm_config.tools]
            response_params["tool_choice"] = "auto"

        response = self.model.chat.completions.create(
            **response_params
        )

        if stream:
            return response
    
        return response.choices[0].message.content
