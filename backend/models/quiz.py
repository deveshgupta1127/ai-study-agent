import uuid
from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.dialects. postgresql import UUID
from sqlalchemy.orm import relationship
from backend.database import Base
from datetime import datetime

class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    topic_id = Column(UUID(as_uuid=True), ForeignKey("topics.id"), nullable=False)

    quiz_type = Column(String, nullable=False)
    difficulty = Column(Integer, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    questions = relationship("Question", back_populates="quiz", cascade="all, delete")

    # 🔥 THIS MUST EXIST EXACTLY
    attempts = relationship("QuizAttempt", back_populates="quiz", cascade="all, delete")

class Question(Base):
    __tablename__ = "questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    quiz_id = Column(UUID(as_uuid=True), ForeignKey("quizzes.id"))

    question_text = Column(String)
    options = Column(JSON, nullable=True)

    correct_answer = Column(String)
    explanation = Column(String)

    # 🔥 ADD THIS
    quiz = relationship("Quiz", back_populates="questions")


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"))
    quiz_id = Column(UUID(as_uuid=True), ForeignKey("quizzes.id"))

    user_answer = Column(String)
    is_correct = Column(Boolean)

    attempted_at=Column(DateTime,default=datetime.utcnow)

    # 🔥 MUST MATCH EXACT STRING
    quiz = relationship("Quiz", back_populates="attempts")
    user = relationship("User", back_populates="attempts")