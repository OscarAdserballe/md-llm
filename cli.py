#!/usr/bin/env python
import click
from termcolor import colored
import sys

from config import DEFAULT_MODEL, DEFAULT_SYSTEM_PROMPT_NAME, SESSIONS_DIR, SUPPORTED_MODELS

from src.llm import LLM
from src.session_manager import SessionManager
from src.session import Session
from prompts.prompts import PROMPTS

from config_logger import logger

@click.group()
def cli():
    """LLM CLI tool"""
    pass

@cli.command()
@click.argument('query', required=True)
def query(query):
    """Send a query to the LLM"""
    logger.debug('initialising llm...')

    query = f"Query: {query}"

    if not sys.stdin.isatty():
        terminal_output = sys.stdin.read().strip()
        query += f"\nTerminal context:\n{terminal_output}"

    llm = LLM(llm_config = SUPPORTED_MODELS[DEFAULT_MODEL])
    llm.llm_config.system_prompt = PROMPTS['default']

    messages = [{"role": "user", "content": query}]

    response_stream = llm.query(messages=messages, stream=True)

    print(colored("Response: ", "cyan"), end="", flush=True)

    try:
        for chunk in response_stream:
            if chunk.choices[0].delta.content is not None:
                print(colored(chunk.choices[0].delta.content, "magenta"), end="", flush=True)
        print()  # Add final newline
       
    except KeyboardInterrupt:
        print("\nStreaming interrupted by user")
        return

@cli.command()
def ls():
    """Lists all available sessions"""
    logger.debug('received `llm ls` request')
    session_manager = SessionManager(SESSIONS_DIR)
    sessions = session_manager.list_sessions()
    if not sessions:
        print(colored("No sessions found.", "yellow"))
        return
    
    for session in sessions:
        print(colored(f"- {session}", "cyan"))

@cli.command()
@click.argument("session_name", type=str)
def create(session_name):
    """Create a new session"""
    session_manager = SessionManager(SESSIONS_DIR)

    session_manager.create_session(session_name)
    print(colored(f"Created new session: {session_name}", "cyan"))

@cli.command()
@click.argument("session_name", type=str)
def delete(session_name):
    """Delete a given session"""
    session_manager = SessionManager(SESSIONS_DIR)

    session_manager.delete_session(session_name)
    print(colored(f"Deleted session: {session_name}", "cyan"))

@cli.command()
@click.argument("session_name", type=str)
def run_session(session_name):
    """Runs specific session"""
    session = Session(session_name)
    # run_session returns True if the session was correctly updated
    if session.run_session():
        print(colored(f"Updated {session_name}", "cyan"))

@cli.command()
@click.argument("file_name", type=str)
def run_file(file_name):
    """Run a given file as a session"""
    session = Session(file_name, is_session=False)
    # run_session returns True if the session was correctly updated
    if session.run_session():
        print(colored(f"Updated {file_name}", "cyan"))

# adding from central_evaluator.py
from evaluations.central_evaluator import evaluate as evaluate_command
cli.add_command(evaluate_command, name="evaluate")

if __name__ == "__main__":
    cli()

