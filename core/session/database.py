"""
SQLite database for session persistence
"""
import sqlite3
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from core.session.models import Session
from core.llm import Message


class SessionDatabase:
    """SQLite database for session persistence
    
    Stores sessions and messages for recovery after restart.
    """
    
    def __init__(self, db_path: str = ".sessions.db"):
        """Initialize session database
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None
    
    def connect(self):
        """Connect to database"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def create_schema(self):
        """Create database schema"""
        if not self.conn:
            raise RuntimeError("Not connected")
        
        cursor = self.conn.cursor()
        
        # Sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                metadata TEXT
            )
        """)
        
        # Messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
            )
        """)
        
        # Index for faster session lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_session 
            ON messages(session_id)
        """)
        
        self.conn.commit()
    
    def save_session(self, session: Session):
        """Save or update session
        
        Args:
            session: Session to save
        """
        if not self.conn:
            raise RuntimeError("Not connected")
        
        cursor = self.conn.cursor()
        
        # Insert or replace session
        cursor.execute("""
            INSERT OR REPLACE INTO sessions (id, created_at, updated_at, metadata)
            VALUES (?, ?, ?, ?)
        """, (
            session.id,
            session.created_at.isoformat() if session.created_at else datetime.now(timezone.utc).isoformat(),
            session.updated_at.isoformat() if session.updated_at else datetime.now(timezone.utc).isoformat(),
            json.dumps(session.metadata)
        ))
        
        # Clear old messages for this session
        cursor.execute("DELETE FROM messages WHERE session_id = ?", (session.id,))
        
        # Insert all messages
        for msg in session.messages:
            cursor.execute("""
                INSERT INTO messages (session_id, role, content, metadata)
                VALUES (?, ?, ?, ?)
            """, (
                session.id,
                msg.role,
                msg.content,
                json.dumps(msg.metadata)
            ))
        
        self.conn.commit()
    
    def load_session(self, session_id: str) -> Optional[Session]:
        """Load session by ID
        
        Args:
            session_id: Session ID
            
        Returns:
            Session or None if not found
        """
        if not self.conn:
            raise RuntimeError("Not connected")
        
        cursor = self.conn.cursor()
        
        # Load session
        cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        # Load messages
        cursor.execute("""
            SELECT * FROM messages 
            WHERE session_id = ? 
            ORDER BY created_at ASC
        """, (session_id,))
        
        messages = []
        for msg_row in cursor.fetchall():
            messages.append(Message(
                role=msg_row["role"],
                content=msg_row["content"],
                metadata=json.loads(msg_row["metadata"]) if msg_row["metadata"] else {}
            ))
        
        return Session(
            id=row["id"],
            messages=messages,
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            metadata=json.loads(row["metadata"]) if row["metadata"] else {}
        )
    
    def delete_session(self, session_id: str) -> bool:
        """Delete session
        
        Args:
            session_id: Session ID
            
        Returns:
            True if deleted, False if not found
        """
        if not self.conn:
            raise RuntimeError("Not connected")
        
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        self.conn.commit()
        
        return cursor.rowcount > 0
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all sessions (metadata only)
        
        Returns:
            List of session metadata
        """
        if not self.conn:
            raise RuntimeError("Not connected")
        
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM sessions ORDER BY updated_at DESC")
        
        sessions = []
        for row in cursor.fetchall():
            sessions.append({
                "id": row["id"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "metadata": json.loads(row["metadata"]) if row["metadata"] else {}
            })
        
        return sessions
    
    def clear_all(self):
        """Clear all sessions"""
        if not self.conn:
            raise RuntimeError("Not connected")
        
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM sessions")
        self.conn.commit()
    
    def count(self) -> int:
        """Count total sessions
        
        Returns:
            Number of sessions
        """
        if not self.conn:
            raise RuntimeError("Not connected")
        
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM sessions")
        return cursor.fetchone()["count"]
