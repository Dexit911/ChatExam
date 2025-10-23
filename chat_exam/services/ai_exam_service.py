"""
AI Exam Service
===============

Handles background generation of exam questions and verdicts using AI.
Integrates with Exam and StudentExam models.
"""

# === Built-in ===
from threading import Thread, Lock
from cachetools import TTLCache
import uuid
import logging

# === Local ===
from chat_exam.utils.ai_examinator import AIExaminator
from chat_exam.utils.git_fecther import fetch_github_code

logger = logging.getLogger(__name__)


# === Shared in-memory cache ===
exam_cache = TTLCache(maxsize=100, ttl=300)

# === Locks ===
_question_lock = Lock()
_verdict_lock = Lock()


# === QUESTIONS ===


def ensure_questions_ready(user_id: int, file_data: dict, question_count: int):
    """
    Ensure questions exist in cache or trigger async generation.
    """
    existing_task = next(
        (tid for tid, entry in exam_cache.items()
         if entry.get("user_id") == user_id
         and entry.get("type") == "question"
         ),
        None
    )

    if not existing_task:
        task_id = _generate_questions_async(user_id, file_data, question_count)
    else:
        task_id = existing_task


    # === race safe cache write/read ===
    with _qustion_lock:
        cache_entry = exam_cache.get(task_id)

    # === If no cache with given id, return nothing with status pending ===
    if not cache_entry:
        return task_id, None, "pending"
    return task_id, cache_entry, cache_entry["status"]


def _generate_questions_async(user_id: int, file_data: dict, question_count: int) -> str:
    """Starts a background thread for generating AI exam questions."""
    task_id = str(uuid.uuid4())

    # === Race safe cache write/read ===
    with _qustion_lock:
        exam_cache[task_id] = {"status": "pending"}

    # === Create a thread for question generation ===
    thread = Thread(
        target=_generate_questions_background,
        args=(task_id, user_id, file_data, question_count),
        daemon=True
    )
    thread.start()

    logger.info(f"[THREAD] Started question generation for user_id={user_id}")
    return task_id


def _generate_questions_background(task_id: str, user_id: int, file_data: dict, question_count: int):
    """Runs in a background thread to generate questions."""
    try:
        examinator = AIExaminator(question_count=question_count)
        content_string = _generate_content_string(file_data)
        questions = examinator.create_questions(content_string)

        # === Race safe cache write/read ===
        with _qustion_lock:
            exam_cache[task_id] = {
                "type": "question",
                "status": "done",
                "questions": questions,
                "user_id": user_id,
            }

        logger.info(f"[QUESTIONS] Done for user_id={user_id}")

    except Exception as e:
        # === Race safe cache write/read ===
        with _qustion_lock:
            exam_cache[task_id] = {"status": "error", "error": str(e)}

        logger.error(f"[QUESTIONS] Failed for user_id={user_id}: {e}")



# === VERDICT ===


def ensure_verdict_ready(user_id: int, file_data: dict, question_data: dict, answer_data: dict):
    """
    Ensure verdict is ready or trigger async generation.
    """
    existing_task = next(
        (tid for tid, entry in exam_cache.items()
         if entry.get("user_id") == user_id
         and entry.get("type") == "verdict"
         ),
        None
    )

    if not existing_task:
        task_id = _generate_verdict_async(user_id, file_data, question_data, answer_data)
    else:
        task_id = existing_task

    # === race safe cache write/read ===
    with _verdict_lock:
        cache_entry = exam_cache.get(task_id)

    if not cache_entry:
        return task_id, None, "pending"

    return task_id, cache_entry, cache_entry["status"]


def _generate_verdict_async(user_id: int, file_data: dict, question_data: dict, answer_data: dict) -> str:
    """Starts a background thread for AI verdict generation."""
    task_id = str(uuid.uuid4())

    # === Race safe cache write/read ===
    with _verdict_lock:
        exam_cache[task_id] = {"status": "pending"}

    thread = Thread(
        target=_generate_verdict_background,
        args=(task_id, user_id, file_data, question_data, answer_data),
        daemon=True
    )
    thread.start()

    logger.info(f"[THREAD] Started verdict generation for user_id={user_id}")
    return task_id


def _generate_verdict_background(task_id: str, user_id: int, file_data: dict, question_data: dict, answer_data: dict):
    """Runs in a background thread to generate AI verdict."""
    try:
        verdict, rating = AIExaminator().create_verdict(
            code=_generate_content_string(file_data),
            questions=question_data,
            answers=answer_data,
        )
        # === Race safe cache write/read ===
        with _verdict_lock:
            exam_cache[task_id] = {
                "type": "verdict",
                "status": "done",
                "verdict": verdict,
                "rating": rating,
                "user_id": user_id,
            }
        logger.info(f"[VERDICT] Done for user_id={user_id}")

    except Exception as e:
        # === Race safe cache write/read ===
        with _verdict_lock:
            exam_cache[task_id] = {"status": "error", "error": str(e)}

        logger.error(f"[VERDICT] Failed for user_id={user_id}: {e}")



# === UTILS ===


def _generate_content_string(file_data: dict) -> str:
    """Convert student's repo files into a single string for AI prompts."""
    content_string = "Student files:\n"
    for filename, code in file_data.items():
        content_string += f"\n{filename}:\n{code}\n"
    return content_string
