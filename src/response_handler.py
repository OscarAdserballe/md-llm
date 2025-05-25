from pathlib import Path
import os
from termcolor import colored
from typing import Dict, Any, Optional, List, Union
from config import DEFAULT_PAPERS_OUTPUT_DIR
from src.vector_store import VectorStore

class ResponseHandler:
    """
    Handles formatting and output of LLM responses to various destinations.
    Supports multiple output types including terminal, file, and specialized formats like obsidian_papers.
    Also stores responses in vector database for future reference.
    """
    
    def __init__(self, model_name: str, force_overwrite: bool = False, store_in_db: bool = True):
        self.model_name = model_name
        self.force_overwrite = force_overwrite
        self.store_in_db = store_in_db
        self.vector_store = VectorStore() if store_in_db else None
    
    def handle_response(self, 
                       response: str, 
                       output_destination: Optional[str] = None,
                       input_file: Optional[Path] = None,
                       query: Optional[str] = None) -> None:
        """
        Handle the response from the LLM based on the output destination.
        
        Args:
            response: The response text from the LLM
            output_destination: Where to send the output (terminal, file, obsidian_papers)
            input_file: The input file that was processed (if any)
        """
        # Store the response in vector DB if enabled and we have a query
        if self.store_in_db and self.vector_store and query:
            query_type = "file_analysis" if input_file else "question"
            file_path = str(input_file) if input_file else None
            
            try:
                self.vector_store.add_interaction(
                    query=query,
                    response=response,
                    model_name=self.model_name,
                    query_type=query_type,
                    file_path=file_path
                )
            except Exception as e:
                print(colored(f"Warning: Could not store response in vector database: {e}", "yellow"))
        
        # Default to terminal if no destination specified
        if not output_destination:
            self.output_to_terminal(response)
            return
            
        # Handle different output destinations
        if output_destination == "obsidian_papers":
            self.output_to_obsidian_papers(response, input_file)
        elif output_destination == "file":
            self.output_to_file(response, input_file)
        else:
            # Assume output_destination is a directory path
            output_path = Path(output_destination)
            if output_path.is_dir():
                self.output_to_directory(response, output_path, input_file)
            else:
                print(colored(f"Warning: Output destination '{output_destination}' is not a valid directory. Outputting to terminal.", "yellow"))
                self.output_to_terminal(response)
    
    def output_to_terminal(self, response: str) -> None:
        """Output the response to the terminal"""
        print(colored(response, "magenta"))
    
    def output_to_file(self, response: str, input_file: Optional[Path] = None) -> None:
        """Output the response to a file in the current directory"""
        out_filename = f"llm_response_{self.model_name}.txt"
        if input_file:
            out_filename = f"{self.model_name}_{input_file.stem}.md"
        
        # Check if file already exists
        if Path(out_filename).exists() and not self.force_overwrite:
            print(colored(f"File {out_filename} already exists. Skipping.", "yellow"))
            return
            
        with open(out_filename, "w", encoding="utf-8") as f:
            f.write(response)
            
        print(colored(f"Response written to {out_filename}", "green"))
    
    def output_to_directory(self, response: str, directory: Path, input_file: Optional[Path] = None) -> None:
        """Output the response to a file in the specified directory"""
        directory.mkdir(exist_ok=True, parents=True)
        
        out_filename = f"llm_response_{self.model_name}.txt"
        if input_file:
            out_filename = f"{self.model_name}_{input_file.stem}.md"
            
        out_path = directory / out_filename
        
        # Check if file already exists
        if out_path.exists() and not self.force_overwrite:
            print(colored(f"File {out_path} already exists. Skipping.", "yellow"))
            return
            
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(response)
            
        print(colored(f"Response written to {out_path}", "green"))
    
    def output_to_obsidian_papers(self, response: str, input_file: Optional[Path] = None) -> None:
        """Output the response to the Obsidian papers directory"""
        output_path = DEFAULT_PAPERS_OUTPUT_DIR
        output_path.mkdir(exist_ok=True, parents=True)
        
        if input_file:
            out_filename = f"summary_{input_file.stem}.md"
        else:
            out_filename = f"note_{self.model_name}.md"
            
        out_path = output_path / f"{out_filename}"
        
        # Check if file already exists
        if out_path.exists() and not self.force_overwrite:
            print(colored(f"File {out_path} already exists. Skipping.", "yellow"))
            return
            
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(response)
            
        print(colored(f"Response written to {out_path}", "green"))
