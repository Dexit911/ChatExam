# === Local ===
from chat_exam.models import Exam, Attempt
from chat_exam.utils.seb_manager import Seb_manager
from chat_exam.utils.session_manager import create_temp_token
from chat_exam.utils.validators import validate_user
from chat_exam.exceptions import ValidationError, AuthError
from chat_exam.utils  import session_manager as sm
import chat_exam.repositories as repo



# noinspection PyUnreachableCode
def generate_config(attempt: Attempt, exam: Exam, student_id: int) -> None:
    """Generate seb config for student attempt"""
    validate_user(student_id, "student")

    if not attempt:
        raise ValidationError('Student attempt not found')

    if attempt.student_id != student_id:
        raise AuthError('Student attempt id does not match')

    if not exam:
        raise ValidationError('Exam not found')

    token = create_temp_token(student_id)
    seb = Seb_manager()
    seb.generate_seb_file(
        settings=exam.seb_settings,
        attempt_id=attempt.id,
        exam_code=exam.code,
        token=token,
        encrypt=False,
    )

def validate_seb_access(attempt_id: int, token: str | None, user_id: int | None):
    """"""
    attempt = repo.get_by_id(Attempt, attempt_id)
    if not attempt:
        raise ValidationError("Exam attempt not found.")

    if token:
        uid = sm.validate_temp_token(token)
        if uid != attempt.student_id:
            raise AuthError("Unauthorized attempt access.", public=True)
    elif not user_id or user_id != attempt.student_id:
        raise AuthError("Unauthorized attempt access.", public=True)

    return attempt
