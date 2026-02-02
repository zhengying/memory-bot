"""
Session manager for handling multiple chat sessions
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from .models import Session
from .database import SessionDatabase
from core.llm import Message


class SessionManager:
    """Manage chat sessions and message history

    Supports both in-memory and persistent storage.
    """

    def __init__(self, db: Optional[SessionDatabase] = None, persist: bool = False):
        """Initialize session manager
        
        Args:
            db: Optional database for persistence (creates new if persist=True)
            persist: Whether to enable persistence (creates default db if True)
        """
        self.sessions: Dict[str, Session] = {}
        self.db: Optional[SessionDatabase] = None
        
        if db:
            self.db = db
            self._load_all_sessions()
        elif persist:
            self.db = SessionDatabase()
            self.db.connect()
            self.db.create_schema()
            self._load_all_sessions()

    def _generate_id(self) -> str:
        """Generate unique session ID

        Returns:
            Session ID
        """
        import uuid
        return str(uuid.uuid4())
    
    def _load_all_sessions(self):
        """Load all sessions from database into memory"""
        if not self.db:
            return
        
        session_list = self.db.list_sessions()
        for session_meta in session_list:
            session_id = session_meta["id"]
            session = self.db.load_session(session_id)
            if session:
                self.sessions[session_id] = session
    
    def _persist_session(self, session: Session):
        """Persist session to database if persistence is enabled
        
        Args:
            session: Session to persist
        """
        if self.db:
            self.db.save_session(session)
    
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
        
        # Persist if database is enabled
        if self.db:
            self.db.save_session(session)
        
        return session
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """Get session by ID

        Args:
            session_id: Session ID

        Returns:
            Session or None if not found
        """
        # First check memory
        if session_id in self.sessions:
            return self.sessions[session_id]
        
        # If persistence enabled, try to load from database
        if self.db:
            session = self.db.load_session(session_id)
            if session:
                self.sessions[session_id] = session
            return session
        
        return None
    
    def delete_session(self, session_id: str) -> bool:
        """Delete session

        Args:
            session_id: Session ID

        Returns:
            True if deleted, False if not found
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            
            # Also delete from database if persistence enabled
            if self.db:
                return self.db.delete_session(session_id)
            
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
            
            # Persist updated session
            if self.db:
                self.db.save_session(session)
            
            return session
        return None
    
    def persist_session(self, session_id: str) -> bool:
        """Manually persist a session to database
        
        Args:
            session_id: Session ID
            
        Returns:
            True if persisted, False if session not found or no database
        """
        if not self.db:
            return False
        
        session = self.get_session(session_id)
        if session:
            self.db.save_session(session)
            return True
        return False
    
    def clear_all(self):
        """Clear all sessions (memory and database)"""
        self.sessions.clear()
        
        if self.db:
            self.db.clear_all()
