from chat_exam.repositories import get_by_id, get_by, delete
from typing import Optional, List
from chat_exam.models import Student, StudentTeacher


def get_student_by_email(email: str) -> Optional[Student]:
    """Return Student by email"""
    return get_by(Student, email=email)

def get_student_by_teacher(teacher_id: int) -> List[Student]:
    """Return list with Students linked to teacher"""
    return (
        Student.query.join(StudentTeacher)
        .filter(StudentTeacher.teacher_id == teacher_id)
        .all()
    )

def delete_student(student_model: Student) -> None:
    """Delete student by model"""
    return delete(student_model, auto_commit=True)




