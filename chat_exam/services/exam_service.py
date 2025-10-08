"""
Exam Service
============

Core business logic for creating exams and student attempts in ChatExam.

Responsibilities:
- Create exams with generated codes and SEB configuration files.
- Manage student exam attempts and ensure teacher-student linking.
- Keep persistence and validation logic outside Flask routes.

This module is part of the ChatExam service layer — designed for clarity,
testability, and future scaling into API or background services.
"""


# === Built-in ===
from datetime import datetime
# === Add-on ===
from flask import url_for
from sqlalchemy.exc import SQLAlchemyError
# === Local ===
from chat_exam.repositories import exam_repo, save, get_by, student_teacher_repo, flush, get_by_id, delete
from chat_exam.models import StudentExam, Exam
from chat_exam.utils.seb_manager import Seb_manager

"""ATTEMPT"""
def create_attempt(student_id: int, code: str, github_link: str) -> StudentExam:
    """
    Create student exam attempt
    :param student_id: id of student who attempts
    :param code: the unique code of the exam
    :param github_link: link to students github code
    :return: StudentExam
    """
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
    student_to_teacher = student_teacher_repo.link_exists(
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


# noinspection PyUnreachableCode
def delete_attempt(attempt_id: int) -> None:
    """Delete student exam attempt"""
    attempt = get_by_id(StudentExam, attempt_id)
    if not attempt:
        raise ValueError("Student exam attempt does not exist")

    return delete(attempt, auto_commit=True)

def get_attempt_data():
    pass

def save_attempt_results():
    pass

"""CREATE EXAM"""
def create_exam(title: str, teacher_id: int, question_count: str, settings: dict) -> Exam:
    """
    Creates Exam
    :param title: Exam title
    :param teacher_id: id of teacher that is creating this exam
    :param question_count: question count for this exam
    :param settings: Exam settings in dict format. Example:
        {
            "browserViewMode": form.browser_view_mode.data,
            "allowQuit": form.allow_quit.data,
            "allowClipboard": form.allow_clipboard.data,
        }
    :return: db.Model -> Exam()
    """

    try:
        # Create empty Exam model
        exam = Exam()
        flush()

        # Insert values in exam
        exam.generate_code()
        exam.title = title
        exam.teacher_id = teacher_id
        exam.settings = settings
        exam.date = datetime.now()
        exam.question_count = question_count

        # Create exam.seb file
        exam_url = create_exam_url(exam.code)
        create_exam_file(
            exam_id=exam.id,
            exam_url=exam_url,
            settings=settings,
        )

        return save(exam)

    except SQLAlchemyError as e:
        raise ValueError(f"###Failed to create exam, SQLAlchemyError:\n{e}\n###")





def create_exam_url(code: int) -> str:
    """
    Create exam url
    :param code: exam code (int)
    :return: exam url (str)
    """

    return url_for("student.exam", code=code, _external=True)


def create_exam_file(exam_id: int, exam_url: str, settings: dict) -> None:
    """
    Create exam.seb file. When is starts - person goes in seb kiosk env
    :param exam_id: id of exam that is going to be created
    :param exam_url: url to exam page
    :param settings: settings in dict format.
    """
    # Create xml config string
    seb_config_str = Seb_manager().create_config(
        settings=settings,
        exam_url=exam_url,
    )

    # Save .seb exam file
    Seb_manager().save_configuration_file(
        xml_str=seb_config_str,
        exam_id=exam_id,
        encrypt=False,
    )
