from typing import Optional

from chat_exam.repositories import get_by
from chat_exam.models import Teacher

def get_teacher_by_email(email: str) -> Optional[Teacher]:
    return get_by(Teacher, email=email)



