import chromadb
from chromadb.config import Settings as ChromaSettings

from backend.config import get_settings

settings=get_settings()

_chroma_client=None

def get_chroma_client():
    global _chroma_client

    if _chroma_client is None:
        _chroma_client=chromadb.HttpClient(
            host=settings.CHROMADB_HOST,
            port=settings.CHROMADB_PORT,
            settings=ChromaSettings(
                anonymized_telemetry=False
            )
        )
    return _chroma_client

def get_collection():
    client=get_chroma_client()

    return client.get_or_create_collection(
        name="study_chunks",
        metadata={"hnsw:space": "cosine"}
    )