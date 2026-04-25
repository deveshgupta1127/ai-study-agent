from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database import engine,Base
from backend.routers import auth, documents, quizzes, chat, groups, progress

from dotenv import load_dotenv
load_dotenv()

app=FastAPI(
    title="AI study assistant",
    version="1.0.0"
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

@app.get("/health")
def health_check():
    return {"status":"ok"}

app.include_router(auth.router, prefix="/api/v1/auth",tags=["auth"])
app.include_router(documents.router, prefix="/api/v1/documents",tags=["documents"])
app.include_router(chat.router, prefix="/api/v1/chat")
app.include_router(quizzes.router, prefix="/api/v1/quizzes")
app.include_router(groups.router, prefix="/api/v1/groups", tags=["groups"])
app.include_router(progress.router, prefix="/api/v1/progress", tags=["progress"])
