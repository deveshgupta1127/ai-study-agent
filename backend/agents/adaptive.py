from sqlalchemy.orm import Session
from uuid import UUID

from backend.models import Progress


def get_adaptive_difficulty(
    user_id: UUID,
    topic_id: UUID,
    db: Session,
) -> int:
    """
    Returns difficulty level (1–5) based on user's mastery score.
    """

    progress = db.query(Progress).filter(
        Progress.user_id == user_id,
        Progress.topic_id == topic_id,
    ).first()

    # No data → default medium
    if not progress:
        return 3

    mastery = progress.mastery_score or 0.0

    # ---------------------------
    # Difficulty Mapping Logic
    # ---------------------------
    if mastery < 0.3:
        return 1  # very easy

    elif mastery < 0.6:
        return 2  # easy-medium

    elif mastery < 0.8:
        return 3  # medium

    elif mastery < 0.9:
        return 4  # medium-hard

    else:
        return 5  # hard