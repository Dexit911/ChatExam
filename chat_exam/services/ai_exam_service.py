"""
AI Exam Service
===============

Handles background generation of exam questions using AI.
Integrates with Exam and StudentExam models.
"""

# === Built-in ===
from threading import Thread
from cachetools import TTLCache
import uuid
# === Local ===
from chat_exam.utils.ai_examinator import AIExaminator
from chat_exam.utils.git_fecther import fetch_github_code

# === Create cache space ===
exam_cache = TTLCache(maxsize=100, ttl=300)


def ensure_questions_ready(student_id: int, data: dict, question_count: int):
    """
    Ensure questions exist in cache or trigger async generation.

    :param student_id: (int) id of the student to generate questions for
    :param data: (dict) files data from students gitHub repo
    :param question_count: (int) number of questions to generate on exam

    """

    existing_task = next(
        (tid for tid, data in exam_cache.items() if data.get("student_id") == student_id),
        None
    )
    if not existing_task:
        task_id = _generate_questions_async(data, question_count, student_id)
    else:
        task_id = existing_task

    data = exam_cache.get(task_id)
    if not data:
        return task_id, None, "pending"
    return task_id, data, data["status"]


def generate_verdict(data: dict, questions_dict: dict, answers_dict: dict) -> tuple[str, int]:
    """UNDER CONSTRUCTION"""
    code_string = _generate_content_string(data)

    verdict, rating = AIExaminator().create_verdict(
        code=code_string,
        questions=questions_dict,
        answers=answers_dict,
    )

    return verdict, rating


def _generate_questions_background(task_id: int, data: dict, question_count: int, student_id: int) -> None:
    """
    This function happens on individual thread. Here is AI response cached.
    :param task_id: id of the cache
    :param data: (dict) files data from gitHub repo
    :param question_count: number of questions to generate on exam
    :param student_id: id of the student to generate questions for
    """
    try:

        examinator = AIExaminator(question_count=question_count)
        content_string = _generate_content_string(data)
        questions = examinator.create_questions(content_string)

        exam_cache[str(task_id)] = {
            "status": "done",
            "questions": questions,
            "student_id": student_id,
        }
        print(f"===[ OK ] Questions ready for student: {student_id} id===")

    except Exception as e:
        exam_cache[str(task_id)] = {"status": "error", "error": str(e)}
        print(f"===[ ERROR ] Generating questions for student {student_id}: {e}===")


def _generate_questions_async(data: dict, question_count: int, student_id: int):
    """
    Starts a thread for individual question generation.
    Purpose of the thread is to prevent students wait in a line for every response.
    :param data: (dict) files data from gitHub repo
    :param question_count: number of questions to generate on exam
    :param student_id: id of the student to generate questions for
    """
    # === Generate unique task id ===
    task_id = str(uuid.uuid4())

    # === Mark status as "ongoing" for this thread ===
    exam_cache[task_id] = {"status": "pending"}

    # === Generate Thread ===
    thread = Thread(
        target=_generate_questions_background,
        args=(task_id, data, question_count, student_id),
    )
    thread.daemon = True
    thread.start()

    return task_id


def _generate_content_string(data: dict) -> str:
    """
    Makes fetched data from repo prompt ready
    :param data: filtered fetched data with student gitHub files - example:
        {
            "index.html": "<"<!DOCTYPE html> ...",
            "style.css": "body {...} ...",
        }
    """
    content_string = "Student files: "
    data = {"test1": "1", "test2": "2", "test3": "3", "test4": "4"}

    for key, value in data.items():
        content_string += f"\n{key}: {value}"

    return content_string
