"""
Tools exposed to the LangGraph chatbot agent.

Each tool opens its own short-lived DB session (rather than sharing FastAPI's
request-scoped session) since tool calls happen inside the LangGraph runtime,
independent of any single HTTP request lifecycle.

All tools are strictly READ-oriented against the student database, by design:
the chatbot is a query/reporting assistant, not a mutation path. This keeps
the "AI touches the database" surface area safe and auditable.
"""
from __future__ import annotations

from langchain_core.tools import tool

from app.database import SessionLocal
from app.models.student import Student
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.chatbot.vector_store import semantic_search_students


@tool
def list_students_tool(search: str = "", major: str = "", limit: int = 10) -> str:
    """
    List students from the database, optionally filtering by a name/email
    substring (`search`) and/or a `major`. Returns up to `limit` results.
    Use this for questions like "who are the CS students" or "find students
    named Rao".
    """
    db = SessionLocal()
    try:
        query = db.query(Student)
        if search:
            like = f"%{search}%"
            query = query.filter(
                (Student.first_name.ilike(like))
                | (Student.last_name.ilike(like))
                | (Student.email.ilike(like))
            )
        if major:
            query = query.filter(Student.major.ilike(f"%{major}%"))
        students = query.limit(limit).all()
        if not students:
            return "No students found matching that criteria."
        lines = [
            f"- ID {s.id}: {s.first_name} {s.last_name} | major={s.major} | "
            f"year={s.enrollment_year} | gpa={s.gpa} | email={s.email}"
            for s in students
        ]
        return "\n".join(lines)
    finally:
        db.close()


@tool
def get_student_detail_tool(student_id: int) -> str:
    """
    Get full details for one student by their numeric ID, including every
    course they are enrolled in and their grade/status in each.
    """
    db = SessionLocal()
    try:
        student = db.get(Student, student_id)
        if not student:
            return f"No student found with ID {student_id}."
        lines = [
            f"Student {student.id}: {student.first_name} {student.last_name}",
            f"Email: {student.email}",
            f"Major: {student.major}, Enrollment year: {student.enrollment_year}, GPA: {student.gpa}",
            f"Bio: {student.bio or 'N/A'}",
            "Enrollments:",
        ]
        if not student.enrollments:
            lines.append("  (not enrolled in any courses)")
        for e in student.enrollments:
            course = db.get(Course, e.course_id)
            course_label = f"{course.code} - {course.title}" if course else f"course_id={e.course_id}"
            lines.append(
                f"  - {course_label} | status={e.status.value} | grade={e.grade} | semester={e.semester}"
            )
        return "\n".join(lines)
    finally:
        db.close()


@tool
def list_courses_tool(search: str = "", department: str = "", limit: int = 10) -> str:
    """
    List courses, optionally filtered by a title/code substring (`search`)
    and/or `department`. Use this for questions like "what CS courses exist".
    """
    db = SessionLocal()
    try:
        query = db.query(Course)
        if search:
            like = f"%{search}%"
            query = query.filter((Course.title.ilike(like)) | (Course.code.ilike(like)))
        if department:
            query = query.filter(Course.department.ilike(f"%{department}%"))
        courses = query.limit(limit).all()
        if not courses:
            return "No courses found matching that criteria."
        lines = [
            f"- {c.code}: {c.title} | dept={c.department} | credits={c.credits} | instructor={c.instructor}"
            for c in courses
        ]
        return "\n".join(lines)
    finally:
        db.close()


@tool
def get_course_roster_tool(course_code: str) -> str:
    """
    Get the full roster (enrolled students and grades) for a course, given
    its course code (e.g. "CS101").
    """
    db = SessionLocal()
    try:
        course = db.query(Course).filter(Course.code.ilike(course_code)).first()
        if not course:
            return f"No course found with code '{course_code}'."
        enrollments = db.query(Enrollment).filter(Enrollment.course_id == course.id).all()
        if not enrollments:
            return f"{course.code} - {course.title} currently has no enrolled students."
        lines = [f"Roster for {course.code} - {course.title}:"]
        for e in enrollments:
            student = db.get(Student, e.student_id)
            name = f"{student.first_name} {student.last_name}" if student else f"student_id={e.student_id}"
            lines.append(f"  - {name} | status={e.status.value} | grade={e.grade}")
        return "\n".join(lines)
    finally:
        db.close()


@tool
def semantic_student_search_tool(query: str, n_results: int = 5) -> str:
    """
    Semantically search student bios/profiles using the vector database for
    fuzzy, meaning-based questions the SQL tools can't answer well, e.g.
    "which students are interested in robotics or AI research".
    This does NOT do exact keyword matching — use list_students_tool for that.
    """
    hits = semantic_search_students(query, n_results=n_results)
    if not hits:
        return (
            "The semantic student index is empty. Call the /api/v1/chatbot/reindex "
            "endpoint first to build it from current student bios."
        )
    lines = ["Closest-matching students:"]
    for h in hits:
        lines.append(
            f"- {h['name']} (student_id={h['student_id']}, major={h['major']}, "
            f"similarity_distance={h['distance']:.3f}): {h['summary']}"
        )
    return "\n".join(lines)


@tool
def database_stats_tool() -> str:
    """Get high-level counts: total students, total courses, total enrollments."""
    db = SessionLocal()
    try:
        return (
            f"Students: {db.query(Student).count()}, "
            f"Courses: {db.query(Course).count()}, "
            f"Enrollments: {db.query(Enrollment).count()}"
        )
    finally:
        db.close()


ALL_TOOLS = [
    list_students_tool,
    get_student_detail_tool,
    list_courses_tool,
    get_course_roster_tool,
    semantic_student_search_tool,
    database_stats_tool,
]
