"""
Teacher Service
===============

Core business logic for managing teachers in ChatExam.

Responsibilities:
- Handle student registration and authentication.

This module is part of the ChatExam service layer — designed for clarity,
testability, and future scaling into API or background services.

"""

# === Local ===
from chat_exam.repositories import teacher_repo, save
from chat_exam.models import Teacher


def create_teacher(username: str, email: str, password: str) -> Teacher:
    """Create a new teacher"""
    if teacher_repo.get_teacher_by_email(email):
        raise ValueError('Teacher already exists')

    teacher = Teacher(username=username, email=email)
    teacher.set_password(password)
    return save(teacher)

# noinspection PyUnreachableCode
def login_teacher(email: str, password: str) -> Teacher:
    """Authenticate a teacher by email and password."""
    teacher = teacher_repo.get_teacher_by_email(email)
    if not teacher:
        raise ValueError("Invalid email or password")

    if not teacher.check_password(password):
        raise ValueError("Invalid email or password")

    return teacher


