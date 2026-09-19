from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app import crud
from app.schemas.enrollment import EnrollmentCreate, EnrollmentOut, EnrollmentUpdate

router = APIRouter(prefix="/enrollments", tags=["Enrollments"])


@router.post("", response_model=EnrollmentOut, status_code=status.HTTP_201_CREATED)
def create_enrollment(payload: EnrollmentCreate, db: Session = Depends(get_db)):
    """Enroll a student in a course."""
    if not crud.student.get_student(db, payload.student_id):
        raise HTTPException(status_code=404, detail="Student not found")
    if not crud.course.get_course(db, payload.course_id):
        raise HTTPException(status_code=404, detail="Course not found")
    if crud.enrollment.get_existing_enrollment(db, payload.student_id, payload.course_id):
        raise HTTPException(status_code=409, detail="Student is already enrolled in this course.")
    return crud.enrollment.create_enrollment(db, payload)


@router.get("", response_model=list[EnrollmentOut])
def list_enrollments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    student_id: int | None = Query(None),
    course_id: int | None = Query(None),
    db: Session = Depends(get_db),
):
    """List enrollments, optionally filtered by student or course."""
    return crud.enrollment.list_enrollments(
        db, skip=skip, limit=limit, student_id=student_id, course_id=course_id
    )


@router.get("/{enrollment_id}", response_model=EnrollmentOut)
def get_enrollment(enrollment_id: int, db: Session = Depends(get_db)):
    """Retrieve a single enrollment record."""
    enrollment = crud.enrollment.get_enrollment(db, enrollment_id)
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    return enrollment


@router.put("/{enrollment_id}", response_model=EnrollmentOut)
@router.patch("/{enrollment_id}", response_model=EnrollmentOut)
def update_enrollment(enrollment_id: int, payload: EnrollmentUpdate, db: Session = Depends(get_db)):
    """Update an enrollment (e.g. change status or record a grade)."""
    enrollment = crud.enrollment.get_enrollment(db, enrollment_id)
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    return crud.enrollment.update_enrollment(db, enrollment, payload)


@router.delete("/{enrollment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_enrollment(enrollment_id: int, db: Session = Depends(get_db)):
    """Remove a student's enrollment from a course."""
    enrollment = crud.enrollment.get_enrollment(db, enrollment_id)
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    crud.enrollment.delete_enrollment(db, enrollment)
    return None
