from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
import json
import re
from langchain_anthropic import ChatAnthropic

from backend.database import get_db
from backend.models import Quiz, Question, QuizAttempt, Progress, Topic
from backend.routers.auth import get_current_user
from backend.agents.orchestrator import get_orchestrator

from backend.schemas.requests import QuizGenerateRequest, QuizSubmitRequest
from backend.schemas.responses import QuizResponse, QuizResultResponse


router = APIRouter()


# ==============================
# GENERATE QUIZ (AGENT CALL)
# ==============================

def _generate_questions_with_llm(
    title: str,
    summary: str,
    num: int,
    quiz_type: str,
) -> list[dict]:
    """Ask the LLM to produce question content only. No IDs, no DB objects."""
    llm = ChatAnthropic(
        model="claude-sonnet-4-5",
        max_tokens=2048,
    )

    if quiz_type == "mcq":
        schema_hint = """[
  {"question": "...", "options": ["...", "...", "...", "..."], "answer": "exact text of the correct option", "explanation": "..."}
]"""
    else:
        schema_hint = """[
  {"question": "...", "answer": "...", "explanation": "..."}
]"""

    prompt = f"""Generate {num} {quiz_type} questions about the topic below.

Topic title: {title}
Topic summary: {summary}

Rules:
- Questions must be conceptual and test understanding
- Return ONLY a JSON array, no markdown fences, no prose before or after
- Do NOT invent or include any IDs, topic_ids, or quiz_ids

Format:
{schema_hint}
"""

    raw = llm.invoke(prompt).content.strip()
    # Strip ```json ... ``` fences if the model added them anyway
    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw).strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"[LLM JSON parse failed] {e}\nRaw output: {raw[:500]}")
        return []

    return data if isinstance(data, list) else []

@router.post("/generate", response_model=QuizResponse)
def generate_quiz(
    request: QuizGenerateRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    # Step 1: Look up the topic ourselves — never trust the LLM with IDs
    topic = db.query(Topic).filter(Topic.id == request.topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    # Step 2: Ask the LLM ONLY to generate question content.
    # It never sees topic_id, quiz_id, or anything resembling a primary key.
    questions_data = _generate_questions_with_llm(
        title=topic.title,
        summary=topic.summary or "",
        num=request.num_questions,
        quiz_type=request.quiz_type,
    )

    if not questions_data:
        raise HTTPException(status_code=500, detail="LLM returned no questions")

    # Step 3: WE create the Quiz using the trusted topic.id from the DB
    quiz = Quiz(
        topic_id=topic.id,                 # trusted UUID, straight from DB
        quiz_type=request.quiz_type,
        difficulty=request.difficulty,
    )
    db.add(quiz)
    db.commit()
    db.refresh(quiz)

    # Step 4: Save questions, attaching them to the quiz WE just made
    for q in questions_data:
        if not q.get("question"):
            continue  # skip malformed entries
        question = Question(
            quiz_id=quiz.id,
            question_text=q["question"],
            options=q.get("options", []),
            correct_answer=q.get("answer") or q.get("correct", ""),
            explanation=q.get("explanation", ""),
        )
        db.add(question)
    db.commit()

    questions = db.query(Question).filter(Question.quiz_id == quiz.id).all()
    if not questions:
        raise HTTPException(status_code=500, detail="No questions were saved")

    return QuizResponse(
        id=quiz.id,
        topic_id=quiz.topic_id,
        quiz_type=quiz.quiz_type,
        difficulty=quiz.difficulty,
        questions=[
            {
                "id": q.id,
                "question_text": q.question_text,
                "options": q.options,
                "quiz_type": quiz.quiz_type,
            }
            for q in questions
        ],
    )

# ==============================
# GET QUIZ
# ==============================

@router.get("/{quiz_id}", response_model=QuizResponse)
def get_quiz(
    quiz_id: UUID,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()

    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    questions = db.query(Question).filter(Question.quiz_id == quiz.id).all()

    return QuizResponse(
        id=quiz.id,
        topic_id=quiz.topic_id,
        quiz_type=quiz.quiz_type,
        difficulty=quiz.difficulty,
        questions=[
            {
                "id": q.id,
                "question_text": q.question_text,
                "options": q.options,
                "quiz_type": quiz.quiz_type
            }
            for q in questions
        ]
    )


# ==============================
# SUBMIT QUIZ
# ==============================

@router.post("/{quiz_id}/submit", response_model=QuizResultResponse)
def submit_quiz(
    quiz_id: UUID,
    request: QuizSubmitRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    questions = db.query(Question).filter(Question.quiz_id == quiz_id).all()

    if not questions:
        raise HTTPException(status_code=404, detail="Quiz not found")

    correct = 0
    results = []

    for ans in request.answers:
        question = next((q for q in questions if q.id == ans.question_id), None)

        if not question:
            continue

        is_correct = question.correct_answer.strip().lower() == ans.answer.strip().lower()

        if is_correct:
            correct += 1

        attempt = QuizAttempt(
            user_id=user.id,
            question_id=question.id,
            user_answer=ans.answer,
            is_correct=is_correct
        )
        db.add(attempt)

        results.append({
            "question_id": question.id,
            "user_answer": ans.answer,
            "correct_answer": question.correct_answer,
            "is_correct": is_correct,
            "explanation": question.explanation
        })

    total = len(questions)
    score = correct / total if total > 0 else 0

    # 🔥 Update progress
    topic_id = db.query(Quiz).filter(Quiz.id == quiz_id).first().topic_id

    progress = (
        db.query(Progress)
        .filter(Progress.user_id == user.id, Progress.topic_id == topic_id)
        .first()
    )

    if not progress:
        progress = Progress(
            user_id=user.id,
            topic_id=topic_id,
            mastery_score=score,
            questions_attempted=total,
            questions_correct=correct
        )
        db.add(progress)
    else:
        progress.questions_attempted += total
        progress.questions_correct += correct
        progress.mastery_score = (
            progress.questions_correct / progress.questions_attempted
        )

    db.commit()

    return QuizResultResponse(
        quiz_id=quiz_id,
        score=score,
        total=total,
        correct=correct,
        results=results
    )


# ==============================
# GET RESULTS
# ==============================

@router.get("/{quiz_id}/results", response_model=QuizResultResponse)
def get_results(
    quiz_id: UUID,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    attempts = (
        db.query(QuizAttempt)
        .join(Question)
        .filter(Question.quiz_id == quiz_id, QuizAttempt.user_id == user.id)
        .all()
    )

    if not attempts:
        raise HTTPException(status_code=404, detail="No attempts found")

    correct = sum(1 for a in attempts if a.is_correct)
    total = len(attempts)

    results = [
        {
            "question_id": a.question_id,
            "user_answer": a.user_answer,
            "correct_answer": a.question.correct_answer,
            "is_correct": a.is_correct,
            "explanation": a.question.explanation
        }
        for a in attempts
    ]

    return QuizResultResponse(
        quiz_id=quiz_id,
        score=correct / total if total > 0 else 0,
        total=total,
        correct=correct,
        results=results
    )