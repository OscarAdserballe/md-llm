#!/usr/bin/env python
import click
from termcolor import colored
import sys
import base64
from pathlib import Path
import os

from config import DEFAULT_MODEL, DEFAULT_SYSTEM_PROMPT_NAME, SUPPORTED_MODELS, PROMPTS, DEFAULT_PAPERS_OUTPUT_DIR
from src.llm import LLM

# Default output directory for paper summaries

def get_image_message(image_path: str):
    # print(colored(f"Processing image: {image_path}", "cyan"))
    with open(image_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode("utf-8")
    return {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{base64_image}",
                # "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg",
                },
            }

def get_file_message(file_path: str):
    # print(colored(f"Processing file: {file_path}", "cyan"))
    with open(file_path, 'r') as f:
        file_content = f.read()
    return {"type": "text", "text": f"\nFile Content:\n\n {file_content}"}

def get_terminal_message():
    # print(colored(f"Processing piped input", "cyan"))
    terminal_output = sys.stdin.read().strip()
    return {"type": "text", "text": f"\nTerminal context:\n{terminal_output}"}

### CLI ######

@click.group(invoke_without_command=True)
@click.pass_context
@click.argument('query', required=False)
@click.option('-p', '--prompt', type=click.Choice(list(PROMPTS.keys())), default=DEFAULT_SYSTEM_PROMPT_NAME, help='Select system prompt')
@click.option('-m', '--model', type=click.Choice(list(SUPPORTED_MODELS.keys())), default=DEFAULT_MODEL, help='Select LLM model')
@click.option('-t', '--temperature', type=float, default=0.5, help='Set the temperature for response creativity')
@click.option('-v', '--vision', type=click.Path(exists=True), help='Path to image for vision query')
@click.option('-f', '--file', type=click.Path(exists=True), help='Path to file to process')
@click.option('--pdf', is_flag=True, help='Process file as a PDF research paper and generate summary')
def main_cli(ctx, query, prompt, model, temperature, vision, file, pdf):
    """LLM CLI tool - running without subcommand acts as basic query"""
    if ctx.invoked_subcommand is None:
        # PDF paper processing mode
        if pdf and file:
            if not file.lower().endswith('.pdf'):
                print(colored("Error: File must be a PDF when using --pdf flag", "red"))
                return
                
            # Use the claude model for PDF processing if not otherwise specified
            if model == DEFAULT_MODEL and SUPPORTED_MODELS.get("claude"):
                model = "claude"
                print(colored(f"Using Claude model for PDF processing", "cyan"))
            
            # Note: Now all models support PDF processing using Tika

            output_path = DEFAULT_PAPERS_OUTPUT_DIR
                
            # Initialize LLM
            llm_config = SUPPORTED_MODELS[model]
            llm_config.temperature = temperature
            llm = LLM(llm_config=llm_config)
            
            # Process the PDF
            file_path = Path(file).resolve()
            print(colored(f"Processing PDF paper with {model} using Tika: {file_path}", "cyan"))
            summary = llm.process_pdf(file_path, PROMPTS['paper_summary'])

            out_filename = f"summary_{file_path.stem}.md"
            out_path = output_path / f"{model}_{out_filename}"
            
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(summary)
                
            print(colored(f"Summary written to {out_path}", "green"))
            
            return
            
        # Regular query mode
        elif query:
            ##### Initialising LLM with config specified ##########
            llm_config = SUPPORTED_MODELS[model]
            if prompt: llm_config.system_prompt = PROMPTS[prompt]
            if temperature: llm_config.temperature = temperature
            llm = LLM(llm_config=llm_config)

            ###### Loading in messages ######################
            llm_content = []
           
            # loading in file contents
            if file:
                llm_content.append(get_file_message(file)) 

            # loading in piped input
            if not sys.stdin.isatty():
                llm_content.append(get_terminal_message())       

            llm_content.append({"type": "text", "text": f"\nQuery\n: {query}"})

            # loading in image contents
            if vision:
                llm_content.append(get_image_message(vision)) 

            messages = [{"role": "user", "content": llm_content}]

            #### Streaming the output based on context string and model constructed ######
            # special case if structured output - cannot stream
            if llm.llm_config.response_format or vision:
                response = llm.query(messages=messages)
                print(response)
                return

            else:
                response_stream = llm.query(messages=messages, stream=True)

                try:
                    for chunk in response_stream:
                        if hasattr(chunk, 'choices') and hasattr(chunk.choices[0], 'delta'):
                            if chunk.choices[0].delta.content is not None:
                                print(colored(chunk.choices[0].delta.content, "magenta"), end="", flush=True)
                    print()  # Final newline

                except KeyboardInterrupt:
                    print("\nStreaming interrupted by user")
                    return
                except Exception as e:
                    print(colored(f"\nError during streaming: {e}", "red"))
                    return

        # falling back on this in case of user input error
        else:
            print(colored("Usage: `llm <args> <query>` or `llm --pdf -f <pdf_file>`", "red"))

@main_cli.command()
def supported_models():
    """List all supported LLM models"""
    print(colored("Supported Models:", "cyan", attrs=["bold"]))
    for model, config in SUPPORTED_MODELS.items():
        provider = config.provider
        supports_pdf = "✓" if provider == "anthropic" else "✗"
        print(colored(f"- {model} ({provider}, PDF: {supports_pdf})", "green"))

if __name__ == "__main__":
    main_cli()
