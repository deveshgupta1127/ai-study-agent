from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from backend.database import get_db
from backend.models import ChatSession, Message, Document
from backend.routers.auth import get_current_user
from backend.agents.orchestrator import get_orchestrator

from backend.schemas.requests import ChatCreateRequest, ChatAskRequest
from backend.schemas.responses import(
    ChatSessionResponse,
    ChatAnswerResponse,
    MessageResponse,
    SourceRef
)

router=APIRouter()

@router.post("/sessions", response_model=ChatSessionResponse)
def create_session(
    request: ChatCreateRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    # ✅ If document is provided, validate it
    if request.document_id:
        doc = db.query(Document).filter(Document.id == request.document_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

    # ✅ ALWAYS create session
    session = ChatSession(
        user_id=user.id,
        document_id=request.document_id  # can be None
    )

    db.add(session)
    db.commit()
    db.refresh(session)

    return session

@router.post("/sessions/{session_id}/ask",response_model=ChatAnswerResponse)
def ask_question(
    session_id:UUID,
    request: ChatAskRequest,
    db:Session=Depends(get_db),
    user=Depends(get_current_user)
):
    session=db.query(ChatSession).filter(ChatSession.id== session_id).first()

    if not session or session.user_id!= user.id:
        raise HTTPException(status_code=404, detail="Session not found")
    
    user_msg=Message(
        session_id=session.id,
        role="user",
        content=request.question
    )
    db.add(user_msg)
    agent=get_orchestrator()

    try:
        response = agent.invoke({
            "messages": [
                {
                    "role": "user",
                    "content": f"""
Answer this question using document context.

question: {request.question}
doc_id: {session.document_id}
"""
                }
            ]
        })
        answer_text=response["messages"][-1].content
    
    except Exception as e:
        raise HTTPException(status_code=500,detail=str(e))
    
    ai_msg=Message(
        session_id=session.id,
        role="assitant",
        content=answer_text
    )
    db.add(ai_msg)
    db.commit()

    sources=[]
    if "Sources:" in answer_text:
        try:
            parts=answer_text.split("Sources: ")
            source_part=parts[1].strip()
            source_ids=source_part.strip("[]").split(",")

            for sid in source_ids:
                sid=sid.strip()
                if sid:
                    sources.append(
                        SourceRef(
                            chunk_id=sid,
                            content_preview="",
                            relevance_score=0.0
                        )
                    )
        except:
            pass

    return ChatAnswerResponse(
        answer=answer_text,
        sources=sources
    )

@router.get("/sessions/{session_id}/history", response_model=list[MessageResponse])
def get_history(
    session_id: UUID,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()

    if not session or session.user_id != user.id:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = (
        db.query(Message)
        .filter(Message.session_id == session_id)
        .order_by(Message.sent_at)
        .all()
    )

    return [
        {
            "role":msg.role,
            "content": msg.content
        }
        for msg in messages
    ]