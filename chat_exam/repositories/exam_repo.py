from typing import Optional

from chat_exam.repositories import save, delete, get_by_id, get_by
from chat_exam.models import Teacher, Student, StudentTeacher, Exam


def get_exam_by_code(code: str) -> Optional[Exam]:
    """Get exam by code"""
    return get_by(Exam, code=code)
