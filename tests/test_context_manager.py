import pytest
from pathlib import Path
from src.context_manager import ContextManager
from unittest.mock import patch, mock_open

@pytest.fixture
def temp_context_dir(tmp_path):
    context_dir = tmp_path / "context"
    context_dir.mkdir(parents=True, exist_ok=True)
    (context_dir / "files").mkdir(exist_ok=True)
    return context_dir

def test_context_manager_load_files(temp_context_dir):
    test_file = temp_context_dir / "test_file.txt"
    test_file.write_text("Sample content")
    
    with patch('src.context_manager.parser.from_file') as mock_parser:
        mock_parser.return_value = {'content': 'Parsed file content'}
        
        context = ContextManager(
            location=temp_context_dir,
            files=["test_file.txt"],
            search=[],
            query="Test query",
            is_session=False
        )
        
        print(context.files_content)
        assert context.files_content.get("test_file.txt") == "Parsed file content"

def test_context_manager_load_search(temp_context_dir):
    with patch('src.context_manager.LLM') as mock_llm:
        mock_llm_instance = mock_llm.return_value
        mock_llm_instance.query.return_value = "Search result for Python testing"
        
        context = ContextManager(
            location=temp_context_dir,
            files=[],
            search=["Python testing"],
            query="Explain Python testing",
            is_session=False
        )
        
        search_content = context.load_search()
        assert search_content["Python testing"] == "Search result for Python testing"
