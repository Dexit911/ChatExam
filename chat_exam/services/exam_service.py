from chat_exam.repositories import student_repo, teacher_repo, exam_repo, save,  get_by
from chat_exam.models import Student, Teacher, StudentTeacher, StudentExam, Exam


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

    return save(attempt)





