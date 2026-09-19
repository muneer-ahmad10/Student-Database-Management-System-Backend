import datetime as dt
from pydantic import BaseModel, ConfigDict, Field

from app.models.enrollment import EnrollmentStatus


class EnrollmentBase(BaseModel):
    student_id: int
    course_id: int
    status: EnrollmentStatus = EnrollmentStatus.ACTIVE
    grade: float | None = Field(None, ge=0.0, le=10.0)
    semester: str | None = Field(None, examples=["Fall 2026"])


class EnrollmentCreate(EnrollmentBase):
    pass


class EnrollmentUpdate(BaseModel):
    status: EnrollmentStatus | None = None
    grade: float | None = Field(None, ge=0.0, le=10.0)
    semester: str | None = None


class EnrollmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    course_id: int
    status: EnrollmentStatus
    grade: float | None
    semester: str | None
    enrolled_at: dt.datetime
