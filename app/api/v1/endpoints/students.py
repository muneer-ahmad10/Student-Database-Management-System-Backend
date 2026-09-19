from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app import crud
from app.schemas.student import StudentCreate, StudentOut, StudentUpdate, StudentWithEnrollments

router = APIRouter(prefix="/students", tags=["Students"])


@router.post("", response_model=StudentOut, status_code=status.HTTP_201_CREATED)
def create_student(payload: StudentCreate, db: Session = Depends(get_db)):
    """Create a new student record."""
    if crud.student.get_student_by_email(db, payload.email):
        raise HTTPException(status_code=409, detail="A student with this email already exists.")
    return crud.student.create_student(db, payload)


@router.get("", response_model=list[StudentOut])
def list_students(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    search: str | None = Query(None, description="Search by first name, last name, or email"),
    major: str | None = Query(None),
    is_active: bool | None = Query(None),
    db: Session = Depends(get_db),
):
    """List students with pagination, search, and filters."""
    return crud.student.list_students(
        db, skip=skip, limit=limit, search=search, major=major, is_active=is_active
    )


@router.get("/{student_id}", response_model=StudentWithEnrollments)
def get_student(student_id: int, db: Session = Depends(get_db)):
    """Retrieve a single student by ID, including their enrollments."""
    student = crud.student.get_student(db, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


@router.put("/{student_id}", response_model=StudentOut)
@router.patch("/{student_id}", response_model=StudentOut)
def update_student(student_id: int, payload: StudentUpdate, db: Session = Depends(get_db)):
    """Update a student. Supports partial updates (PATCH) or full replace (PUT)."""
    student = crud.student.get_student(db, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    if payload.email and payload.email != student.email:
        existing = crud.student.get_student_by_email(db, payload.email)
        if existing:
            raise HTTPException(status_code=409, detail="Email already in use by another student.")

    return crud.student.update_student(db, student, payload)


@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student(student_id: int, db: Session = Depends(get_db)):
    """Delete a student record."""
    student = crud.student.get_student(db, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    crud.student.delete_student(db, student)
    return None
