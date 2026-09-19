from fastapi import APIRouter

from app.api.v1.endpoints import students, courses, enrollments, chatbot

api_router = APIRouter()
api_router.include_router(students.router)
api_router.include_router(courses.router)
api_router.include_router(enrollments.router)
api_router.include_router(chatbot.router)
