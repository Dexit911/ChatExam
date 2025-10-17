import logging
from typing import Optional


from chat_exam.repositories import get_by, get_by_id, save
from chat_exam.models import Exam, StudentExam
from chat_exam.exceptions import ValidationError

logger = logging.getLogger(__name__)


def get_exam_by_code(code: str) -> Optional[Exam]:
    """Get exam by code"""
    return get_by(Exam, code=code)

