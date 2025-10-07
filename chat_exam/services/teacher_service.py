from chat_exam.repositories import student_repo, teacher_repo, save
from chat_exam.models import Teacher, Student
from chat_exam.utils import security

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


