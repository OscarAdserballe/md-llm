import pytest
from pathlib import Path
from src.session_manager import SessionManager
import shutil

@pytest.fixture
def temp_sessions_dir(tmp_path):
    return tmp_path / "sessions"

def test_create_session(temp_sessions_dir):
    manager = SessionManager(sessions_dir=temp_sessions_dir)
    session_name = "test_session"
    
    session_path = manager.create_session(session_name)
    
    assert session_path.exists()
    assert session_path.is_dir()
    md_file = session_path / f"{session_name}.md"
    assert md_file.exists()
    with open(md_file, "r") as f:
        content = f.read()
        assert "---" in content  # YAML metadata should be present

def test_list_sessions(temp_sessions_dir):
    manager = SessionManager(sessions_dir=temp_sessions_dir)
    session_names = ["session1", "session2", "session3"]
    for name in session_names:
        manager.create_session(name)
    
    listed_sessions = manager.list_sessions()
    assert set(listed_sessions) == set(session_names)

def test_delete_session(temp_sessions_dir):
    manager = SessionManager(sessions_dir=temp_sessions_dir)
    session_name = "session_to_delete"
    manager.create_session(session_name)
    
    assert session_name in manager.list_sessions()
    
    manager.delete_session(session_name)
    assert session_name not in manager.list_sessions()
    session_dir = temp_sessions_dir / session_name
    assert not session_dir.exists()
