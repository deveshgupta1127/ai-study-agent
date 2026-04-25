import uuid
from datetime import datetime

from sqlalchemy import Column, String, Text, Integer, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.database import Base


# --- Progress Model ---
class Progress(Base):
    __tablename__ = "progress"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    topic_id = Column(UUID(as_uuid=True), ForeignKey("topics.id"), nullable=False)

    mastery_score = Column(Float, default=0.0)  # 0.0 → 1.0

    questions_attempted = Column(Integer, default=0)
    questions_correct = Column(Integer, default=0)

    last_studied = Column(DateTime, default=datetime.utcnow)

    # --- Relationships ---
    user = relationship("User", back_populates="progress_records")


# --- ChatSession Model ---
class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=True)

    started_at = Column(DateTime, default=datetime.utcnow)

    # --- Relationships ---
    messages = relationship("Message", back_populates="session", cascade="all, delete")


# --- Message Model ---
class Message(Base):
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id"), nullable=False)

    role = Column(String(20), nullable=False)  # user | assistant
    content = Column(Text, nullable=False)

    sent_at = Column(DateTime, default=datetime.utcnow)

    # --- Relationships ---
    session = relationship("ChatSession", back_populates="messages")