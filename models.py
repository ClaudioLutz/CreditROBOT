# models.py
from datetime import datetime, timezone # Ensure timezone awareness
from sqlalchemy import Text, Float, String, DateTime, Integer
from db import db

class Conversation(db.Model):
    __tablename__ = 'conversations'

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(String(36), nullable=False, index=True)
    timestamp = db.Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    role = db.Column(String(16), nullable=False)
    language = db.Column(String(5), nullable=False)
    content = db.Column(Text, nullable=False)
    doc_path = db.Column(Text, nullable=True) # Column allows None
    similarity = db.Column(Float, nullable=True) # Column allows None

    def __init__(self, session_id: str, role: str, language: str, content: str, doc_path: str | None = None, similarity: float | None = None):
        self.session_id = session_id
        self.role = role
        self.language = language
        self.content = content
        self.doc_path = doc_path
        self.similarity = similarity
        # id is auto-incrementing and handled by SQLAlchemy
        # timestamp uses the column default and is handled by SQLAlchemy

    def __repr__(self):
        return f"<Conversation {self.id} (Session: {self.session_id}) {self.role}: {self.content[:30]}>"
