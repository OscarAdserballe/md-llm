#!/usr/bin/env python
import click
from termcolor import colored
import sys

from config import DEFAULT_MODEL, DEFAULT_SYSTEM_PROMPT_NAME, SESSIONS_DIR, SUPPORTED_MODELS

from src.llm import LLM
from src.session_manager import SessionManager
from src.session import Session

from config_logger import logger

@click.group()
def cli():
    pass

@cli.command()
@click.argument("query", type=str)
def query(query):
    """Basic query"""
    logger.debug('initialisign llm...')
    llm = LLM(llm_config = SUPPORTED_MODELS[DEFAULT_MODEL])

    messages = [{"role": "user", "content": f"{query}. Try to be concise and clear in your answer."}]
    
    response = llm.query(messages=messages) 

    logger.debug(f'Got a response! {response}')
    print(colored(response, "magenta"))

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

@cli.command()
@click.argument("query", type=str)
def terminal(query):
    """
    Query with terminal output as context. E.g. `echo "Hello, world" | llm terminal "What was the terminal context provided?"` Using 2>&1 at the end of the command will also capture stderr.
    llm run-session test_session 2>&1 | llm terminal "can you explain this error"
    """

    # Get terminal output either from pipe or recent history
    terminal_output = ""
    if not sys.stdin.isatty():
        terminal_output = sys.stdin.read().strip()
    full_query = f"Terminal context:\n{terminal_output}\n\nQuery: {query}"
    
    llm = LLM(llm_config=SUPPORTED_MODELS[DEFAULT_MODEL])
    logger.debug(f'LLM initialised with query {full_query}')
    
    messages = [{"role": "user", "content": full_query}]
    response = llm.query(messages=messages)
    print(colored(response, "magenta"))

# adding from central_evaluator.py
from evaluations.central_evaluator import evaluate as evaluate_command
cli.add_command(evaluate_command, name="evaluate")

if __name__ == "__main__":
    cli()

