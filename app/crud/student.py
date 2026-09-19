"""CRUD (Create, Read, Update, Delete) operations for the Student entity."""
from sqlalchemy import select, or_
from sqlalchemy.orm import Session

from app.models.student import Student
from app.schemas.student import StudentCreate, StudentUpdate


def create_student(db: Session, payload: StudentCreate) -> Student:
    student = Student(**payload.model_dump())
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


def get_student(db: Session, student_id: int) -> Student | None:
    return db.get(Student, student_id)


def get_student_by_email(db: Session, email: str) -> Student | None:
    return db.execute(select(Student).where(Student.email == email)).scalar_one_or_none()


def list_students(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    search: str | None = None,
    major: str | None = None,
    is_active: bool | None = None,
) -> list[Student]:
    stmt = select(Student)
    if search:
        like = f"%{search}%"
        stmt = stmt.where(
            or_(
                Student.first_name.ilike(like),
                Student.last_name.ilike(like),
                Student.email.ilike(like),
            )
        )
    if major:
        stmt = stmt.where(Student.major.ilike(f"%{major}%"))
    if is_active is not None:
        stmt = stmt.where(Student.is_active == is_active)

    stmt = stmt.offset(skip).limit(limit)
    return list(db.execute(stmt).scalars().all())


def count_students(db: Session) -> int:
    return db.query(Student).count()


def update_student(db: Session, student: Student, payload: StudentUpdate) -> Student:
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(student, field, value)
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


def delete_student(db: Session, student: Student) -> None:
    db.delete(student)
    db.commit()
