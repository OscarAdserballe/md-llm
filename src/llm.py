from openai import OpenAI
from typing import List, Dict, Optional
from config_logger import logger
from pathlib import Path
from config import LLMConfig
import google.generativeai as genai

REASONING_MODELS = ["o1-mini", "o1", "o1-preview", "o3-mini"]

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
        # if self.llm_config.provider == "gemini":
        #     return self.query_gemini(messages, stream)
        #
        # # Default to OpenAI which has the broadest api support
        # else:
        return self.query_openai(messages, stream)
        
    # WIP
    def query_gemini(self, messages: List[Dict[str, str]], stream: bool = False) -> Optional[str]:
        genai.configure(api_key=self.llm_config.api_key)
        model = genai.get_model(self.llm_config.model_name)
        
        ### Preparing Messages going into LLM ####
        full_messages = []

        if self.llm_config.model_name not in REASONING_MODELS:
            full_messages.append({"role": "system", "content": self.llm_config.system_prompt})

        full_messages.extend(messages)


        #### Preparing Response Parameters ####

        # Example message:
        # completion = client.beta.chat.completions.parse(
        #     model="gemini-1.5-flash",
        #     messages=[
        #         {"role": "system", "content": "Extract the event information."},
        #         {"role": "user", "content": "John and Susan are going to an AI conference on Friday."},
        #     ],
        #     response_format=CalendarEvent,
        # )

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
                response = self.model.beta.chat.completions.parse(**response_params)
                return response.choices[0].message.parsed.model_dump_json(indent=2)
            
            # every other case
            else:
                response = self.model.chat.completions.create(**response_params)

                # 1. Streaming case
                if stream:
                    return response
                
                # 2. Base case
                return response.choices[0].message.content

        except Exception as e:
            self.logger.error(f"Error querying LLM: {e}")
            return None

    def query_openai(self, messages: List[Dict[str, str]], stream: bool = False) -> Optional[str]:

        ### Preparing Messages going into LLM ####
        full_messages = []

        if self.llm_config.model_name not in REASONING_MODELS:
            full_messages.append({"role": "system", "content": self.llm_config.system_prompt})

        full_messages.extend(messages)


        #### Preparing Response Parameters ####

        # Example message:
        # completion = client.beta.chat.completions.parse(
        #     model="gemini-1.5-flash",
        #     messages=[
        #         {"role": "system", "content": "Extract the event information."},
        #         {"role": "user", "content": "John and Susan are going to an AI conference on Friday."},
        #     ],
        #     response_format=CalendarEvent,
        # )

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
                response = self.model.beta.chat.completions.parse(**response_params)
                return response.choices[0].message.parsed.model_dump_json(indent=2)
            
            # every other case
            else:
                response = self.model.chat.completions.create(**response_params)

                # 1. Streaming case
                if stream:
                    return response
                
                # 2. Base case
                return response.choices[0].message.content

        except Exception as e:
            self.logger.error(f"Error querying LLM: {e}")
            return None

