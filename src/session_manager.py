from pathlib import Path
from datetime import datetime
import yaml
import shutil
from typing import List, Dict, Optional, Tuple

from config import DEFAULT_MODEL, SESSIONS_DIR

class SessionManager:
    def __init__(self, sessions_dir: Path=Path(SESSIONS_DIR)):
        """Initialize the SessionManager with the sessions directory.
        
        Args:
            sessions_dir (Path): Path to the directory containing all sessions
        """
        self.sessions_dir = Path(sessions_dir)
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

    def create_session(self, session_name: str) -> Path:
        session_dir = self.sessions_dir / session_name
        session_dir.mkdir(parents=True, exist_ok=True)
        
        # Create session markdown file
        session_md = session_dir / f"{session_name}.md"
        
        default_metadata = {
            "session_name": session_name,
            "created_at": datetime.now().isoformat(),
            "llm_config": DEFAULT_MODEL,
            "files": [],
            "search": [],
            "current_tokens": 0,
        }
                  
        # Write metadata and create initial markdown file
        with session_md.open('w') as f:
            f.write('---\n')
            yaml.dump(default_metadata, f, default_flow_style=False)
            f.write('---\n\n')
        return session_dir
            
 
    def list_sessions(self) -> List[str]:
        """Listing the existing sessions based on existence of .md file"""
        return [d.name for d in self.sessions_dir.iterdir() 
                if d.is_dir() and (d / f"{d.name}.md").exists()]

    def delete_session(self, session_name: str):
        """Delete a session and all its associated files.
        
        Args:
            session_name (str): Name of the session to delete
        """
        session_dir = self.sessions_dir / session_name
        if session_dir.exists():
            shutil.rmtree(session_dir)
