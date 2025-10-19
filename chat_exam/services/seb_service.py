# === Local ===
from chat_exam.models import Exam, StudentExam
from chat_exam.utils.seb_manager import Seb_manager
from chat_exam.utils.session_manager import create_temp_token
from chat_exam.utils.validators import validate_student
from chat_exam.exceptions import ValidationError, AuthError


# noinspection PyUnreachableCode
def generate_config(attempt: StudentExam, exam: Exam, student_id: int):
    """Generate seb config for student attempt"""
    validate_student(student_id)

    if not attempt:
        raise ValidationError('Student attempt not found')

    if attempt.student_id != student_id:
        raise AuthError('Student attempt id does not match')

    if not exam:
        raise ValidationError('Exam not found')

    token = create_temp_token(student_id)
    seb = Seb_manager()
    seb.generate_seb_file(
        settings=exam.settings,
        attempt_id=attempt.id,
        exam_code=exam.code,
        token=token,
        encrypt=False,
    )
