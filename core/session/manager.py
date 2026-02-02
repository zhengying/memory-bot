"""
Session manager for handling multiple chat sessions
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from .models import Session
from core.llm import Message


class SessionManager:
    """Manage chat sessions and message history

    Stores sessions in memory (can be extended to use SQLite).
    """

    def __init__(self):
        """Initialize session manager"""
        self.sessions: Dict[str, Session] = {}

    def create_session(
        self,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Session:
        """Create a new session

        Args:
            session_id: Optional session ID (auto-generated if None)
            metadata: Optional metadata

        Returns:
            New session
        """
        if session_id is None:
            session_id = self._generate_id()

        session = Session(
            id=session_id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            metadata=metadata or {}
        )

        self.sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        """Get session by ID

        Args:
            session_id: Session ID

        Returns:
            Session or None if not found
        """
        return self.sessions.get(session_id)

    def delete_session(self, session_id: str) -> bool:
        """Delete session

        Args:
            session_id: Session ID

        Returns:
            True if deleted, False if not found
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False

    def list_sessions(self) -> List[Session]:
        """List all sessions

        Returns:
            List of sessions
        """
        return list(self.sessions.values())

    def add_message(self, session_id: str, message: Message) -> Optional[Session]:
        """Add message to session

        Args:
            session_id: Session ID
            message: Message to add

        Returns:
            Updated session or None if not found
        """
        session = self.get_session(session_id)
        if session:
            session.add_message(message)
            return session
        return None

    def _generate_id(self) -> str:
        """Generate unique session ID

        Returns:
            Session ID
        """
        import uuid
        return str(uuid.uuid4())
