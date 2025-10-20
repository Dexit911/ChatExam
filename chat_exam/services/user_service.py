"""
Student Service
===============

Core business logic for student management in ChatExam.

Responsibilities:
- Handle student registration and authentication.
- Manage teacher-student linking through StudentTeacher relations.

This module is part of the ChatExam service layer — designed for clarity,
testability, and future scaling into API or background services.
"""

# === Local ===
from chat_exam.repositories import user_repo, supervision_repo
from chat_exam.models import User
from chat_exam.exceptions import ValidationError
from chat_exam.utils.validators import validate_user


def create_student(username: str, email: str, password: str) -> User:
    """Create a new student and save"""
    if user_repo.get_user_by_email(email):
        raise ValueError("Email already registered")

    student = User(
        username=username,
        email=email,
        password=password,
        role='student'
    )

    student.set_password(password)
    return save(student)


# noinspection PyUnreachableCode
def login_student(email: str, password: str) -> User:
    user = user_repo.get_user_by_email(email)
    if not user or user.role != "student":
        raise ValueError("Invalid email or password")
    if not user.check_password(password):
        raise ValueError("Invalid email or password")

    return user



def assign_supervision(student_id: int, teacher_id: int) -> None:
    """Link a student to a teacher (supervision)."""
    student = user_repo.get_by_id(student_id)
    teacher = user_repo.get_by_id(teacher_id)

    if not student or not teacher:
        raise ValidationError("Invalid student or teacher ID")

    if student.role != "student":
        raise ValidationError("User is not a student")

    if teacher.role != "teacher":
        raise ValidationError("User is not a teacher")

    if supervision_repo.link_exists(student_id, teacher_id):
        return

    student_teacher_repo.link(student_id, teacher_id)



# === Teacher related ===

def login_teacher(email: str, password: str) -> User:
    user = user_repo.get_user_by_email(email)
    if not user or user.role != "teacher":
        raise ValueError("Invalid email or password")
    if not user.check_password(password):
        raise ValueError("Invalid email or password")

    return user

def get_students(teacher_id: int) -> list:
    # === Auth check ===
    validate_user(teacher_id, "teacher")

    # === Get all student that belongs to this teacher ===
    students = user_repo.get_students_by_teacher(teacher_id)
    return students



