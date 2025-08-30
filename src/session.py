from pathlib import Path
from typing import Tuple, Dict
import yaml
from config_logger import logger
import tiktoken

from config import DEFAULT_METADATA, SESSIONS_DIR, DELIMITER, INTERNAL_CHAT_DELIMITER, SUPPORTED_MODELS, DEFAULT_MODEL
from src.context_manager import ContextManager
from src.llm import LLM
from prompts.prompts import PROMPTS

class Session:
    def __init__(self, session_name:str, is_session:bool=True):
        self.session_name = session_name
        self.logger = logger

        if not is_session:
            self.session_file = Path(session_name).expanduser().resolve()
            if not self.session_file.exists():
                raise FileNotFoundError(f"File specified for run_file not found: {self.session_file}")
            self.session_dir = self.session_file.parent
            self.md_file = self.session_file
        else: 
            self.session_dir = Path(SESSIONS_DIR) / session_name
            self.md_file = self.session_dir / f"{session_name}.md"

        # Load session data: metadata, chat history. Images are handled by ContextManager via 'files' key.
        loaded_metadata, self.latest_query, self.chat_history = self.load_session_core()
        self.metadata = loaded_metadata
        
        self.context = ContextManager(
            location=self.session_dir,
            files=self.metadata.get('files', []), # 'files' now handles text and images
            search=self.metadata.get('search', []),
            # images parameter removed
            query=self.latest_query,
            chat_history=self.chat_history,
            is_session=is_session
        )
        self.llm_config_name = self.metadata.get('llm_config', DEFAULT_MODEL)
        if self.llm_config_name not in SUPPORTED_MODELS:
            self.logger.warning(
                f"LLM config '{self.llm_config_name}' not found in SUPPORTED_MODELS. "
                f"Falling back to default model '{DEFAULT_MODEL}'."
            )
            self.llm_config_name = DEFAULT_MODEL
            self.metadata['llm_config'] = DEFAULT_MODEL

        self.system_prompt_name = self.metadata.get('prompt', 'default')
        
        self.llm_config = SUPPORTED_MODELS[self.llm_config_name]

        if self.system_prompt_name in PROMPTS:
            self.logger.info(f"Using system prompt '{self.system_prompt_name}'")
            self.llm_config.system_prompt = PROMPTS[self.system_prompt_name]

        self.llm = LLM(
            llm_config=SUPPORTED_MODELS[self.llm_config_name]
        )

    def count_tokens(self, text) -> int:
        """Count tokens in text using tiktoken"""
        try:
            encoding = tiktoken.get_encoding("cl100k_base")  # GPT-4 encoding
            return len(encoding.encode(text))
        except Exception as e:
            self.logger.error(f"Error counting tokens: {e}")
            return 0

    def parse_chat_history(self, unstructured_text: str) -> Tuple[str, list[dict]]:
        """Going from raw .md file to chat history structured object"""
        blocks = unstructured_text.split(DELIMITER)

        # Handle empty file case
        if not blocks:
            return "", []
            
        _chat_history, latest_query = blocks[:-1], blocks[-1].strip()

        chat_history = []

        for chat in _chat_history:
            if INTERNAL_CHAT_DELIMITER not in chat:
                continue
                
            user_message, ai_response = chat.split(INTERNAL_CHAT_DELIMITER, 1)
           
            # validating user_message and ai_response in case empty:
            if user_message.strip() == "":
                user_message = "..."
            if ai_response.strip() == "":
                ai_response = "..."

            # Add each message individually to the chat history
            chat_history.append({
                "role": "user",
                "content": user_message.strip()
            })
            chat_history.append({
                "role": "assistant",
                "content": ai_response.strip()
            })

        return latest_query, chat_history

    def load_session_core(self) -> Tuple[Dict, str, list[dict]]:
        if not self.md_file.exists():
            self.logger.error(f"Session markdown file {self.md_file} not found.")
            return DEFAULT_METADATA.copy(), "", []

        with self.md_file.open('r', encoding='utf-8') as f:
            content = f.read()
            
        metadata = DEFAULT_METADATA.copy()
        _content_for_chat = content 

        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) == 3:
                _, _metadata_str, _content_after_yaml = parts
                try:
                    loaded_meta = yaml.safe_load(_metadata_str)
                    if loaded_meta is not None: 
                        metadata.update(loaded_meta)
                    _content_for_chat = _content_after_yaml
                except yaml.YAMLError as e:
                    self.logger.error(f"Error parsing YAML metadata in {self.session_name}: {e}. Using default metadata for YAML block, chat content follows.")
                    _content_for_chat = _content_after_yaml 
            else:
                self.logger.warning(f"Malformed YAML frontmatter in {self.session_name}. Content after first '---' will be parsed as chat.")
                _content_for_chat = parts[1] if len(parts) > 1 else ""
        
        # images_from_yaml logic removed here
            
        latest_query, chat_history = self.parse_chat_history(_content_for_chat)

        return metadata, latest_query, chat_history

    def run_session(self):
        """Passing new block since it was initialised and using"""
        messages = self.context.get_messages()

        n_tokens = sum([self.count_tokens(m['content']) for m in messages])
        self.metadata['current_tokens'] = n_tokens

        response = self.llm.query(messages=messages)

        self.logger.info(f"Using model {self.llm_config_name} to generate response...")

        with self.md_file.open('r') as f:
            content = f.read()
            if content.find('---') == -1:
                write_metadata = False
                self.logger.info("No metadata found in file, adding default metadata")
                body = content
            else:   
                _, _, body = content.split('---', 2)
                write_metadata = True

        # Recreating file from the bottom up
        with self.md_file.open('w') as f:
            if write_metadata:
                f.write('---\n')
                yaml.dump(self.metadata, f, default_flow_style=False)
                f.write('---')
           
            if body.strip() == "":
                f.write('\n')
            else:
                f.write(body)
            f.write(f'\n{INTERNAL_CHAT_DELIMITER}{response}\n\n')
            f.write(f"{DELIMITER}")
            
        self.logger.info(f"Session {self.session_name} updated with new response")
        return True
            


