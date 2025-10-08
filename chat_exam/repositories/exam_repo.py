from typing import Optional

from chat_exam.repositories import get_by
from chat_exam.models import Exam, StudentExam


def get_exam_by_code(code: str) -> Optional[Exam]:
    """Get exam by code"""
    return get_by(Exam, code=code)