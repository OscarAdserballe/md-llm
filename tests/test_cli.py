import pytest
from click.testing import CliRunner
from cli import cli
from unittest.mock import patch
from pathlib import Path

@pytest.fixture
def runner():
    return CliRunner()

def test_cli_query(runner):
    with patch('src.llm.LLM.query') as mock_query:
        mock_query.return_value = "Test response"
        result = runner.invoke(cli, ['query', 'Hello'])
        assert result.exit_code == 0
        assert "Test response" in result.output

def test_cli_ls_empty(runner):
    with patch('src.session_manager.SessionManager.list_sessions') as mock_list:
        mock_list.return_value = []
        result = runner.invoke(cli, ['ls'])
        assert result.exit_code == 0
        assert "No sessions found." in result.output

def test_cli_ls_with_sessions(runner):
    with patch('src.session_manager.SessionManager.list_sessions') as mock_list:
        mock_list.return_value = ["session1", "session2"]
        result = runner.invoke(cli, ['ls'])
        assert result.exit_code == 0
        assert "- session1" in result.output
        assert "- session2" in result.output

def test_cli_create_session(runner):
    with patch('src.session_manager.SessionManager.create_session') as mock_create:
        mock_create.return_value = Path("/fake/path/session")
        session_name = "new_session"
        result = runner.invoke(cli, ['create', session_name])
        assert result.exit_code == 0
        assert f"Created new session: {session_name}" in result.output

def test_cli_delete_session(runner):
    with patch('src.session_manager.SessionManager.delete_session') as mock_delete:
        session_name = "delete_session"
        result = runner.invoke(cli, ['delete', session_name])
        assert result.exit_code == 0
        assert f"Deleted session: {session_name}" in result.output

def test_cli_terminal_no_input(runner):
    with patch('src.llm.LLM.query') as mock_query:
        mock_query.return_value = "Terminal response"
        result = runner.invoke(cli, ['terminal', 'Explain the output'])
        assert result.exit_code == 0
        assert "Terminal response" in result.output

def test_cli_terminal_with_input(runner):
    with patch('src.llm.LLM.query') as mock_query:
        mock_query.return_value = "Terminal echoed response"
        input_text = "echo 'Hello, World!'"
        result = runner.invoke(cli, ['terminal', 'Explain this'], input=input_text)
        assert result.exit_code == 0
        assert "Terminal echoed response" in result.output
