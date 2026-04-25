from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.database import get_db
from backend.models import StudyGroup, Document, User, user_group_association
from backend.routers.auth import get_current_user
from backend.schemas.requests import (
    GroupCreateRequest,
    GroupJoinRequest,
    GroupShareRequest,
)
from backend.schemas.responses import GroupResponse, DocumentResponse

import secrets
import string

router = APIRouter(tags=["groups"])


# -------------------------------
# Helper: Generate Invite Code
# -------------------------------
def generate_invite_code(length: int = 8) -> str:
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


# -------------------------------
# Create Group
# -------------------------------
@router.post("/", response_model=GroupResponse)
def create_group(
    payload: GroupCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        invite_code = generate_invite_code()

        group = StudyGroup(
            name=payload.name,
            owner_id=user.id,
            invite_code=invite_code,
        )

        db.add(group)
        db.commit()
        db.refresh(group)

        # add owner to group members
        db.execute(
            user_group_association.insert().values(
                user_id=user.id,
                group_id=group.id,
            )
        )
        db.commit()

        return GroupResponse(
            id=group.id,
            name=group.name,
            invite_code=group.invite_code,
            owner_id=group.owner_id,
            member_count=1,
            created_at=group.created_at,
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# -------------------------------
# Join Group
# -------------------------------
@router.post("/join", response_model=GroupResponse)
def join_group(
    payload: GroupJoinRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    group = db.query(StudyGroup).filter(
        StudyGroup.invite_code == payload.invite_code
    ).first()

    if not group:
        raise HTTPException(status_code=404, detail="Invalid invite code")

    # check if already member
    existing = db.execute(
        user_group_association.select().where(
            (user_group_association.c.user_id == user.id) &
            (user_group_association.c.group_id == group.id)
        )
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Already a member")

    try:
        db.execute(
            user_group_association.insert().values(
                user_id=user.id,
                group_id=group.id,
            )
        )
        db.commit()

        # count members
        member_count = db.execute(
            func.count().select().select_from(user_group_association).where(
                user_group_association.c.group_id == group.id
            )
        ).scalar()

        return GroupResponse(
            id=group.id,
            name=group.name,
            invite_code=group.invite_code,
            owner_id=group.owner_id,
            member_count=member_count,
            created_at=group.created_at,
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# -------------------------------
# Get User Groups
# -------------------------------
@router.get("/", response_model=list[GroupResponse])
def get_groups(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    groups = db.query(StudyGroup).join(
        user_group_association,
        StudyGroup.id == user_group_association.c.group_id
    ).filter(
        user_group_association.c.user_id == user.id
    ).all()

    results = []

    for group in groups:
        member_count = db.execute(
            func.count().select().select_from(user_group_association).where(
                user_group_association.c.group_id == group.id
            )
        ).scalar()

        results.append(
            GroupResponse(
                id=group.id,
                name=group.name,
                invite_code=group.invite_code,
                owner_id=group.owner_id,
                member_count=member_count,
                created_at=group.created_at,
            )
        )

    return results


# -------------------------------
# Share Document to Group
# -------------------------------
@router.post("/{group_id}/share", response_model=DocumentResponse)
def share_document(
    group_id: str,
    payload: GroupShareRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    group = db.query(StudyGroup).filter(StudyGroup.id == group_id).first()

    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    # check membership
    membership = db.execute(
        user_group_association.select().where(
            (user_group_association.c.user_id == user.id) &
            (user_group_association.c.group_id == group_id)
        )
    ).first()

    if not membership:
        raise HTTPException(status_code=403, detail="Not a group member")

    document = db.query(Document).filter(
        Document.id == payload.document_id
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # only owner can share
    if document.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not your document")

    try:
        document.group_id = group_id
        db.commit()
        db.refresh(document)

        return document

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# -------------------------------
# Get Group Documents
# -------------------------------
@router.get("/{group_id}/documents", response_model=list[DocumentResponse])
def get_group_documents(
    group_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # check membership
    membership = db.execute(
        user_group_association.select().where(
            (user_group_association.c.user_id == user.id) &
            (user_group_association.c.group_id == group_id)
        )
    ).first()

    if not membership:
        raise HTTPException(status_code=403, detail="Not a group member")

    documents = db.query(Document).filter(
        Document.group_id == group_id
    ).all()

    return documents