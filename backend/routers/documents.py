from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
import os
import shutil
from uuid import uuid4
from backend.database import get_db
from backend.services.file_processor import extract_text

from backend.agents.tools import (
    chunk_text,
    generate_embeddings,
    save_to_chromadb,
    extract_topics_from_text
)

from sqlalchemy import or_

from backend.models import Document, Topic, user_group_association
from backend.routers.auth import get_current_user
from backend.schemas.responses import DocumentResponse, TopicResponse, MessageResponse

from backend.agents.orchestrator import get_orchestrator

import uuid

router = APIRouter(tags=["documents"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# =========================
# BACKGROUND PROCESSING
# =========================

def process_document(file_path: str, file_type: str, document_id: str, db: Session):
    """
    Runs in background:
    - extract text
    - chunk
    - embed
    - store
    - extract topics
    """

    try:
        print(f"[START] Processing document: {document_id}")

        # =========================
        # SET STATUS → PROCESSING
        # =========================
        document = db.query(Document).filter(Document.id == document_id).first()
        if document:
            document.status = "processing"
            db.commit()

        # =========================
        # 1. Extract text
        # =========================
        text = extract_text(file_path, file_type)

        if not text or len(text.strip()) == 0:
            raise Exception("Extracted text is empty")

        # =========================
        # 2. Chunk text
        # =========================
        chunks = chunk_text.invoke({"text": text})
        chunk_contents = [c["content"] for c in chunks]

        print(f"[INFO] Total chunks: {len(chunk_contents)}")

        # =========================
        # 3. Generate embeddings (mock)
        # =========================
        ids = generate_embeddings.invoke({"chunks": chunk_contents})

        # =========================
        # 4. Save to ChromaDB
        # =========================
        save_to_chromadb.invoke({
            "chunks": chunk_contents,
            "ids": ids,
            "doc_id": document_id
        })

        # =========================
        # 5. Extract topics
        # =========================
        topics = extract_topics_from_text.invoke({"text": text})

        print(f"[INFO] Topics extracted: {len(topics)}")

        # =========================
        # 6. Save topics
        # =========================
        for t in topics:
            topic = Topic(
                document_id=document_id,
                title=t.get("title"),
                summary=t.get("summary"),
                difficulty_level=t.get("difficulty", 3)
            )
            db.add(topic)

        # =========================
        # 7. FINAL STATUS → DONE
        # =========================
        document = db.query(Document).filter(Document.id == document_id).first()
        if document:
            document.status = "done"

        db.commit()

        print(f"[SUCCESS] Document processed: {document_id}")

    except Exception as e:
        print(f"[ERROR] Document processing failed: {str(e)}")

        # =========================
        # FAIL SAFE
        # =========================
        document = db.query(Document).filter(Document.id == document_id).first()
        if document:
            document.status = "error"
            db.commit()

def has_document_access(user_id, document, db: Session) -> bool:
    # Owner
    if document.user_id == user_id:
        return True

    # Group access
    if document.group_id:
        membership = db.execute(
            user_group_association.select().where(
                (user_group_association.c.user_id == user_id) &
                (user_group_association.c.group_id == document.group_id)
            )
        ).first()

        return membership is not None

    return False


# =========================
# UPLOAD ENDPOINT
# =========================

@router.post("/upload")
def upload_document(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    allowed_types = ["pdf", "txt", "docx"]

    filename = file.filename
    file_ext = filename.split(".")[-1].lower()

    if file_ext not in allowed_types:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    # Save file
    document_id = str(uuid4())
    file_dir = os.path.join(UPLOAD_DIR, document_id)
    os.makedirs(file_dir, exist_ok=True)

    file_path = os.path.join(file_dir, filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # DB entry
    document = Document(
        id=document_id,
        user_id=user.id,
        filename=filename,
        file_type=file_ext,
        status="pending"
    )

    db.add(document)
    db.commit()

    # Background task
    background_tasks.add_task(
        process_document,
        file_path,
        file_ext,
        document_id,
        db
    )

    return {
        "id": document_id,
        "filename": filename,
        "status": "processing"
    }


# =========================
# GET DOCUMENTS
# =========================

@router.get("")
def get_documents(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    documents = (
        db.query(Document)
        .filter(Document.user_id == user.id)
        .all()
    )
    return documents


# =========================
# GET TOPICS
# =========================

@router.get("/{document_id}/topics")
def get_document_topics(
    document_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == user.id
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    topics = db.query(Topic).filter(
        Topic.document_id == document_id
    ).all()

    return topics

@router.delete("/{document_id}")
@router.delete("/{doc_id}", response_model=MessageResponse)
def delete_document(
    doc_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    document = db.query(Document).filter(Document.id == doc_id).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Only owner can delete
    if document.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not your document")

    db.delete(document)
    db.commit()

    return {"message": "Document deleted successfully"}

@router.post("/upload", response_model=DocumentResponse)
def upload_document(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    # Validate file
    ext = file.filename.split(".")[-1].lower()
    if ext not in ["pdf", "txt", "docx"]:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    # Save file
    doc_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{doc_id}.{ext}")

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Create DB record
    document = Document(
        id=doc_id,
        user_id=user.id,
        filename=file.filename,
        file_type=ext,
        status="pending",
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    # Background processing via agent
    def process():
        agent = get_orchestrator()

        try:
            agent.invoke({
                "messages": [
                    {
                        "role": "user",
                        "content": f"Process document {file_path} with document_id={doc_id}"
                    }
                ]
            })

            document.status = "done"
        except Exception:
            document.status = "error"

        finally:
            db.commit()

    background_tasks.add_task(process)

    return document

@router.get("/", response_model=list[DocumentResponse])
def get_documents(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    # get user's group ids
    group_ids = db.execute(
        user_group_association.select().where(
            user_group_association.c.user_id == user.id
        )
    ).fetchall()

    group_ids = [g.group_id for g in group_ids]

    documents = db.query(Document).filter(
        or_(
            Document.user_id == user.id,
            Document.group_id.in_(group_ids)
        )
    ).all()

    return documents

@router.get("/{doc_id}", response_model=DocumentResponse)
def get_document(
    doc_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    document = db.query(Document).filter(Document.id == doc_id).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if not has_document_access(user.id, document, db):
        raise HTTPException(status_code=403, detail="Access denied")

    return document

@router.get("/{doc_id}/topics", response_model=list[TopicResponse])
def get_topics(
    doc_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    document = db.query(Document).filter(Document.id == doc_id).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if not has_document_access(user.id, document, db):
        raise HTTPException(status_code=403, detail="Access denied")

    topics = db.query(Topic).filter(
        Topic.document_id == doc_id
    ).all()

    return topics