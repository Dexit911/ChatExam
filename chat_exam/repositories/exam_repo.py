from chat_exam.models import Exam
from chat_exam.repositories import get_by_id, get_by, filter_by, save, delete

def get_exam_by_id(exam_id) -> Exam | None:
    return get_by_id(Exam, exam_id)

def get_exam_by_code(code) -> Exam | None:
    return get_by(Exam, code=code)
