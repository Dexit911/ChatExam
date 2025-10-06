from chat_exam.repositories import student_repo, teacher_repo, student_teacher_repo, save
from chat_exam.models import Student



def create_student(username: str, email: str, password: str) -> Student:
    """Create a new student and save"""
    if student_repo.get_student_by_email(email):
        raise ValueError("Email already registered")

    student = Student(username=username, email=email)
    student.set_password(password)
    return save(student)

# noinspection PyUnreachableCode
def login_student(email: str, password: str) -> Student:
    """Authenticate a student by email and password."""
    student = student_repo.get_student_by_email(email)
    if not student:
        raise ValueError("Invalid email or password")

    if not student.check_password(password):
        raise ValueError("Invalid email or password")

    return student


def assign_teacher(student_id: int, teacher_id: int) -> None:
    """Assign a student to a teacher."""
    student = student_repo.get_student_by_id(student_id)
    teacher = teacher_repo.get_teacher_by_id(teacher_id)

    if not student or not teacher:
        raise ValueError("Invalid student or teacher")

    if student_teacher_repo.exists_link(student_id, teacher_id):
        return

    student_teacher_repo.link(student_id, teacher_id)
