"""
Session management for the web UI.

This module handles creating, storing, and managing user sessions
with their associated data and retention policies.
"""

import json
import secrets
from datetime import datetime, timedelta
from pathlib import Path

from ..core.models import SessionConfig, TextSource


class SessionManager:
    """
    Manage web UI sessions.

    This class handles session creation, persistence, and cleanup
    based on retention policies.

    Attributes
    ----------
    data_dir : Path
        Directory for storing session data
    sessions : Dict[str, SessionConfig]
        In-memory cache of sessions
    """

    def __init__(self, data_dir: str = "./data/sessions"):
        """
        Initialize the session manager.

        Parameters
        ----------
        data_dir : str, optional
            Directory for session data (default: "./data/sessions")
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.sessions: dict[str, SessionConfig] = {}
        self._load_sessions()

    def _generate_session_id(self) -> str:
        """
        Generate a unique session ID.

        Returns
        -------
        str
            Random session ID
        """
        return secrets.token_urlsafe(32)

    def _session_path(self, session_id: str) -> Path:
        """
        Get the file path for a session.

        Parameters
        ----------
        session_id : str
            Session ID

        Returns
        -------
        Path
            Path to session file
        """
        return self.data_dir / f"{session_id}.json"

    def _load_sessions(self):
        """Load all sessions from disk."""
        for session_file in self.data_dir.glob("*.json"):
            try:
                with open(session_file, encoding="utf-8") as f:
                    data = json.load(f)

                # Parse dates
                data["created_at"] = datetime.fromisoformat(data["created_at"])
                data["last_accessed"] = datetime.fromisoformat(data["last_accessed"])

                # Parse text sources
                data["text_sources"] = [
                    TextSource(**src) for src in data["text_sources"]
                ]

                session = SessionConfig(**data)
                self.sessions[session.session_id] = session
            except Exception as e:
                print(f"Error loading session {session_file}: {e}")

    def create_session(
        self,
        text_sources: list[TextSource],
        selected_resources: list[str],
        retention_days: int | None = 180,
    ) -> SessionConfig:
        """
        Create a new session.

        Parameters
        ----------
        text_sources : List[TextSource]
            Text sources for this session
        selected_resources : List[str]
            IDs of selected resources
        retention_days : Optional[int], optional
            Days to retain session (default: 180, None for indefinite)

        Returns
        -------
        SessionConfig
            The created session
        """
        session_id = self._generate_session_id()

        session = SessionConfig(
            session_id=session_id,
            text_sources=text_sources,
            selected_resources=selected_resources,
            retention_days=retention_days,
        )

        self.sessions[session_id] = session
        self._save_session(session)

        return session

    def get_session(self, session_id: str) -> SessionConfig | None:
        """
        Get a session by ID.

        Parameters
        ----------
        session_id : str
            Session ID

        Returns
        -------
        Optional[SessionConfig]
            Session if found, None otherwise
        """
        session = self.sessions.get(session_id)

        if session:
            # Update last accessed time
            session.last_accessed = datetime.now()
            self._save_session(session)

        return session

    def _save_session(self, session: SessionConfig):
        """
        Save a session to disk.

        Parameters
        ----------
        session : SessionConfig
            Session to save
        """
        session_path = self._session_path(session.session_id)

        # Convert to dict for JSON serialization
        data = {
            "session_id": session.session_id,
            "text_sources": [
                {
                    "id": src.id,
                    "name": src.name,
                    "content": src.content,
                    "source_type": src.source_type,
                    "original_path": src.original_path,
                }
                for src in session.text_sources
            ],
            "selected_resources": session.selected_resources,
            "retention_days": session.retention_days,
            "created_at": session.created_at.isoformat(),
            "last_accessed": session.last_accessed.isoformat(),
        }

        with open(session_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.

        Parameters
        ----------
        session_id : str
            Session ID to delete

        Returns
        -------
        bool
            True if deleted, False if not found
        """
        if session_id not in self.sessions:
            return False

        # Remove from memory
        del self.sessions[session_id]

        # Remove from disk
        session_path = self._session_path(session_id)
        if session_path.exists():
            session_path.unlink()

        return True

    def cleanup_expired_sessions(self):
        """
        Clean up expired sessions based on retention policy.

        This should be called periodically (e.g., daily) to remove
        sessions that have exceeded their retention period.
        """
        now = datetime.now()
        sessions_to_delete = []

        for session_id, session in self.sessions.items():
            # Skip sessions with indefinite retention
            if session.retention_days is None:
                continue

            # Check if expired
            expiry_date = session.last_accessed + timedelta(days=session.retention_days)
            if now > expiry_date:
                sessions_to_delete.append(session_id)

        # Delete expired sessions
        for session_id in sessions_to_delete:
            self.delete_session(session_id)

    def update_session_sources(
        self, session_id: str, text_sources: list[TextSource]
    ) -> bool:
        """
        Update text sources for a session.

        Parameters
        ----------
        session_id : str
            Session ID
        text_sources : List[TextSource]
            New text sources

        Returns
        -------
        bool
            True if updated, False if session not found
        """
        session = self.sessions.get(session_id)
        if not session:
            return False

        session.text_sources = text_sources
        session.last_accessed = datetime.now()
        self._save_session(session)

        return True

    def update_session_resources(
        self, session_id: str, selected_resources: list[str]
    ) -> bool:
        """
        Update selected resources for a session.

        Parameters
        ----------
        session_id : str
            Session ID
        selected_resources : List[str]
            New selected resource IDs

        Returns
        -------
        bool
            True if updated, False if session not found
        """
        session = self.sessions.get(session_id)
        if not session:
            return False

        session.selected_resources = selected_resources
        session.last_accessed = datetime.now()
        self._save_session(session)

        return True


# Global session manager instance
_global_session_manager: SessionManager | None = None


def get_session_manager(data_dir: str = "./data/sessions") -> SessionManager:
    """
    Get or create the global session manager instance.

    Parameters
    ----------
    data_dir : str, optional
        Directory for session data (default: "./data/sessions")

    Returns
    -------
    SessionManager
        The global session manager instance
    """
    global _global_session_manager
    if _global_session_manager is None:
        _global_session_manager = SessionManager(data_dir)
    return _global_session_manager
