from config_logger import logger
from config import ALLOWED_EXTENSIONS, MAX_TOKENS, SUPPORTED_MODELS
from src.llm import LLM

from tika import parser 
import os
import time
from pathlib import Path
from typing import List, Union, Dict
import tiktoken

class ContextManager:
    def __init__(
        self,
        location: Path,
        files: List[Union[str, Path]] = [],
        search: List[str] = [],
        query: str = "",
        chat_history: List[Dict[str, str]] = [],
        logger = logger
    ):
        self.location = location
        self.logger = logger
        self.query = query
        self.chat_history = chat_history
        self.files = files
        self.search_terms = search
        
        # Parse and add files if provided
        self.files_dir = self.location / "files"
        self.files_dir.mkdir(exist_ok=True)
        self.files_content = self.load_files() 
        
        # Parse and add search content if provided
        self.search_dir = self.location / "search"
        self.search_dir.mkdir(exist_ok=True)
        self.search_content = self.load_search()

    def get_messages(self) -> list[dict]:
        prompt = f"""
        <query>
            {self.query}
        </query>
        <files>
            {"\n".join([f"{filename}: {content}" for filename, content in self.files_content.items()])}
        </files>
        <search>
            {"\n".join([f"{search_term}: {content}" for search_term, content in self.search_content.items()])}
        </search>
 
        """
        messages = self.chat_history + [{"role": "user", "content": prompt}]
        self.logger.debug(f"Getting messages: {messages}")
        return messages 

    def _sanitize_filename(self, term: str) -> str:
        """Sanitize the search term to create a valid filename."""
        return "".join([c if c.isalnum() else "_" for c in term])

    def get_search_result(self, search_string: str) -> str:
        self.logger.info(f"Searching for: {search_string}")
        try:
            perplexity_llm = LLM(llm_config=SUPPORTED_MODELS['perplexity'])
            messages = [{"role" : "user", "content" : search_string}]
            response = perplexity_llm.query(messages)
            self.logger.info(f"Got search response back for {search_string}")
            self.logger.debug(f"Search response: {response}")
            return response
        except Exception as e:
            self.logger.error(f"Error in get_search_result: {e}")

    def load_search(self):
        """Load search content from files"""
        search_content = {}
        
        for search_term in self.search_terms:
            sanitized_search_term = self._sanitize_filename(search_term)
            search_file_path = self.search_dir / f"{sanitized_search_term}.txt"
            
            if not search_file_path.is_file():
                content = self.get_search_result(search_term)
                if content:
                    with open(search_file_path, "w+") as f:
                        f.write(content)
                else:
                    self.logger.error(f"Failed to get search result for {search_term}. Skipping.")
                    continue

            with open(search_file_path, "r") as f:
                content = f.read().strip()
                search_content[search_term] = content
            
        return search_content
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken"""
        try:
            encoding = tiktoken.get_encoding("cl100k_base")  # GPT-4 encoding
            return len(encoding.encode(text))
        except Exception as e:
            self.logger.error(f"Error counting tokens: {e}")
            return 0

    def process_file(self, file_path: Path) -> str:
        """Process a single file and return its content"""
        if not self.should_process_file(file_path):
            return ""
            
        session_file_path = self.files_dir / f"{file_path.stem}.txt"

        # Parse file if it hasn't been processed yet
        if session_file_path.name not in os.listdir(self.location):
            self.parse_file(
                file_path=file_path,
                destination_path=session_file_path
            )

        # Read and return the processed content
        try:
            with open(session_file_path, "r") as f:
                content = f.read().strip()
                if not content:
                    self.logger.error(f"File {file_path} is empty. Skipping.")
                    return ""
                return content
        except Exception as e:
            self.logger.error(f"Error reading {session_file_path}: {e}")
            return ""

    def load_files(self) -> Dict[str, str]:
        """Load all files and directories, processing each file encountered"""
        files_content = {}

        for path in self.files:
            path = Path(path).expanduser().resolve()
            
            if path.is_file():
                # Process single file
                content = self.process_file(path)
                if content:
                    files_content[path.stem] = content
                    
            elif path.is_dir():
                # Walk through directory recursively
                self.logger.info(f"Processing directory: {path}")
                for file_path in path.rglob('*'):
                    if file_path.is_file():
                        content = self.process_file(file_path)
                        if content:
                            files_content[file_path.stem] = content
            
        return files_content

    def should_process_file(self, file_path: Path) -> bool:
        if not file_path.is_file():
            return False
            
        # Skip already processed text files and check allowed extensions
        if file_path.suffix == '.txt' or file_path.suffix.lower() not in ALLOWED_EXTENSIONS:
            self.logger.debug(f"Skipping {file_path} - not in allowed extensions")
            return False

        return True

            
    def ocr(self, file_path):
        """Fallback function to parse a file if the parser fails."""
        import pytesseract
        from pdf2image import convert_from_path
        
        try:
            images = convert_from_path(file_path)
            text = ""
            for image in images:
                text += pytesseract.image_to_string(image)

            return text

        except Exception as e:
            self.logger.error(f"Error in fallback parsing: {e}")
            return ""

    def parse_file(self, file_path: Path, destination_path: Path):
        """Parses a file using Tika, with a fallback to OCR if Tika fails."""
        if not self.should_process_file(file_path):
            return ""

        start_time = time.time()

        try:
            parsed_file = parser.from_file(str(file_path), requestOptions={'timeout': 180})
            content = parsed_file['content']
        except Exception as e:
            self.logger.error(f"Failed parsing {file_path}. OCR'ing it. Error:\n\n {e}")
            content = self.ocr(file_path) 

        time_to_parse = time.time() - start_time

        self.logger.info(f"Parsing {file_path} took {time_to_parse} seconds. Writing to .txt file.")
        
        token_count = self.count_tokens(content)
        if token_count > MAX_TOKENS:
            self.logger.error(f"File {file_path} has {token_count} tokens, which is more than the maximum of {MAX_TOKENS}. Skipping.")
            return ""

        with open(destination_path, "w+") as f:
            f.write(content)

