import datetime as dt
import enum

from sqlalchemy import Integer, DateTime, ForeignKey, Enum, Float, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class EnrollmentStatus(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    DROPPED = "dropped"


class Enrollment(Base):
    """Association object between Student and Course (many-to-many + extra data)."""

    __tablename__ = "enrollments"
    __table_args__ = (UniqueConstraint("student_id", "course_id", name="uq_student_course"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=False)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), nullable=False)
    status: Mapped[EnrollmentStatus] = mapped_column(
        Enum(EnrollmentStatus), default=EnrollmentStatus.ACTIVE
    )
    grade: Mapped[float | None] = mapped_column(Float, nullable=True)
    semester: Mapped[str | None] = mapped_column(nullable=True)
    enrolled_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)

    student = relationship("Student", back_populates="enrollments")
    course = relationship("Course", back_populates="enrollments")

    def __repr__(self) -> str:
        return f"<Enrollment student_id={self.student_id} course_id={self.course_id}>"
