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
import os
# === Built-in ===
from datetime import datetime
import json
import logging
from typing import Tuple, List
# === Add-on ===
from flask import url_for
from sqlalchemy.exc import SQLAlchemyError
# === Local ===
from chat_exam.repositories import (
    exam_repo,
    user_repo,
    supervision_repo,
    save,
    get_by,
    flush,
    get_by_id,
    delete,
    add,
    commit,
    filter_by,
)
from chat_exam.models import Attempt, Exam
from chat_exam.utils.validators import validate_user, validate_exam_ownership
from chat_exam.exceptions import ValidationError
from chat_exam.config import ATTEMPT_FILES_PATH

logger = logging.getLogger(__name__)


# === ATTEMPT SERVICES ===


def create_attempt(student_id: int, code: str, github_link: str) -> Attempt:
    """
    Create student exam attempt.
    :param student_id: id of student who attempts
    :param code: the unique code of the exam
    :param github_link: link to students gitHub code
    :return: Attempt
    """
    # === AUTH VALIDATION ===
    validate_user(student_id, "student")

    # Get exam by code
    exam = exam_repo.get_exam_by_code(code)
    # Look if the attempt already exists
    exists = get_by(Attempt, student_id=student_id, exam_id=exam.id)

    if exists:
        if exists.status == "ready":
            logger.info(f"Reusing ready attempt for student: {student_id} ID, attempt: {exists.id} ID")
            # TODO: reopen SEB config
            pass
        else:
            raise ValidationError("Student exam attempt already exists")

    # If not, create attempt
    attempt = Attempt(
        student_id=student_id,
        exam_id=exam.id,
        github_link=github_link,
        status="ongoing",
    )
    flush()
    logger.info(f"Created new attempt for student: {student_id} ID, attempt: {attempt} ID ")

    # Check if student is connected to teacher
    supervision_repo.ensure_link(
        student_id=student_id,
        teacher_id=exam.teacher_id,
    )
    logger.info(f"Linked student: {student_id} ID, to teacher {exam.teacher_id} ID")

    return save(attempt)


def delete_attempt(attempt_id: int) -> None:
    """Delete student exam attempt"""
    attempt = get_by_id(Attempt, attempt_id)
    if not attempt:
        raise ValidationError("Student exam attempt does not exist")

    return delete(attempt, auto_commit=True)


def inspect_attempt(teacher_id: int, attempt_id: int) -> dict:
    # === Auth check ===
    validate_user(teacher_id, "teacher")
    exam_id = get_by_id(Attempt, attempt_id).exam_id
    validate_exam_ownership(teacher_id, exam_id)

    attempt_data = _load_attempt_data(attempt_id)
    return attempt_data


def save_attempt_results(attempt_id: int, **kwargs) -> None:
    """
    Update and save exam results.

    :param attempt_id: (int) id of attempt

    **kwargs:
        - questions_dict (dict): All questions student were answering on the exam
        - answers_dict (dict): All answers student gave to questions
        - ai_verdict (str): Short verdict from AI how did student do on the exam
        - ai_rating (str): Rating, 1 - 5
        - files_data (dict): All code files that were used in exam.
    """

    # Get attempt by id
    attempt = get_by_id(Attempt, attempt_id)

    attempt.ai_verdict = kwargs.get("ai_verdict")
    attempt.ai_rating = kwargs.get("ai_rating")

    attempt.files_path = _save_attempt_data(
        attempt_id=attempt_id,
        file_data=kwargs.get("file_data"),
        questions_data=kwargs.get("questions_dict"),
        answers_data=kwargs.get("answers_dict"),
    )

    attempt.status = "done"

    commit()


def _save_attempt_data(attempt_id: int, file_data: dict, questions_data: dict, answers_data: dict) -> str:
    """
    Saves attempt files.

    :param attempt_id: (int) id of attempt
    :param questions_data: (dict) All questions student were answering on the exam - example:
        {
            "q1": "how long is your pipi?",
            ...
        }

    :param answers_data : (dict) All answers student gave to questions - example:
        {
            "q1": "the answer is 15",
            ...
        }

    :param file_data: (dict) with file information - example:
        {
            "index.html": "<!DOCTYPE html> ...",
            "styles.css": "body {...}...",
            ...
        }


    :return: (str) with path to file
    """

    attempt_data = {
        "content": file_data,
        "questions": questions_data,
        "answers": answers_data,
    }

    # === Path for attempt data ===
    path = f"{ATTEMPT_FILES_PATH}{attempt_id}.json"

    # === Save attempt in json format ===
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(attempt_data, f, ensure_ascii=False, indent=2)
    return path

def _load_attempt_data(attempt_id: int) -> dict:
    with open(f"{ATTEMPT_FILES_PATH}{attempt_id}.json", encoding="utf-8") as f:
        return json.load(f)


def get_attempts(teacher_id: int, exam_id: int) -> Tuple[Exam, List]:
    """Get exam and all attempts related to it"""
    #  === Auth check ===
    validate_user(teacher_id, "teacher")
    exam = validate_exam_ownership(teacher_id, exam_id)

    # === Get list of all attempt for this exam ===
    attempts = filter_by(Attempt, exam_id=exam.id)
    return exam, attempts


def set_attempt_status(attempt_id: int, status: str) -> Attempt:
    """
    Set exam status for attempt
    :param attempt_id: (int) Attempt ID
    :param status: (str) exam status. Must be one of 'ready', 'ongoing' or 'done'
    :return: Attempt
    """
    # Check if attempt exists
    attempt = get_by_id(Attempt, attempt_id)
    if not attempt:
        raise ValidationError("Invalid attempt ID - could not find attempt in database")

    attempt.status = status
    return save(attempt)


# === EXAM SERVICES ===


def create_exam(title: str, teacher_id: int, question_count: str, seb_settings: dict) -> Exam:
    """
    Creates exam.
    :param title: exam title
    :param teacher_id: id of teacher that is creating this exam
    :param question_count: question count for this exam
    :param seb_settings: exam settings in dict format. Example:
        {
            "browserViewMode": form.browser_view_mode.data,
            "allowQuit": form.allow_quit.data,
            "allowClipboard": form.allow_clipboard.data,
        }
    :return: db.Model -> Exam()
    """
    # === Auth check ===
    validate_user(teacher_id, "teacher")

    try:
        # Create empty Exam model
        exam = Exam()

        # Insert values in exam
        exam.generate_code()
        exam.title = title
        exam.teacher_id = teacher_id
        exam.seb_settings = seb_settings
        exam.question_count = question_count

        add(exam)
        flush()

        return save(exam)

    except SQLAlchemyError as e:
        raise ValueError(f"###Failed to create exam, SQLAlchemyError:\n{e}\n###")


def delete_exam(teacher_id: int, exam_id: int) -> None:
    # === Auth check ===
    validate_user(teacher_id, "teacher")
    exam = validate_exam_ownership(teacher_id, exam_id)

    # === Delete Exam ===
    delete(exam.teacher_id, exam.exam_id)


def view_exams(teacher_id: int) -> list:
    # === Auth check ===
    validate_user(teacher_id, "teacher")
    exams = filter_by(Exam, teacher_id=teacher_id)
    return exams
