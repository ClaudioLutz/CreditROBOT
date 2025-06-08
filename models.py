# models.py
from datetime import datetime, timezone
from sqlalchemy import Text, Float, String, DateTime, Integer, ForeignKey
from sqlalchemy.orm import relationship
from db import db

class Session(db.Model):
    __tablename__ = 'sessions'
    id = db.Column(Integer, primary_key=True)
    # This is the UUID string from the client
    session_id = db.Column(String(36), unique=True, nullable=False, index=True)
    created_at = db.Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # This field will store the running summary of the conversation
    conversation_summary = db.Column(Text, nullable=True, default="The conversation has just begun.")

    # Establish the one-to-many relationship
    conversations = relationship('Conversation', back_populates='session')

    def __repr__(self):
        return f"<Session {self.session_id}>"

class Conversation(db.Model):
    __tablename__ = 'conversations'
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign key to the sessions table
    session_uuid = db.Column(String(36), ForeignKey('sessions.session_id'), nullable=False)
    
    timestamp = db.Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    role = db.Column(String(16), nullable=False)
    language = db.Column(String(5), nullable=False)
    content = db.Column(Text, nullable=False)
    doc_path = db.Column(Text, nullable=True)
    similarity = db.Column(Float, nullable=True)

    # Establish the many-to-one relationship
    session = relationship('Session', back_populates='conversations')

    # Update __init__ to accept the session_uuid
    def __init__(self, session_uuid: str, role: str, language: str, content: str, doc_path: str | None = None, similarity: float | None = None):
        self.session_uuid = session_uuid
        self.role = role
        self.language = language
        self.content = content
        self.doc_path = doc_path
        self.similarity = similarity
        # id is auto-incrementing and handled by SQLAlchemy
        # timestamp uses the column default and is handled by SQLAlchemy

    def __repr__(self):
        return f"<Conversation {self.id} (Session: {self.session_uuid}) {self.role}: {self.content[:30]}>"

    # It's good practice to keep to_dict if it's used elsewhere,
    # or remove it if it's no longer needed.
    # For now, let's assume it might be used and update it.
    def to_dict(self):
        return {
            'id': self.id,
            'session_uuid': self.session_uuid, # Changed from session_id
            'timestamp': self.timestamp.isoformat(),
            'role': self.role,
            'language': self.language,
            'content': self.content,
            'doc_path': self.doc_path,
            'similarity': self.similarity
        }
