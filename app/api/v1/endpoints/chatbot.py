from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import settings
from app.chatbot.graph import run_chat
from app.chatbot.vector_store import sync_student_index

router = APIRouter(prefix="/chatbot", tags=["AI Chatbot"])


class ChatTurn(BaseModel):
    role: str = Field(..., examples=["user"])
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., examples=["Which students are majoring in Computer Science?"])
    history: list[ChatTurn] | None = Field(
        default=None, description="Optional prior turns for multi-turn context."
    )


class ChatResponse(BaseModel):
    answer: str
    trace: list[dict]


class ReindexResponse(BaseModel):
    indexed_students: int
    message: str


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest):
    """
    Talk to the LangGraph-powered student database assistant.

    The agent (Gemini) decides which tools to call — e.g. looking up a
    student, listing a course roster, or doing a semantic search over
    student bios — to ground its answer in real database content.
    """
    if not settings.GOOGLE_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="Chatbot unavailable: GOOGLE_API_KEY is not configured on the server.",
        )
    history = [turn.model_dump() for turn in payload.history] if payload.history else None
    try:
        result = run_chat(payload.message, history=history)
    except Exception as exc:  # surface a clean 500 instead of a raw stack trace
        raise HTTPException(status_code=500, detail=f"Chatbot error: {exc}") from exc
    return ChatResponse(answer=result["answer"], trace=result["trace"])


@router.post("/reindex", response_model=ReindexResponse)
def reindex_students(db: Session = Depends(get_db)):
    """
    Rebuild the vector index (Chroma) from current student records.
    Call this after bulk-loading or significantly changing student bios so
    semantic search reflects the latest data.
    """
    count = sync_student_index(db)
    return ReindexResponse(
        indexed_students=count,
        message=f"Vector index rebuilt with {count} student profile(s).",
    )
