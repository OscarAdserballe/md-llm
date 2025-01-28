from openai import OpenAI
import base64
from typing import List, Dict, Optional
from pydantic import BaseModel
from config_logger import logger
from config import LLMConfig

class LLM:
    def __init__(self, llm_config: LLMConfig):
        self.llm_config = llm_config
        self.logger = logger

        if self.llm_config.provider == "openai":
            self.model = OpenAI(api_key=self.llm_config.api_key)
        else:
            self.model = OpenAI(
                api_key=self.llm_config.api_key,
                base_url=self.llm_config.base_url,
            )

    def query(self, messages: List[Dict[str, str]], stream: bool = False) -> Optional[str]:
        if self.llm_config.model_name not in ["o1-mini", "o1", "o1-preview"]:
            full_messages = [{"role": "system", "content": self.llm_config.system_prompt}] + messages
        else:
            full_messages = messages

        response_params = {
            "model": self.llm_config.model_name,
            "n": 1,
            "messages": full_messages,
        }

        if stream:
            response_params["stream"] = True

        if self.llm_config.model_name not in ["o1-mini", "o1", "o1-preview"]:
            response_params["max_tokens"] = self.llm_config.max_tokens
            response_params["temperature"] = self.llm_config.temperature

        if self.llm_config.tools:
            response_params["tools"] = self.llm_config.tools
            response_params["tool_choice"] = "auto"

        try:
            response = self.model.chat.completions.create(**response_params)
            if stream:
                return response
            return response.choices[0].message.content
        except Exception as e:
            self.logger.error(f"Error querying LLM: {e}")
            return None

    def encode_image(self, image_path: str) -> str:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    def vision_query(self, image_path: str) -> Optional[str]:
        base64_image = self.encode_image(image_path)
        try:
            response = self.model.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "What is in this image?"},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}},
                        ],
                    }
                ],
            )
            return response.choices[0].message.content
        except Exception as e:
            self.logger.error(f"Error processing vision query: {e}")
            return None

    def structured_parse(
        self, 
        model_name: str, 
        messages: List[Dict[str, str]], 
        response_format: BaseModel
    ) -> Optional[BaseModel]:
        try:
            client = OpenAI()
            completion = client.beta.chat.completions.parse(
                model=model_name,
                messages=messages,
                response_format=response_format,
            )
            return completion.choices[0].message.parsed
        except Exception as e:
            self.logger.error(f"Error in structured parsing: {e}")
            return None

