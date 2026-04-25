from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from typing import Optional, List

class UserRegister(BaseModel):
    email: EmailStr
    password: str =Field(min_length=6)
    display_name:str

class UserLogin(BaseModel):
    email: EmailStr
    password:str

class TokenRefresh(BaseModel):
    refresh_token:str

class QuizGenerateRequest(BaseModel):
    topic_id: UUID
    quiz_type: str
    difficulty: int
    num_questions: int

class AnswerItem(BaseModel):
    question_id: UUID
    answer: str

class QuizSubmitRequest(BaseModel):
    answers: list[AnswerItem]

class ChatCreateRequest(BaseModel):
    document_id: Optional[UUID]=None

class ChatAskRequest(BaseModel):
    question:str

class GroupCreateRequest(BaseModel):
    name:str= Field(min_length=1, max_length=100)

class GroupJoinRequest(BaseModel):
    invite_code: str=Field(min_length=6,max_length=12)

class GroupShareRequest(BaseModel):
    document_id:UUID

