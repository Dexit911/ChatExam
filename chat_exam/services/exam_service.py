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
import json
import logging
# === Add-on ===
from flask import url_for
from sqlalchemy.exc import SQLAlchemyError
# === Local ===
from chat_exam.repositories import (
    exam_repo,
    save,
    get_by,
    student_teacher_repo,
    flush,
    get_by_id,
    delete,
    add,
    commit
)
from chat_exam.models import StudentExam, Exam
from chat_exam.utils.seb_manager import Seb_manager
from chat_exam.exceptions import ValidationError
from chat_exam.utils.validators import validate_student

logger = logging.getLogger(__name__)

"""ATTEMPT"""


def create_attempt(student_id: int, code: str, github_link: str) -> StudentExam:
    """
    Create student exam attempt.
    :param student_id: id of student who attempts
    :param code: the unique code of the exam
    :param github_link: link to students github code
    :return: StudentExam
    """
    # === AUTH VALIDATION ===
    validate_student(student_id)

    # Get exam by code
    exam = exam_repo.get_exam_by_code(code)
    # Look if the attempt already exists
    exists = get_by(StudentExam, student_id=student_id, exam_id=exam.id)

    if exists:
        if exists.status == "ready":
            logger.info(f"Reusing ready attempt for student: {student_id} ID, attempt: {exists.id} ID")
            # TODO: reopen SEB config
            pass
        else:
            raise ValidationError("Student exam attempt already exists")

    # If not, create attempt
    attempt = StudentExam(
        student_id=student_id,
        exam_id=exam.id,
        github_link=github_link,
        status="ongoing",
    )
    flush()
    logger.info(f"Created new attempt for student: {student_id} ID, attempt: {attempt} ID ")

    # Check if student is connected to teacher
    student_teacher_repo.ensure_link(
        student_id=student_id,
        teacher_id=exam.teacher_id,
    )
    logger.info(f"Linked student: {student_id} ID, to teacher {exam.teacher_id} ID")

    return save(attempt)


def open_attempt(student_id: int, code: str) -> StudentExam:
    pass


def set_attempt_status(attempt_id: StudentExam, status: str) -> StudentExam:
    """
    Set exam status for attempt
    :param attempt_id: (int) StudentExam ID
    :param status: (str) exam status. Must be one of 'ready', 'ongoing' or 'done'
    :return: StudentExam
    """
    # Check if attempt exists
    attempt = get_by_id(StudentExam, attempt_id)
    if not attempt:
        raise ValidationError("Invalid attempt ID - could not find attempt in database")

    attempt.status = status
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


def save_attempt_results(attempt_id: int, **kwargs):
    """
    Update and save exam results.

    :param attempt_id: (int) id of attempt

    **kwargs:
        - questions_dict (dict): All questions student were answering on the exam
        - answers_dict (dict): All answers student gave to questions
        - code_string (str): student provided code
        - ai_verdict (str): Short verdict from AI how did student do on the exam
        - ai_rating (str): Rating, 1 - 5
    """

    # Get attempt by id
    attempt = get_by_id(StudentExam, attempt_id)

    attempt.questions_json = json.dumps(kwargs.get("questions_dict"))
    attempt.answers_json = json.dumps(kwargs.get("answers_dict"))
    attempt.code = kwargs.get("code_string")
    attempt.ai_verdict = kwargs.get("ai_verdict")
    attempt.ai_rating = kwargs.get("ai_rating")

    attempt.ai_conversation = ""
    attempt.status = "done"

    commit()


"""CREATE EXAM"""


def create_exam(title: str, teacher_id: int, question_count: str, settings: dict) -> Exam:
    """
    Creates exam.
    :param title: exam title
    :param teacher_id: id of teacher that is creating this exam
    :param question_count: question count for this exam
    :param settings: exam settings in dict format. Example:
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

        # Insert values in exam
        exam.generate_code()
        exam.title = title
        exam.teacher_id = teacher_id
        exam.settings = settings
        exam.date = datetime.now()
        exam.question_count = question_count

        add(exam)
        flush()

        return save(exam)

    except SQLAlchemyError as e:
        raise ValueError(f"###Failed to create exam, SQLAlchemyError:\n{e}\n###")
