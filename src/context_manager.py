from config_logger import logger
from config import ALLOWED_EXTENSIONS, MAX_TOKENS, SUPPORTED_MODELS, EXCLUDED_DIRS, IMAGE_EXTENSIONS
from src.llm import LLM
from src.file_processor import FileProcessor

from tika import parser 
import os
import time
from pathlib import Path
from typing import List, Union, Dict, Any
import tiktoken
from typing import Set

class ContextManager:
    def __init__(
        self,
        location: Path,
        files: List[Union[str, Path]] = [],
        search: List[str] = [],
        query: str = "",
        chat_history: List[Dict[str, str]] = [],
        logger = logger,
        is_session: bool = False
    ):
        self.location = location
        self.logger = logger
        self.query = query
        self.chat_history = chat_history
        self.files = files
        self.search_terms = search
        self.is_session = is_session
        
        self.file_processor = FileProcessor()
        
        self.files_dir = self.location / "files"
        self.files_dir.mkdir(exist_ok=True, parents=True)
        
        self.files_content: Dict[str, Union[str, Dict[str, Any]]] = self.load_files() 
        
        self.search_dir = self.location / "search"
        self.search_dir.mkdir(exist_ok=True, parents=True)
        self.search_content = self.load_search()

    def generate_tree(self, directory: Path, prefix: str = "", exclude_dirs: Set[str] | None = None) -> str:
        """Generate a tree view of the directory structure"""
        if exclude_dirs is None:
            exclude_dirs = set(EXCLUDED_DIRS)
            
        tree = ""
        directory = Path(directory)
        
        # Get all items in directory
        items = sorted(directory.glob("*"))
        
        # Filter out excluded directories and their contents
        items = [item for item in items if not any(excluded in str(item) for excluded in exclude_dirs)]
        
        for i, path in enumerate(items):
            is_last = i == len(items) - 1
            node = "└──" if is_last else "├──"
            
            tree += f"{prefix}{node} {path.name}\n"
            
            if path.is_dir():
                extension = "    " if is_last else "│   "
                tree += self.generate_tree(
                    path,
                    prefix=prefix + extension,
                    exclude_dirs=exclude_dirs
                )
                
        return tree

    def get_messages(self) -> list[dict]:
        user_content_parts: List[Dict[str, Any]] = []
        text_prompt_elements: List[str] = []

        project_structure = ""
        for item_path_str in self.files:
            path = Path(item_path_str).expanduser().resolve()
            original_path_in_session = (self.location / Path(item_path_str)).resolve() if not Path(item_path_str).is_absolute() else Path(item_path_str).resolve()

            if original_path_in_session.is_dir():
                project_structure += f"\nProject structure for {original_path_in_session}:\n"
                project_structure += self.generate_tree(original_path_in_session)
        
        if project_structure:
            text_prompt_elements.append(project_structure.strip())

        # Query
        text_prompt_elements.append(f"<query>\n{self.query}\n</query>")

        # Files content (text and images)
        if self.files_content:
            text_files_str_parts = []
            for filename_or_key, content_item in self.files_content.items():
                if isinstance(content_item, str):
                    text_files_str_parts.append(f"--- {filename_or_key} ---\n{content_item}")
                elif isinstance(content_item, dict) and content_item.get("type") == "image_url":
                    user_content_parts.append(content_item)
                    self.logger.debug(f"Added image {filename_or_key} to session messages from files_content.")
            
            if text_files_str_parts:
                text_prompt_elements.append(f"<files>\n{''.join(text_files_str_parts)}\n</files>")

        # Search content
        if self.search_content:
            search_str = "\n".join([f"--- {search_term} ---\n{content}" for search_term, content in self.search_content.items()])
            text_prompt_elements.append(f"<search>\n{search_str}\n</search>")
        
        if text_prompt_elements:
            full_text_prompt = "\n\n".join(text_prompt_elements).strip()
            user_content_parts.insert(0, {"type": "text", "text": full_text_prompt})

        final_user_content: Union[str, List[Dict[str, Any]]]
        if not user_content_parts:
            final_user_content = "" 
            self.logger.warning("User content parts are empty in get_messages.")
        elif len(user_content_parts) == 1 and user_content_parts[0]["type"] == "text":
            final_user_content = user_content_parts[0]["text"]
        else:
            final_user_content = user_content_parts

        messages = self.chat_history + [{"role": "user", "content": final_user_content}]
        self.logger.debug(f"Getting messages for session: {messages}")
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
            return response if response else ""
        except Exception as e:
            self.logger.error(f"Error in get_search_result: {e}")
            return ""

    def load_search(self):
        """Load search content from files or memory based on is_file flag"""
        search_content = {}
        
        for search_term in self.search_terms:
            if not self.is_session:
                content = self.get_search_result(search_term)
                if content:
                    search_content[search_term] = content
                else:
                    self.logger.error(f"Failed to get search result for {search_term} (non-session). Skipping.")
                continue
            
            sanitized_search_term = self._sanitize_filename(search_term)
            search_file_path = self.search_dir / f"{sanitized_search_term}.txt"
            
            if not search_file_path.is_file():
                content = self.get_search_result(search_term)
                if content:
                    with open(search_file_path, "w+", encoding='utf-8') as f:
                        f.write(content)
                else:
                    self.logger.error(f"Failed to get search result for {search_term} (session). Skipping file write.")
                    continue

            with open(search_file_path, "r", encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    search_content[search_term] = content
            
        return search_content
    
    def count_tokens(self, text) -> int:
        """Count tokens in text using tiktoken"""
        if not isinstance(text, str):
            self.logger.warning(f"Attempted to count tokens on non-string type: {type(text)}. Returning 0.")
            return 0
        try:
            encoding = tiktoken.get_encoding("cl100k_base")  # GPT-4 encoding
            return len(encoding.encode(text))
        except Exception as e:
            self.logger.error(f"Error counting tokens: {e}")
            return 0

    def load_files(self) -> Dict[str, Union[str, Dict[str, Any]]]:
        """
        Load all files and directories specified in self.files.
        Processes text files and image files differently.
        Caches text file content to session's files_dir.
        Image data is processed directly.
        """
        processed_content_map: Dict[str, Union[str, Dict[str, Any]]] = {}

        for item_path_str in self.files:
            item_path = Path(item_path_str)
            
            resolved_path: Path | None = None
            if item_path.is_absolute():
                if item_path.exists():
                    resolved_path = item_path
            else:
                potential_path = (self.location / item_path).resolve()
                if potential_path.exists():
                    resolved_path = potential_path

            if not resolved_path:
                self.logger.warning(f"Path specified in session files list does not exist or could not be resolved: {item_path_str} (tried from {self.location})")
                continue

            if resolved_path.is_file():
                if resolved_path.suffix.lower() in IMAGE_EXTENSIONS:
                    try:
                        image_data = self.file_processor.process_image(str(resolved_path))
                        processed_content_map[resolved_path.name] = image_data
                        self.logger.info(f"Processed image file from 'files' list: {resolved_path}")
                    except Exception as e:
                        self.logger.error(f"Error processing image file {resolved_path} from 'files' list: {e}")
                elif self.should_process_file(resolved_path):
                    content = self._process_and_cache_text_file(resolved_path)
                    if content:
                        processed_content_map[resolved_path.name] = content
                else:
                    self.logger.debug(f"Skipping file (not image, or did not pass should_process_file): {resolved_path}")

            elif resolved_path.is_dir():
                self.logger.info(f"Processing directory specified in session files: {resolved_path}")
                for file_in_dir in resolved_path.rglob('*'):
                    if file_in_dir.is_file():
                        relative_key = str(file_in_dir.relative_to(resolved_path))
                        if file_in_dir.suffix.lower() in IMAGE_EXTENSIONS:
                            try:
                                image_data = self.file_processor.process_image(str(file_in_dir))
                                processed_content_map[relative_key] = image_data
                                self.logger.info(f"Processed image from directory {resolved_path}: {file_in_dir}")
                            except Exception as e:
                                self.logger.error(f"Error processing image {file_in_dir} in directory {resolved_path}: {e}")
                        elif self.should_process_file(file_in_dir):
                            content = self._process_and_cache_text_file(file_in_dir)
                            if content:
                                processed_content_map[relative_key] = content
                        else:
                            self.logger.debug(f"Skipping file in directory (not image, or did not pass should_process_file): {file_in_dir}")
        return processed_content_map

    def _process_and_cache_text_file(self, file_path: Path) -> str:
        """Helper to process a single text file and cache its content if in a session."""
        if not self.should_process_file(file_path):
            return ""

        cache_file_name = self._sanitize_filename(str(file_path.resolve())) + ".txt"
        session_cache_file_path = self.files_dir / cache_file_name

        content = ""
        if self.is_session and session_cache_file_path.exists():
            self.logger.debug(f"Loading cached text file content for {file_path} from {session_cache_file_path}")
            with open(session_cache_file_path, "r", encoding='utf-8') as f:
                content = f.read()
        else:
            parsed_content = self.parse_file(file_path)
            if parsed_content:
                content = parsed_content
                if self.is_session:
                    try:
                        with open(session_cache_file_path, "w+", encoding='utf-8') as f:
                            f.write(content)
                        self.logger.debug(f"Cached text file content for {file_path} to {session_cache_file_path}")
                    except Exception as e:
                        self.logger.error(f"Failed to cache text file {file_path} to {session_cache_file_path}: {e}")
        return content

    def should_process_file(self, file_path: Path) -> bool:
        if not file_path.is_file():
            return False
            
        if file_path.suffix.lower() not in ALLOWED_EXTENSIONS:
            self.logger.debug(f"Skipping {file_path} - extension not in allowed list: {file_path.suffix.lower()}")
            return False

        try:
            file_path_str = str(file_path.resolve())
            for excluded_dir_part in EXCLUDED_DIRS:
                if f"{os.sep}{excluded_dir_part}{os.sep}" in file_path_str or \
                   file_path_str.startswith(excluded_dir_part + os.sep) or \
                   file_path.name == excluded_dir_part:
                    self.logger.debug(f"Skipping {file_path} - in excluded directory pattern {excluded_dir_part}")
                    return False
        except Exception as e:
            self.logger.error(f"Error checking excluded directories for {file_path}: {e}")
            return False

        return True

    def ocr(self, file_path: Path) -> str:
        """Fallback function to parse a file if the parser fails."""
        import pytesseract
        from pdf2image import convert_from_path
        
        try:
            images = convert_from_path(str(file_path))
            text = ""
            for image in images:
                text += pytesseract.image_to_string(image)

            return text if text else ""

        except Exception as e:
            self.logger.error(f"Error in fallback OCR parsing for {file_path}: {e}")
            return ""

    def parse_file(self, file_path: Path) -> str:
        """Parses a text-based file using Tika or direct read, with a fallback to OCR if Tika fails for PDFs. Handles token limits."""
        if file_path.suffix.lower() in IMAGE_EXTENSIONS:
            self.logger.warning(f"parse_file called on an image file: {file_path}. This should be handled by image processing logic.")
            return ""

        start_time = time.time()
        content = ""

        try:
            if file_path.suffix.lower() in {'.txt', '.md', '.py', '.js', '.jsx', '.ts', '.tsx', '.html', '.css', '.json', '.yaml', '.yml', '.sql', '.sh', '.bash', '.zsh', '.fish'}:
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
                self.logger.debug(f"Read text-based file directly: {file_path}")
            else:
                parsed_file = parser.from_file(str(file_path), requestOptions={'timeout': 180})
                content = parsed_file.get('content', "") if parsed_file else ""
                if not content and file_path.suffix.lower() == '.pdf':
                    self.logger.warning(f"Tika failed to extract content from PDF {file_path}. Attempting OCR.")
                    content = self.ocr(file_path)
        except Exception as e:
            self.logger.error(f"Failed parsing {file_path} with Tika/direct read. Attempting OCR if PDF. Error: {e}")
            if file_path.suffix.lower() == '.pdf':
                content = self.ocr(file_path) 
            else:
                content = ""

        time_to_parse = time.time() - start_time
        self.logger.debug(f"Parsing {file_path} took {time_to_parse:.2f} seconds. Initial char count: {len(content if content else '')}")
        
        if not content:
            self.logger.warning(f"No content extracted from {file_path} after parsing attempts.")
            return ""

        token_count = self.count_tokens(content)
        if token_count > MAX_TOKENS:
            self.logger.warning(f"File {file_path} has {token_count} tokens, which is more than the maximum of {MAX_TOKENS}. Skipping content.")
            return f"[File content truncated due to exceeding token limit: {file_path.name} ({token_count} tokens)]"

        return content

