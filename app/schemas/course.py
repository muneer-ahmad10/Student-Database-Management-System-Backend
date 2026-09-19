import datetime as dt
from pydantic import BaseModel, ConfigDict, Field


class CourseBase(BaseModel):
    code: str = Field(..., max_length=20, examples=["CS101"])
    title: str = Field(..., max_length=200, examples=["Introduction to Computer Science"])
    description: str | None = Field(None, max_length=1000)
    credits: int = Field(3, ge=0, le=20)
    department: str | None = Field(None, max_length=120, examples=["Computer Science"])
    instructor: str | None = Field(None, max_length=150, examples=["Dr. Rao"])


class CourseCreate(CourseBase):
    pass


class CourseUpdate(BaseModel):
    code: str | None = Field(None, max_length=20)
    title: str | None = Field(None, max_length=200)
    description: str | None = Field(None, max_length=1000)
    credits: int | None = Field(None, ge=0, le=20)
    department: str | None = Field(None, max_length=120)
    instructor: str | None = Field(None, max_length=150)


class CourseOut(CourseBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: dt.datetime
    updated_at: dt.datetime
