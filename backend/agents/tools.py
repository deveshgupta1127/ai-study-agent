from langchain_core.tools import tool
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
import uuid

from datetime import datetime

from backend.services.embedding import get_collection
from backend.models import Chunk, Topic, Quiz, Question, Progress, QuizAttempt
from backend.database import SessionLocal

@tool
def chunk_text(text:str, chunk_size: int=800, overlap: int =200)->List[Dict]:
    """
    Splits text into overlapping chunks.

    Args:
        text: input text
        chunk_size: size of each chunk
        overlap: overlap between chunks

    Returns:
        List of chunk dictionaries
    """
    chunks=[]
    start=0
    index=0
    text_length=len(text)

    while start < text_length:
        end=start+chunk_size
        chunk=text[start:end]

        chunks.append({
            "content": chunk,
            "index":index,
            "start":start,
            "end":end
        })
        start+=(chunk_size-overlap)
        index+=1
    return chunks

@tool
def generate_embeddings(chunks: List[str])->List[str]:
    """
    Generates embedding IDs for chunks (placeholder).

    Args:
        chunks: list of text chunks

    Returns:
        list of embedding IDs
    """
    embedding_ids=[]

    for _ in chunks:
        embedding_ids.append(str(uuid.uuid4()))
    
    return embedding_ids

@tool
def save_to_chromadb(chunks:List[str], ids:List[str],doc_id:str)->bool:
    """
    Saves chunks into ChromaDB.

    Args:
        chunks: list of text chunks
        ids: embedding IDs
        doc_id: document ID

    Returns:
        True if successful
    """
    collection=get_collection()
    try:
        collection.add(
            documents=chunks,
            ids=ids,  # ❗ FIX THIS (was "id")
            metadatas=[{"document_id": doc_id} for _ in chunks]
        )
        return True
    
    except Exception as e:
        raise Exception(f"Failed to save to ChromaDB: {str(e)}")

@tool
def extract_topics_from_text(text: str) -> List[Dict]:
    """Extract meaningful study topics from a document."""
    from langchain.chat_models import init_chat_model
    import json, re

    llm = init_chat_model("anthropic:claude-sonnet-4-5")
    prompt = f"""Extract 3-5 main study topics from this text.
Return ONLY a JSON array, no markdown:
[{{"title": "...", "summary": "...", "difficulty": 1-5}}]

Text:
{text[:4000]}
"""
    resp = llm.invoke(prompt).content.strip()
    resp = re.sub(r"^```(?:json)?\s*|\s*```$", "", resp)
    try:
        return json.loads(resp)
    except json.JSONDecodeError:
        return [{"title": "Untitled topic", "summary": text[:200], "difficulty": 3}]

@tool
def read_topic_chunks(topic_id: str)-> List[Dict]:
    """
    Fetch all chunks associated with a topic via its document.
    Returns list of chunk content and IDs.
    """
    db: Session = SessionLocal()

    try:
        topic=db.query(Topic).filter(Topic.id==topic_id).first()
        if not topic:
            return []
        
        chunks=(
            db.query(Chunk)
            .filter(Chunk.document_id==topic.document_id)
            .order_by(Chunk.chunk_index)
            .all()
        )

        return [
            {
                "chunk_id": str(chunk.id),
                "content":chunk.content
            }
            for chunk in chunks
        ]
    finally:
        db.close()

@tool
def generate_mcq(topic: str, context: str, num: int = 5) -> List[Dict]:
    """Generate multiple-choice questions (MCQs) from study material.

    Use this tool when the user wants to practice, self-test, or create a quiz
    from content they've uploaded or studied. Each question has 4 options, one
    correct answer, and an explanation.

    Args:
        topic: The subject or focus area for the questions (e.g., "photosynthesis").
        context: The source text the questions should be based on — typically a
            chunk of the user's document or notes.
        num: How many questions to generate. Defaults to 5.

    Returns:
        A list of dicts, each with keys: "question", "options" (list of 4),
        "correct", and "explanation". Returns an empty list if generation fails.
    """
    llm = init_chat_model("anthropic:claude-3-5-sonnet")

    prompt = f"""
Generate {num} MCQ questions.

Topic: {topic}

Context:
{context}

Rules:
- Questions must be conceptual
- 4 options each
- One correct answer
- Include explanation

Return ONLY JSON:
[
  {{
    "question": "...",
    "options": ["A","B","C","D"],
    "correct": "A",
    "explanation": "..."
  }}
]
"""

    response = llm.invoke(prompt)

    try:
        return json.loads(response.content)
    except:
        return []

@tool
def generate_short_answer(topic:str, context:str, num: int=3)->List[Dict]:
    """
    Generate short-answer questions from given topic and context.
    Returns list of questions with answers and explanations.
    """
    return [
        {
            "question":"sample question about {topic}",
            "answer":"sample answer about{topic}",
            "explanation":"sample explanation about {topic}"
        }
    ]

@tool
def save_quiz(
    topic_id:str,
    quiz_type:str,
    difficulty:int,
    questions:List[Dict]
)-> str:
    """
    LLM will generate MCQs — we just define structure
    """
    db: Session=SessionLocal()

    try:
        quiz=Quiz(
            id=uuid.uuid4(),
            topic_id=topic_id,
            quiz_type=quiz_type,
            difficulty=difficulty
        )
        db.add(quiz)
        db.flush()

        for q in questions:
            question=Question(
                id=uuid.uuid4(),
                quiz_id=quiz.id,
                question_text=q.get("question"),
                options=q.get("options"),
                correct_answer=q.get("correct") or q.get("answer"),
                explanation=q.get("explanation")
            )
            db.add(question)
        db.commit()
        return str(quiz.id)
    
    except Exception as e:
        db.rollback()
        raise e
    
    finally:
        db.close()

@tool
def search_chromadb(
    query: str,
    doc_id: Optional[str] = None,
    n_results: int = 5
) -> List[Dict]:
    """
    Semantic search in ChromaDB
    """
    collection = get_collection()

    where_filter = {}
    if doc_id:
        where_filter["document_id"] = doc_id

    results = collection.query(
        query_texts=[query],
        n_results=n_results,
        where=where_filter if where_filter else None
    )

    chunks = []
    for i in range(len(results["documents"][0])):
        chunks.append({
            "chunk_id": results["ids"][0][i],
            "content": results["documents"][0][i],
            "distance": results["distances"][0][i]
        })

    return chunks


@tool
def format_context(chunks: List[Dict]) -> str:
    """
    Convert retrieved chunks into LLM-readable context
    """
    if not chunks:
        return "No relevant context found."

    formatted = []
    for i, chunk in enumerate(chunks):
        formatted.append(
            f"[Chunk {i+1} | ID: {chunk['chunk_id']}]\n{chunk['content']}"
        )

    return "\n\n".join(formatted)

@tool
def read_progress(user_id: str)-> List[Dict]:
    """
    Fetch all progress records for a user.
    """
    from backend.database import SessionLocal

    db:Session=SessionLocal()

    try:
        records = db.query(Progress, Topic).join(
            Topic, Progress.topic_id == Topic.id
        ).filter(
            Progress.user_id==user_id
        ).all()

        result=[]

        for progress, topic in records:
            result.append({
                "topic_id": str(topic.id),
                "topic_title": topic.title,
                "mastery_score": float(progress.mastery_score or 0.0),
                "questions_attempted": progress.questions_attempted,
                "questions_correct": progress.questions_correct,
                "last_studied": progress.last_studied.isoformat() if progress.last_studied else None,
            })
        
        return result

    finally:
        db.close()

@tool
def calculate_mastery(attempts: List[Dict]) -> float:
    """
    Calculates mastery score from attempts.
    """
    if not attempts:
        return 0.0

    total = len(attempts)
    correct = sum(1 for a in attempts if a.get("is_correct"))

    return round(correct / total, 2)

@tool
def identify_weak_areas(
    progress: List[Dict],
    threshold: float = 0.6
) -> List[Dict]:
    """
    Returns topics where mastery is below threshold.
    """
    weak = [
        p for p in progress
        if p["mastery_score"] < threshold
    ]

    # sort by lowest mastery first
    weak.sort(key=lambda x: x["mastery_score"])

    return weak

@tool
def generate_study_plan(
    weak_topics: List[Dict],
    all_progress: List[Dict]
) -> List[Dict]:
    """
    Generate prioritized study plan.
    """

    plan = []

    now = datetime.utcnow()

    for topic in weak_topics:
        mastery = topic["mastery_score"]

        # -------------------------
        # Priority Logic
        # -------------------------
        priority = 1  # default

        if mastery < 0.3:
            priority = 5
        elif mastery < 0.5:
            priority = 4
        elif mastery < 0.6:
            priority = 3

        # boost if not studied recently
        if topic["last_studied"]:
            last = datetime.fromisoformat(topic["last_studied"])
            days_gap = (now - last).days

            if days_gap > 7:
                priority += 1

        # -------------------------
        # Action Logic
        # -------------------------
        if mastery < 0.3:
            action = "Re-learn fundamentals and take easy quiz"
            difficulty = 1

        elif mastery < 0.6:
            action = "Practice with mixed questions"
            difficulty = 2

        elif mastery < 0.8:
            action = "Attempt challenging questions"
            difficulty = 3

        else:
            action = "Revise and maintain"
            difficulty = 4

        plan.append({
            "topic_id": topic["topic_id"],
            "topic_title": topic["topic_title"],
            "recommended_action": action,
            "difficulty": difficulty,
            "priority": priority,
            "est_minutes": 20 + (5 - difficulty) * 5
        })

    # sort by priority descending
    plan.sort(key=lambda x: x["priority"], reverse=True)

    return plan