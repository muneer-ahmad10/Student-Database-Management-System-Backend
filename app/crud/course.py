"""CRUD operations for the Course entity."""
from sqlalchemy import select, or_
from sqlalchemy.orm import Session

from app.models.course import Course
from app.schemas.course import CourseCreate, CourseUpdate


def create_course(db: Session, payload: CourseCreate) -> Course:
    course = Course(**payload.model_dump())
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


def get_course(db: Session, course_id: int) -> Course | None:
    return db.get(Course, course_id)


def get_course_by_code(db: Session, code: str) -> Course | None:
    return db.execute(select(Course).where(Course.code == code)).scalar_one_or_none()


def list_courses(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    search: str | None = None,
    department: str | None = None,
) -> list[Course]:
    stmt = select(Course)
    if search:
        like = f"%{search}%"
        stmt = stmt.where(or_(Course.title.ilike(like), Course.code.ilike(like)))
    if department:
        stmt = stmt.where(Course.department.ilike(f"%{department}%"))
    stmt = stmt.offset(skip).limit(limit)
    return list(db.execute(stmt).scalars().all())


def update_course(db: Session, course: Course, payload: CourseUpdate) -> Course:
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(course, field, value)
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


def delete_course(db: Session, course: Course) -> None:
    db.delete(course)
    db.commit()
