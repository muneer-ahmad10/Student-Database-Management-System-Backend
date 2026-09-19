"""
Vector database exploration module.

Uses Chroma (local, embedded vector DB) with Gemini embeddings to enable
semantic search over student bios/profiles — e.g. "find students interested
in robotics" instead of exact keyword matching. This demonstrates how a
vector store can sit alongside the relational database: SQL for structured
CRUD data, vectors for unstructured semantic search over free-text fields.

The index is built lazily and refreshed on demand (`sync_student_index`) so
it never blocks API startup and always reflects the current DB contents.
"""
from __future__ import annotations

import chromadb
from chromadb.utils import embedding_functions
from sqlalchemy.orm import Session

from app.config import settings
from app.models.student import Student

_client = None
_collection = None


def _get_client() -> "chromadb.ClientAPI":
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
    return _client


def _get_embedding_function():
    """
    Uses Gemini embeddings when an API key is configured, otherwise falls back
    to Chroma's bundled default (all-MiniLM) so the vector store still works
    in demo/offline mode without a Gemini key.
    """
    if settings.GOOGLE_API_KEY:
        return embedding_functions.GoogleGenerativeAiEmbeddingFunction(
            api_key=settings.GOOGLE_API_KEY,
            model_name=settings.GEMINI_EMBEDDING_MODEL,
        )
    return embedding_functions.DefaultEmbeddingFunction()


def get_collection():
    global _collection
    if _collection is None:
        client = _get_client()
        _collection = client.get_or_create_collection(
            name=settings.CHROMA_COLLECTION_NAME,
            embedding_function=_get_embedding_function(),
            metadata={"description": "Semantic index of student bios/profiles"},
        )
    return _collection


def _student_document(student: Student) -> str:
    """Builds the text blob that gets embedded for a given student."""
    parts = [
        f"{student.first_name} {student.last_name}",
        f"Major: {student.major}" if student.major else "",
        f"Enrollment year: {student.enrollment_year}" if student.enrollment_year else "",
        f"GPA: {student.gpa}" if student.gpa is not None else "",
        student.bio or "",
    ]
    return ". ".join(p for p in parts if p)


def upsert_student(student: Student) -> None:
    """Add or update a single student's vector embedding."""
    collection = get_collection()
    collection.upsert(
        ids=[str(student.id)],
        documents=[_student_document(student)],
        metadatas=[
            {
                "student_id": student.id,
                "name": f"{student.first_name} {student.last_name}",
                "major": student.major or "",
                "email": student.email,
            }
        ],
    )


def remove_student(student_id: int) -> None:
    collection = get_collection()
    collection.delete(ids=[str(student_id)])


def sync_student_index(db: Session) -> int:
    """Rebuilds the full vector index from the current relational DB state."""
    students = db.query(Student).all()
    if not students:
        return 0
    collection = get_collection()
    collection.upsert(
        ids=[str(s.id) for s in students],
        documents=[_student_document(s) for s in students],
        metadatas=[
            {
                "student_id": s.id,
                "name": f"{s.first_name} {s.last_name}",
                "major": s.major or "",
                "email": s.email,
            }
            for s in students
        ],
    )
    return len(students)


def semantic_search_students(query: str, n_results: int = 5) -> list[dict]:
    """Returns the top-N students whose profile is semantically closest to the query."""
    collection = get_collection()
    if collection.count() == 0:
        return []
    n_results = min(n_results, collection.count())
    results = collection.query(query_texts=[query], n_results=n_results)

    hits = []
    for doc, meta, distance in zip(
        results["documents"][0], results["metadatas"][0], results["distances"][0]
    ):
        hits.append({"summary": doc, **meta, "distance": distance})
    return hits
