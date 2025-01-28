#!/usr/bin/env python
import click
from termcolor import colored
import sys

from config import DEFAULT_MODEL, DEFAULT_SYSTEM_PROMPT_NAME, SUPPORTED_MODELS, PROMPTS
from src.llm import LLM
from config_logger import logger
from src.session_manager import SessionManager
from src.session import Session  # If needed

@click.group(invoke_without_command=True)
@click.pass_context
@click.argument('query', required=False)
@click.option('-p', '--prompt', type=click.Choice(list(PROMPTS.keys())), default=DEFAULT_SYSTEM_PROMPT_NAME, help='Select system prompt')
@click.option('-m', '--model', type=click.Choice(list(SUPPORTED_MODELS.keys())), default=DEFAULT_MODEL, help='Select LLM model')
@click.option('-t', '--temperature', type=float, default=0.5, help='Set the temperature for response creativity')
@click.option('-o', '--object', is_flag=True, help='Enable structured object parsing')
@click.option('-v', '--vision', type=click.Path(exists=True), help='Path to image for vision query')
@click.option('-f', '--file', type=click.Path(exists=True), help='Path to file to process')
def main_cli(ctx, query, prompt, model, temperature, object, vision, file):
    """LLM CLI tool - running without subcommand acts as basic query"""
    if ctx.invoked_subcommand is None and query:
        logger.debug('Initializing LLM with specified configurations...')
        
        llm_config = SUPPORTED_MODELS[model]
        llm_config.system_prompt = PROMPTS[prompt]
        llm_config.temperature = temperature
        llm = LLM(llm_config=llm_config)
        
        if vision:
            response = llm.vision_query(vision)
            if response:
                print(colored("Vision Response:", "cyan"))
                print(colored(response, "magenta"))
            else:
                print(colored("Failed to process vision query.", "red"))
            return
        
        if file:
            print(colored(f"Processing file: {file}", "cyan"))
            with open(file, 'r') as f:
                file_content = f.read()
            messages = [{"role": "user", "content": file_content}]
        else:
            messages = [{"role": "user", "content": query}]
        
        if not sys.stdin.isatty():
            terminal_output = sys.stdin.read().strip()
            messages.append({"role": "user", "content": f"\nTerminal context:\n{terminal_output}"})
        
        if object:
            from pydantic import BaseModel

            class CalendarEvent(BaseModel):
                name: str
                date: str
                participants: list[str]
            
            structured_response = llm.structured_parse(
                model_name="gpt-4o-2024-08-06",
                messages=messages,
                response_format=CalendarEvent
            )
            if structured_response:
                print(colored("Structured Response:", "cyan"))
                print(structured_response.json(indent=2))
            else:
                print(colored("Failed to parse structured response.", "red"))
            return
    
    response_stream = llm.query(messages=messages, stream=True)

    print(colored("Response:", "cyan"), end="", flush=True)

    try:
        for chunk in response_stream:
            if chunk.choices[0].delta.content is not None:
                print(colored(chunk.choices[0].delta.content, "magenta"), end="", flush=True)
        print()  # Final newline
    except KeyboardInterrupt:
        print("\nStreaming interrupted by user")
        return

@main_cli.command()
def supported_models():
    """List all supported LLM models"""
    print(colored("Supported Models:", "cyan", attrs=["bold"]))
    for model in SUPPORTED_MODELS.keys():
        print(colored(f"- {model}", "green"))

if __name__ == "__main__":
    main_cli()
