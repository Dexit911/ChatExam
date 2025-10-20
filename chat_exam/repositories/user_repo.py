from chat_exam.models import User, Supervision
from chat_exam.repositories import get_by, filter_by, save, delete
from chat_exam.extensions import db


def get_user_by_id(user_id: int) -> User | None:
    return get_by(User, id=user_id)


def get_user_by_email(email: str) -> User | None:
    return get_by(User, email=email)


def get_users_by_role(role: str) -> list:
    return filter_by(User, role=role)


def get_students_by_teacher(teacher_id: int) -> list:
    return (
        User.query.join(Supervision, Supervision.student_id == User.id)
        .filter(Supervision.teacher_id == teacher_id)
        .all()
    )
