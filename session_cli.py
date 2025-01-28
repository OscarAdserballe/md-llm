import click
from termcolor import colored

from config import SESSIONS_DIR
from src.session_manager import SessionManager
from src.session import Session
from config_logger import logger

@click.group()
def session_cli():
    """Session management commands"""
    pass

@session_cli.command()
@click.argument("session_name", type=str)
def create(session_name):
    """Create a new session"""
    session_manager = SessionManager(SESSIONS_DIR)
    session_manager.create_session(session_name)
    print(colored(f"Created new session: {session_name}", "cyan"))

@session_cli.command()
def ls():
    """List all available sessions"""
    session_manager = SessionManager(SESSIONS_DIR)
    sessions = session_manager.list_sessions()
    if not sessions:
        print(colored("No sessions found.", "yellow"))
        return
    
    print(colored("Available Sessions:", "cyan", attrs=["bold"]))
    for session in sessions:
        print(colored(f"- {session}", "green"))

@session_cli.command()
@click.argument("session_name", type=str)
def delete(session_name):
    """Delete a specific session"""
    session_manager = SessionManager(SESSIONS_DIR)
    session_manager.delete_session(session_name)
    print(colored(f"Deleted session: {session_name}", "cyan"))

@session_cli.command()
@click.argument("session_name", type=str)
def run_session(session_name):
    """Run a specific session"""
    session = Session(session_name)
    if session.run_session():
        print(colored(f"Updated session: {session_name}", "cyan"))
    else:
        print(colored(f"Failed to update session: {session_name}", "red"))

@session_cli.command()
@click.argument("file_name", type=str)
def run_file(file_name):
    """Run a file as a session"""
    session = Session(file_name, is_session=False)
    if session.run_session():
        print(colored(f"Updated file as session: {file_name}", "cyan"))
    else:
        print(colored(f"Failed to update file as session: {file_name}", "red"))

if __name__ == "__main__":
    session_cli()
