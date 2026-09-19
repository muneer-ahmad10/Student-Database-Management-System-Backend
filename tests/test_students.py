"""
Basic smoke tests for the Students CRUD API.

Run with: pytest -q
Uses an isolated in-memory SQLite DB so tests never touch real data.
"""
import os

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import get_db, Base


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    from app.models import student, course, enrollment  # noqa: F401
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


def test_create_and_get_student(client):
    payload = {
        "first_name": "Test",
        "last_name": "User",
        "email": "test.user@example.com",
        "major": "Computer Science",
        "enrollment_year": 2024,
        "gpa": 8.5,
    }
    resp = client.post("/api/v1/students", json=payload)
    assert resp.status_code == 201
    student_id = resp.json()["id"]

    resp2 = client.get(f"/api/v1/students/{student_id}")
    assert resp2.status_code == 200
    assert resp2.json()["email"] == "test.user@example.com"


def test_duplicate_email_rejected(client):
    payload = {"first_name": "A", "last_name": "B", "email": "dupe@example.com"}
    client.post("/api/v1/students", json=payload)
    resp = client.post("/api/v1/students", json=payload)
    assert resp.status_code == 409


def test_update_and_delete_student(client):
    payload = {"first_name": "Del", "last_name": "Ete", "email": "del.ete@example.com"}
    created = client.post("/api/v1/students", json=payload).json()

    upd = client.patch(f"/api/v1/students/{created['id']}", json={"major": "Physics"})
    assert upd.status_code == 200
    assert upd.json()["major"] == "Physics"

    delete_resp = client.delete(f"/api/v1/students/{created['id']}")
    assert delete_resp.status_code == 204

    get_resp = client.get(f"/api/v1/students/{created['id']}")
    assert get_resp.status_code == 404
