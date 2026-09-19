"""
Seed the database with sample students, courses, and enrollments so the API
and chatbot have something meaningful to query out of the box.

Usage:
    python seed_data.py
"""
from app.database import SessionLocal, init_db
from app.models.student import Student
from app.models.course import Course
from app.models.enrollment import Enrollment, EnrollmentStatus

STUDENTS = [
    dict(
        first_name="Aditi", last_name="Sharma", email="aditi.sharma@example.com",
        major="Computer Science", enrollment_year=2023, gpa=8.7,
        bio="Passionate about machine learning, robotics competitions, and open-source projects.",
    ),
    dict(
        first_name="Rahul", last_name="Verma", email="rahul.verma@example.com",
        major="Electrical Engineering", enrollment_year=2022, gpa=7.9,
        bio="Interested in embedded systems and renewable energy hardware design.",
    ),
    dict(
        first_name="Meera", last_name="Nair", email="meera.nair@example.com",
        major="Computer Science", enrollment_year=2024, gpa=9.1,
        bio="Focused on natural language processing and building AI chatbots.",
    ),
    dict(
        first_name="Karan", last_name="Patel", email="karan.patel@example.com",
        major="Business Administration", enrollment_year=2023, gpa=8.0,
        bio="Enjoys entrepreneurship, finance case competitions, and marketing analytics.",
    ),
    dict(
        first_name="Sara", last_name="Khan", email="sara.khan@example.com",
        major="Computer Science", enrollment_year=2021, gpa=8.4,
        bio="Works on computer vision projects and volunteers teaching kids to code.",
    ),
]

COURSES = [
    dict(code="CS101", title="Introduction to Computer Science", credits=4,
         department="Computer Science", instructor="Dr. Rao"),
    dict(code="CS305", title="Machine Learning", credits=4,
         department="Computer Science", instructor="Dr. Iyer"),
    dict(code="EE210", title="Embedded Systems Design", credits=3,
         department="Electrical Engineering", instructor="Dr. Menon"),
    dict(code="BUS150", title="Principles of Marketing", credits=3,
         department="Business Administration", instructor="Prof. D'Souza"),
]


def run():
    init_db()
    db = SessionLocal()
    try:
        if db.query(Student).count() > 0:
            print("Database already has data — skipping seed.")
            return

        students = [Student(**s) for s in STUDENTS]
        courses = [Course(**c) for c in COURSES]
        db.add_all(students)
        db.add_all(courses)
        db.commit()
        for s in students:
            db.refresh(s)
        for c in courses:
            db.refresh(c)

        enrollments = [
            Enrollment(student_id=students[0].id, course_id=courses[0].id,
                       status=EnrollmentStatus.COMPLETED, grade=9.2, semester="Fall 2023"),
            Enrollment(student_id=students[0].id, course_id=courses[1].id,
                       status=EnrollmentStatus.ACTIVE, semester="Spring 2026"),
            Enrollment(student_id=students[2].id, course_id=courses[1].id,
                       status=EnrollmentStatus.ACTIVE, semester="Spring 2026"),
            Enrollment(student_id=students[1].id, course_id=courses[2].id,
                       status=EnrollmentStatus.COMPLETED, grade=8.5, semester="Fall 2023"),
            Enrollment(student_id=students[3].id, course_id=courses[3].id,
                       status=EnrollmentStatus.ACTIVE, semester="Spring 2026"),
            Enrollment(student_id=students[4].id, course_id=courses[1].id,
                       status=EnrollmentStatus.COMPLETED, grade=9.0, semester="Fall 2023"),
        ]
        db.add_all(enrollments)
        db.commit()

        print(f"Seeded {len(students)} students, {len(courses)} courses, {len(enrollments)} enrollments.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
