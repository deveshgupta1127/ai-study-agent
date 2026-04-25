import uuid
from sqlalchemy import Column, String, DateTime, Table, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database import Base

user_group_association=Table(
    "user_group_association",
    Base.metadata,
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True),
    Column("group_id", UUID(as_uuid=True), ForeignKey("study_groups.id"), primary_key=True),
)

class User(Base):
    __tablename__="users"

    id=Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    display_name = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # --- Relationships ---
    documents = relationship("Document", back_populates="user", cascade="all, delete")
    attempts = relationship("QuizAttempt", back_populates="user", cascade="all, delete")
    progress_records = relationship("Progress", back_populates="user", cascade="all, delete")

    # Many-to-Many with StudyGroup
    groups = relationship(
        "StudyGroup",
        secondary=user_group_association,
        back_populates="members"
    )


# --- StudyGroup Model ---
class StudyGroup(Base):
    __tablename__ = "study_groups"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    invite_code = Column(String(50), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # --- Relationships ---
    owner = relationship("User", backref="owned_groups")

    members = relationship(
        "User",
        secondary=user_group_association,
        back_populates="groups"
    )