from pathlib import Path
from typing import Tuple, Dict
import yaml
from config_logger import logger
import tiktoken

from config import DEFAULT_METADATA, SESSIONS_DIR, DELIMITER, INTERNAL_CHAT_DELIMITER, SUPPORTED_MODELS, DEFAULT_MODEL
from src.context_manager import ContextManager
from src.llm import LLM

class Session:
    def __init__(self, session_name:str, is_session:bool=True):
        self.session_name = session_name

        if not is_session:
            self.session_file = Path(session_name).expanduser().resolve()
            self.session_dir = self.session_file.parent
            self.md_file = self.session_file
        else: # otherwise, assume it's a session
            self.session_dir = Path(SESSIONS_DIR) / session_name
            self.md_file = self.session_dir / f"{session_name}.md"

        self.metadata, self.latest_query, self.chat_history = self.load_session()
        
        # passing query and chat_history from ContextManager
        self.context = ContextManager(
            location=self.session_dir,
            files=self.metadata.get('files', []),
            search=self.metadata.get('search', []),
            query=self.latest_query,
            chat_history=self.chat_history,
        )
        self.llm_config = SUPPORTED_MODELS[self.metadata.get('llm_config', DEFAULT_MODEL)]
        self.llm = LLM(
            llm_config=SUPPORTED_MODELS[self.metadata.get('llm_config', DEFAULT_MODEL)]   # default to flash2 
        )
        self.logger = logger

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

    def load_session(self) -> Tuple[Dict, str, list[dict]]:
        if not self.md_file.exists():
            raise FileNotFoundError(f"Session {self.session_name} not found")

        with self.md_file.open('r') as f:
            content = f.read()
            # Extract YAML metadata between first --- markers
            if content.startswith('---'):
                _, _metadata, _content = content.split('---', 2) # max twice to ensure not out of index.
                
                metadata = yaml.safe_load(_metadata)
                latest_query, chat_history = self.parse_chat_history(_content)

            else:
                metadata = DEFAULT_METADATA
                latest_query, chat_history = self.parse_chat_history(content)


        return metadata, latest_query, chat_history

    def run_session(self):
        """Passing new block since it was initialised and using"""
        messages = self.context.get_messages()

        n_tokens = sum([self.count_tokens(m['content']) for m in messages])
        self.metadata['current_tokens'] = n_tokens

        response = self.llm.query(messages=messages)

        self.logger.info(f"Using model {self.llm_config.model_name} to generate response...")

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
            


