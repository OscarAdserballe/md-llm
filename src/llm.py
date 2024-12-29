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

        if self.llm_config.provider == "openai":
            self.model = OpenAI(
                api_key=self.llm_config.api_key
            )
        else: # for any other provider, we need a base_url
            self.model = OpenAI(
                api_key=self.llm_config.api_key,
                base_url=self.llm_config.base_url,
            )

    def query(self, messages: list[dict]) -> str:
        if self.llm_config.model_name == "o1-mini":
            full_messages = messages
        else: 
            full_messages = [{"role": "system", "content": self.llm_config.system_prompt}] + messages
        
        response_params ={
            "model": self.llm_config.model_name,
            "n": 1,
            "messages": full_messages,
        }
        if self.llm_config.model_name != "o1-mini":
            response_params["max_tokens"] = self.llm_config.max_tokens
            response_params["temperature"] = self.llm_config.temperature

        response = self.model.chat.completions.create(
            **response_params
        )

        return response.choices[0].message.content
