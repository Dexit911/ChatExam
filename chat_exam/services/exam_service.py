from datetime import datetime

from chat_exam.repositories import student_repo, teacher_repo, exam_repo, save, get_by, student_teacher_repo
from chat_exam.models import Student, Teacher, StudentTeacher, StudentExam, Exam

# NOTE: SHOULD I SEPARATE COMMIT AND ADD LOGIC? DOES IT IMPROVE SPEED?

def create_attempt(student_id: int, code: str, github_link: str) -> StudentExam:
    """Create student exam attempt"""
    # Get exam by code
    exam = exam_repo.get_exam_by_code(code)
    # Look if the attempt already exists
    exists = get_by(StudentExam, student_id=student_id, exam_id=exam.id)
    if exists:
        raise ValueError("Student exam attempt already exists")
    # If not, create attempt
    attempt = StudentExam(
        student_id=student_id,
        exam_id=exam.id,
        github_link=github_link,
        status="ongoing",
    )
    # Check if student is not connected to teacher
    student_to_teacher = student_teacher_repo.exists_link(
        student_id=student_id,
        teacher_id=exam.teacher_id,
    )
    # If not link student to teacher
    if not student_to_teacher:
        student_teacher_repo.link(
            student_id=student_id,
            teacher_id=exam.teacher_id,
        )

    return save(attempt)


def create_exam(title: str, teacher_id: int, settings: dict) -> Exam:
    """
    Creates exam
    :param title: exam title
    :param teacher_id: id of teacher that is creating this exam
    :param settings: exam settings in dict format. Example:
        {
            "browserViewMode": form.browser_view_mode.data,
            "allowQuit": form.allow_quit.data,
            "allowClipboard": form.allow_clipboard.data,
        }
    :return: Exam
    """



    exam = Exam(title=title)


