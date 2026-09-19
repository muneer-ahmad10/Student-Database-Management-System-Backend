import datetime as dt
from pydantic import BaseModel, EmailStr, ConfigDict, Field


class StudentBase(BaseModel):
    first_name: str = Field(..., max_length=100, examples=["Aditi"])
    last_name: str = Field(..., max_length=100, examples=["Sharma"])
    email: EmailStr = Field(..., examples=["aditi.sharma@example.com"])
    date_of_birth: dt.date | None = None
    major: str | None = Field(None, max_length=120, examples=["Computer Science"])
    enrollment_year: int | None = Field(None, ge=1900, le=2100, examples=[2023])
    gpa: float | None = Field(None, ge=0.0, le=10.0, examples=[8.7])
    bio: str | None = Field(
        None,
        description="Free-text bio/notes about the student — used for AI semantic search.",
        examples=["Enthusiastic about machine learning and robotics competitions."],
    )
    is_active: bool = True


class StudentCreate(StudentBase):
    pass


class StudentUpdate(BaseModel):
    """All fields optional — supports partial (PATCH-style) updates."""

    first_name: str | None = Field(None, max_length=100)
    last_name: str | None = Field(None, max_length=100)
    email: EmailStr | None = None
    date_of_birth: dt.date | None = None
    major: str | None = Field(None, max_length=120)
    enrollment_year: int | None = Field(None, ge=1900, le=2100)
    gpa: float | None = Field(None, ge=0.0, le=10.0)
    bio: str | None = None
    is_active: bool | None = None


class StudentOut(StudentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: dt.datetime
    updated_at: dt.datetime


class StudentWithEnrollments(StudentOut):
    model_config = ConfigDict(from_attributes=True)
    enrollments: list["EnrollmentOut"] = []


from app.schemas.enrollment import EnrollmentOut  # noqa: E402

StudentWithEnrollments.model_rebuild()
