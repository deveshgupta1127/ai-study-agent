from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from backend.database import get_db
from backend.models import Progress, QuizAttempt, Topic, Document
from backend.routers.auth import get_current_user

from backend.schemas.responses import (
    DashboardResponse,
    TopicMasteryResponse,
    StudyPlanResponse,
    ActivityResponse,
)

# ✅ NEW IMPORTS (IMPORTANT)
from backend.agents.tools import (
    read_progress,
    identify_weak_areas,
    generate_study_plan,
)
from datetime import datetime

router = APIRouter(tags=["progress"])


# -------------------------------
# Dashboard
# -------------------------------
@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    total_docs = db.query(func.count(Document.id)).filter(
        Document.user_id == user.id
    ).scalar()

    total_quizzes = db.query(func.count(QuizAttempt.id)).filter(
        QuizAttempt.user_id == user.id
    ).scalar()

    avg_mastery = db.query(func.avg(Progress.mastery_score)).filter(
        Progress.user_id == user.id
    ).scalar()

    avg_mastery = float(avg_mastery or 0.0)

    topics_studied = db.query(func.count(Progress.topic_id)).filter(
        Progress.user_id == user.id
    ).scalar()

    recent_attempts = db.query(QuizAttempt).filter(
        QuizAttempt.user_id == user.id
    ).order_by(desc(QuizAttempt.attempted_at)).limit(5).all()

    recent_activity = [
        ActivityResponse(
            type="quiz_attempt",
            detail=f"Answered question {a.question_id}",
            timestamp=a.attempted_at,
        )
        for a in recent_attempts
    ]

    return DashboardResponse(
        total_docs=total_docs or 0,
        total_quizzes=total_quizzes or 0,
        avg_mastery=round(avg_mastery, 2),
        topics_studied=topics_studied or 0,
        recent_activity=recent_activity,
    )


# -------------------------------
# Topic Mastery
# -------------------------------
@router.get("/topics", response_model=list[TopicMasteryResponse])
def get_topic_mastery(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    records = db.query(Progress, Topic).join(
        Topic, Progress.topic_id == Topic.id
    ).filter(
        Progress.user_id == user.id
    ).all()

    result = []

    for progress, topic in records:
        result.append(
            TopicMasteryResponse(
                topic_id=topic.id,
                topic_title=topic.title,
                mastery_score=round(progress.mastery_score, 2),
                questions_attempted=progress.questions_attempted,
                last_studied=progress.last_studied,
            )
        )

    return result


# -------------------------------
# Recommendations (FIXED)
# -------------------------------
@router.get("/recommendations", response_model=StudyPlanResponse)
def get_recommendations(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    try:
        # 1. Get progress (from DB via tool)
        progress = read_progress(str(user.id))

        # 2. Identify weak topics
        weak_topics = identify_weak_areas(progress, threshold=0.6)

        # 3. Generate study plan
        study_plan = generate_study_plan(weak_topics, progress)

        return StudyPlanResponse(
            weak_topics=weak_topics,
            study_plan=study_plan,
            generated_at=datetime.utcnow(),
        )

    except Exception as e:
        # fallback safe response
        return StudyPlanResponse(
            weak_topics=[],
            study_plan=[],
            generated_at=None,
        )


# -------------------------------
# Activity History
# -------------------------------
@router.get("/history", response_model=list[ActivityResponse])
def get_history(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    attempts = db.query(QuizAttempt).filter(
        QuizAttempt.user_id == user.id
    ).order_by(desc(QuizAttempt.attempted_at)).limit(20).all()

    history = [
        ActivityResponse(
            type="quiz_attempt",
            detail=f"Answered question {a.question_id}",
            timestamp=a.attempted_at,
        )
        for a in attempts
    ]

    return history