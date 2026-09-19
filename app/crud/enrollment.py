"""CRUD operations for the Enrollment (Student <-> Course) entity."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enrollment import Enrollment
from app.schemas.enrollment import EnrollmentCreate, EnrollmentUpdate


def create_enrollment(db: Session, payload: EnrollmentCreate) -> Enrollment:
    enrollment = Enrollment(**payload.model_dump())
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    return enrollment


def get_enrollment(db: Session, enrollment_id: int) -> Enrollment | None:
    return db.get(Enrollment, enrollment_id)


def get_existing_enrollment(db: Session, student_id: int, course_id: int) -> Enrollment | None:
    stmt = select(Enrollment).where(
        Enrollment.student_id == student_id, Enrollment.course_id == course_id
    )
    return db.execute(stmt).scalar_one_or_none()


def list_enrollments(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    student_id: int | None = None,
    course_id: int | None = None,
) -> list[Enrollment]:
    stmt = select(Enrollment)
    if student_id is not None:
        stmt = stmt.where(Enrollment.student_id == student_id)
    if course_id is not None:
        stmt = stmt.where(Enrollment.course_id == course_id)
    stmt = stmt.offset(skip).limit(limit)
    return list(db.execute(stmt).scalars().all())


def update_enrollment(db: Session, enrollment: Enrollment, payload: EnrollmentUpdate) -> Enrollment:
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(enrollment, field, value)
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    return enrollment


def delete_enrollment(db: Session, enrollment: Enrollment) -> None:
    db.delete(enrollment)
    db.commit()
