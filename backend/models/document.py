import uuid
from datetime import datetime

from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.database import Base


# --- Document ---
class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    group_id = Column(UUID(as_uuid=True), ForeignKey("study_groups.id"), nullable=True)

    filename = Column(String(255), nullable=False)
    file_type = Column(String(20), nullable=False)
    raw_text = Column(Text, nullable=True)

    status = Column(String(20), default="pending")

    uploaded_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="documents")
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete")
    topics = relationship("Topic", back_populates="document", cascade="all, delete")


# --- Chunk ---
class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)

    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)

    embedding_id = Column(String(100), nullable=True)

    # Relationship
    document = relationship("Document", back_populates="chunks")


# --- Topic ---
class Topic(Base):
    __tablename__ = "topics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)

    title = Column(String(255), nullable=False)
    summary = Column(Text, nullable=True)

    difficulty_level = Column(Integer, nullable=True)

    # Relationship
    document = relationship("Document", back_populates="topics")