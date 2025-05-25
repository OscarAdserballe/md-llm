#!/usr/bin/env python
import click
from termcolor import colored
import sys
from pathlib import Path
from time import sleep

from config import DEFAULT_MODEL, DEFAULT_SYSTEM_PROMPT_NAME, SUPPORTED_MODELS, PROMPTS
from src.llm import LLM
from src.response_handler import ResponseHandler
from src.file_processor import FileProcessor
from src.vector_store import VectorStore
from src.search_service import SearchService

### CLI ######

@click.group(invoke_without_command=True)
@click.pass_context
@click.argument('query', required=False)
@click.option('-p', '--prompt', type=click.Choice(list(PROMPTS.keys())), default=DEFAULT_SYSTEM_PROMPT_NAME, help='Select system prompt')
@click.option('-m', '--model', type=click.Choice(list(SUPPORTED_MODELS.keys())), default=DEFAULT_MODEL, help='Select LLM model')
@click.option('-t', '--temperature', type=float, default=0.5, help='Set the temperature for response creativity')
@click.option('-v', '--vision', type=click.Path(exists=True), help='Path to image for vision query')
@click.option('-f', '--file', type=click.Path(exists=True), help='Path to file or directory to process')
@click.option('-s', '--syllabus', type=click.Path(exists=True), help='Path to file or directory to process in addition to other files. No dirs supported')
@click.option('-o', '--output', type=str, help='Output destination (obsidian_papers, file, or directory path)')
@click.option('--force', is_flag=True, help='Force overwrite existing output files')
@click.option('--no-store', is_flag=True, help='Do not store this interaction in the vector database')
def main_cli(ctx, query, prompt, model, temperature, vision, file, output, force, no_store, syllabus):
    """LLM CLI tool - running without subcommand acts as basic query"""
    if ctx.invoked_subcommand is None:
        # Initialize services
        file_processor = FileProcessor()
        
        # Initialize LLM with config
        llm_config = SUPPORTED_MODELS[model]
        if prompt: 
            llm_config.system_prompt = PROMPTS[prompt]
        if temperature: 
            llm_config.temperature = temperature
        
        llm = LLM(llm_config=llm_config)
        # Note, disabling vector store for now
        response_handler = ResponseHandler(model, force_overwrite=force, store_in_db=False)
        
        # File or directory processing mode
        if file:

            # slighly ugly implementation for now; syllabus only processed if there's a file

            if syllabus:
                syllabus_file = file_processor.get_files_from_path(syllabus)


            files = file_processor.get_files_from_path(file)
            
            if not files:
                print(colored(f"No processable files found in {file}", "red"))
                return
                
            for file_path in files:
                print(colored(f"Processing file: {file_path}", "cyan"))
                
                if file_path.suffix.lower() == '.pdf':
                    summary = llm.process_pdf(file_path, PROMPTS.get(prompt, ""))
                    if summary:
                        response_handler.handle_response(summary, output, file_path)
                    
                    # to get around tight rate limits from e.g. Gemini pro 2.5
                    sleep(30)
                else:
                    # Regular file processing
                    try:
                        content = file_processor.process_text_file(str(file_path))
                        
                        # Check if the file was too large
                        if "[File too large" in content['text']:
                            print(colored(content['text'], "yellow"))
                            continue
                            
                        # Prepare query and get response
                        prompt_text = f"{content['text']}\n\n{PROMPTS.get(prompt, '')}"
                        messages = [{"role": "user", "content": prompt_text}]
                        response = llm.query(messages=messages)
                        response_handler.handle_response(response, output, file_path, query=prompt_text)
                    except Exception as e:
                        print(colored(f"Error processing file {file_path}: {e}", "red"))
            
            return
            
        # Regular query mode
        elif query:
            # Loading message content
            llm_content = []
           
            # Add terminal input if available
            if not sys.stdin.isatty():
                llm_content.append(file_processor.process_terminal_input())

            # Add the user's query
            llm_content.append({"type": "text", "text": f"\nQuery\n: {query}"})

            # Add image if specified
            if vision:
                llm_content.append(file_processor.process_image(vision))

            # Create the messages for the LLM
            messages = [{"role": "user", "content": llm_content}]

            # Process the query and get response
            try:
                # Special case for structured output or vision - cannot stream
                if llm.llm_config.response_format or vision:
                    response = llm.query(messages=messages)
                    response_handler.handle_response(response, output, query=query)
                    return
                
                # Handle provider-specific behavior
                if llm.llm_config.provider == "anthropic":
                    print(colored("Streaming not supported for Anthropic models", "red"))
                    response = llm.query(messages=messages)
                    response_handler.handle_response(response, output, query=query)
                else:
                    # For other providers (OpenAI/Gemini)
                    if output:
                        # If output destination specified, don't stream
                        response = llm.query(messages=messages)
                        response_handler.handle_response(response, output, query=query)
                    else:
                        # Stream to terminal
                        response_stream = llm.query(messages=messages, stream=True)
                        for chunk in response_stream:
                            if hasattr(chunk, 'choices') and hasattr(chunk.choices[0], 'delta'):
                                if chunk.choices[0].delta.content is not None:
                                    print(colored(chunk.choices[0].delta.content, "magenta"), end="", flush=True)
                        print()  # Final newline

            except KeyboardInterrupt:
                print("\nStreaming interrupted by user")
                return
            except Exception as e:
                print(colored(f"\nError during query: {e}", "red"))
                return
        
        # Usage information if no valid input provided
        else:
            print(colored("Usage: `llm <args> <query>` or `llm -f <file_or_directory> -o <output_destination>`", "red"))

@main_cli.command()
def supported_models():
    """List all supported LLM models"""
    print(colored("Supported Models:", "cyan", attrs=["bold"]))
    for model, config in SUPPORTED_MODELS.items():
        provider = config.provider
        print(colored(f"- {model} ({provider})", "green"))

@main_cli.command()
@click.argument('search_query')
@click.option('--limit', '-l', type=int, default=5, help='Maximum number of results to return')
@click.option('--detailed', '-d', is_flag=True, help='Show detailed results including full responses')
@click.option('--min-similarity', type=float, default=0.7, help='Minimum similarity score (0.0-1.0)')
def search(search_query, limit, detailed, min_similarity):
    """Search previous interactions for similar queries or content"""
    try:
        # Initialize search service
        search_service = SearchService()
        
        print(colored(f"Searching for: {search_query}", "cyan"))
        results = search_service.search(
            query=search_query,
            limit=limit,
            min_similarity=min_similarity
        )
        
        # Format and display results
        formatted_results = search_service.format_results(results, detailed=detailed)
        print(formatted_results)
        
    except Exception as e:
        print(colored(f"Error during search: {e}", "red"))
        if "ChromaDB" in str(e):
            print(colored("Tip: You may need to install chromadb with 'pip install chromadb'", "yellow"))

if __name__ == "__main__":
    main_cli()
