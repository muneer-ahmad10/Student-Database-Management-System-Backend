from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app import crud
from app.schemas.course import CourseCreate, CourseOut, CourseUpdate

router = APIRouter(prefix="/courses", tags=["Courses"])


@router.post("", response_model=CourseOut, status_code=status.HTTP_201_CREATED)
def create_course(payload: CourseCreate, db: Session = Depends(get_db)):
    """Create a new course."""
    if crud.course.get_course_by_code(db, payload.code):
        raise HTTPException(status_code=409, detail="A course with this code already exists.")
    return crud.course.create_course(db, payload)


@router.get("", response_model=list[CourseOut])
def list_courses(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    search: str | None = Query(None, description="Search by title or course code"),
    department: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """List courses with pagination, search, and department filter."""
    return crud.course.list_courses(db, skip=skip, limit=limit, search=search, department=department)


@router.get("/{course_id}", response_model=CourseOut)
def get_course(course_id: int, db: Session = Depends(get_db)):
    """Retrieve a single course by ID."""
    course = crud.course.get_course(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


@router.put("/{course_id}", response_model=CourseOut)
@router.patch("/{course_id}", response_model=CourseOut)
def update_course(course_id: int, payload: CourseUpdate, db: Session = Depends(get_db)):
    """Update a course. Supports partial updates (PATCH) or full replace (PUT)."""
    course = crud.course.get_course(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return crud.course.update_course(db, course, payload)


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course(course_id: int, db: Session = Depends(get_db)):
    """Delete a course."""
    course = crud.course.get_course(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    crud.course.delete_course(db, course)
    return None
