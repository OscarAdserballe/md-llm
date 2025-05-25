from pathlib import Path
import os
from typing import Optional, List, Dict
from termcolor import colored
import sys
import base64
from config_logger import logger
from config import MAX_TOKENS
import tiktoken

class FileProcessor:
    """
    A class to handle file processing operations, decoupled from the CLI code.
    This handles various file types including PDFs and directories.
    """
    
    def __init__(self):
        self.logger = logger
        
    def process_image(self, image_path: str) -> Dict:
        """Process an image file and return it in the format expected by LLMs."""
        self.logger.debug(f"Processing image: {image_path}")
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode("utf-8")
        
        return {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{base64_image}"
            }
        }
        
    def process_text_file(self, file_path: str) -> Dict:
        """Process a text file and return its contents."""
        self.logger.debug(f"Processing text file: {file_path}")
        try:
            with open(file_path, 'r') as f:
                file_content = f.read()
                
            # Check token count - skip if file is too large
            token_count = self.count_tokens(file_content)
            if token_count > MAX_TOKENS:
                self.logger.warning(f"File {file_path} has {token_count} tokens, which exceeds the limit of {MAX_TOKENS}. Skipping.")
                return {"type": "text", "text": f"\nFile Content:\n\n[File too large ({token_count} tokens) - exceeds limit of {MAX_TOKENS} tokens]"}
                
            return {"type": "text", "text": f"\nFile Content:\n\n {file_content}"}
        except Exception as e:
            self.logger.error(f"Error reading file {file_path}: {e}")
            return {"type": "text", "text": f"[Error reading file: {e}]"}
            
    def process_terminal_input(self) -> Dict:
        """Process input piped from the terminal."""
        self.logger.debug("Processing piped terminal input")
        terminal_output = sys.stdin.read().strip()
        
        # Check token count - truncate if too large
        token_count = self.count_tokens(terminal_output)
        if token_count > MAX_TOKENS:
            self.logger.warning(f"Terminal input has {token_count} tokens, which exceeds the limit of {MAX_TOKENS}. Truncating.")
            # Just truncate to the token limit approximately
            encoding = tiktoken.get_encoding("cl100k_base")
            tokens = encoding.encode(terminal_output)
            truncated_tokens = tokens[:MAX_TOKENS]
            terminal_output = encoding.decode(truncated_tokens)
            terminal_output += "\n[Input truncated due to size limit]"
            
        return {"type": "text", "text": f"\nTerminal context:\n{terminal_output}"}
    
    def extract_pdf_text(self, pdf_path: Path) -> Optional[str]:
        """Extract text from a PDF file using Tika parser."""
        try:
            from tika import parser
            parsed_file = parser.from_file(str(pdf_path), requestOptions={'timeout': 180})
            content = parsed_file.get('content', '')
            
            # If Tika fails to extract content, try OCR
            if not content:
                self.logger.warning(f"Tika failed to extract text from {pdf_path}. Trying OCR.")
                content = self._ocr_pdf(pdf_path)
                
            # Check token count - skip if too large
            if content:
                token_count = self.count_tokens(content)
                if token_count > MAX_TOKENS:
                    self.logger.warning(f"PDF {pdf_path} has {token_count} tokens, which exceeds the limit of {MAX_TOKENS}. Skipping.")
                    return f"[PDF too large ({token_count} tokens) - exceeds limit of {MAX_TOKENS} tokens]"
                    
            return content
        except Exception as e:
            self.logger.error(f"Error extracting text from PDF {pdf_path}: {e}")
            return None
            
    def _ocr_pdf(self, pdf_path: Path) -> str:
        """OCR a PDF file to extract text."""
        try:
            import pytesseract
            from pdf2image import convert_from_path
            
            images = convert_from_path(pdf_path)
            text = ""
            for image in images:
                text += pytesseract.image_to_string(image)
                
            return text
        except Exception as e:
            self.logger.error(f"Error OCRing PDF {pdf_path}: {e}")
            return ""
            
    def get_files_from_path(self, path: str) -> List[Path]:
        """
        Get a list of files from a path, which can be a single file or a directory.
        If a directory, returns all files in that directory (recursive).
        """
        path_obj = Path(path)
        file_paths = []
        
        if path_obj.is_file():
            file_paths.append(path_obj)
        elif path_obj.is_dir():
            self.logger.info(f"Processing directory: {path_obj}")
            # Get all files recursively
            for file_path in path_obj.rglob('*'):
                if file_path.is_file() and not file_path.name.startswith('.'):
                    file_paths.append(file_path)
            
            self.logger.info(f"Found {len(file_paths)} files in directory {path_obj}")
        
        return file_paths
        
    def count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken."""
        try:
            encoding = tiktoken.get_encoding("cl100k_base")  # GPT-4 encoding
            return len(encoding.encode(text))
        except Exception as e:
            self.logger.error(f"Error counting tokens: {e}")
            return 0