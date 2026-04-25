from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class UserResponse(BaseModel):
    model_config=ConfigDict(from_attriibutes=True)

    id:UUID
    email:str
    display_name:str
    created_at:datetime

class TokenResponse(BaseModel):
    access_token:str
    refresh_token:str
    token_type:str="bearer"

class MessageResponse(BaseModel):
    content:str
    role:str

class TopicResponse(BaseModel):
    model_config=ConfigDict(from_attributes=True)

    id:UUID
    title:str
    summary:Optional[str]
    difficulty_level: int

class DocumentResponse(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    id:UUID
    filename:str
    file_type:str
    status:str
    uploaded_at:datetime
    topics: Optional[List[TopicResponse]]=None

class QuestionResponse(BaseModel):
  id: UUID 
  question_text: str
  options: Optional[list]
  quiz_type: str

class QuizResponse(BaseModel):
  id: UUID
  topic_id: UUID
  quiz_type: str
  difficulty: int
  questions: list[QuestionResponse]

class AnswerResult(BaseModel):
  question_id: UUID
  user_answer: str
  correct_answer: str
  is_correct: bool
  explanation: Optional[str]

class QuizResultResponse(BaseModel):
  quiz_id: UUID
  score: float
  total: int
  correct: int
  results: list[AnswerResult]

class SourceRef(BaseModel):
  chunk_id: str
  content_preview: str
  relevance_score: float

class ChatAnswerResponse(BaseModel):
  answer: str
  sources: list[SourceRef]

class ChatSessionResponse(BaseModel):
  id: UUID
  document_id: Optional[UUID]
  started_at: datetime

class GroupResponse(BaseModel):
  id: UUID
  name: str
  invite_code: str
  owner_id: UUID
  member_count: int
  created_at: datetime

class TopicMasteryResponse(BaseModel):
  topic_id: UUID
  topic_title: str
  mastery_score: float
  questions_attempted: int
  last_studied: Optional[datetime]


class PlanItem(BaseModel):
  topic_id: UUID
  topic_title: str
  recommended_action: str
  difficulty: int
  priority: int
  est_minutes: int

class StudyPlanResponse(BaseModel):
  weak_topics: List[dict]   # raw weak topic data
  study_plan: List[PlanItem]
  generated_at: Optional[datetime]


class ActivityResponse(BaseModel):
  type: str
  detail: str
  timestamp: datetime


class DashboardResponse(BaseModel):
  total_docs: int
  total_quizzes: int
  avg_mastery: float
  topics_studied: int
  recent_activity: List[ActivityResponse]

class GroupResponse(BaseModel):
  id: UUID
  name: str
  invite_code: str
  owner_id: UUID
  member_count: int
  created_at: datetime

class TopicMasteryResponse(BaseModel):
  topic_id: UUID
  topic_title: str
  mastery_score: float
  questions_attempted: int
  last_studied: Optional[datetime]


class PlanItem(BaseModel):
  topic_id: UUID
  topic_title: str
  recommended_action: str
  difficulty: int
  priority: int
  est_minutes: int


class StudyPlanResponse(BaseModel):
  weak_topics: List[dict]   # raw weak topic data
  study_plan: List[PlanItem]
  generated_at: Optional[datetime]


class ActivityResponse(BaseModel):
  type: str
  detail: str
  timestamp: datetime


class DashboardResponse(BaseModel):
  total_docs: int
  total_quizzes: int
  avg_mastery: float
  topics_studied: int
  recent_activity: List[ActivityResponse]