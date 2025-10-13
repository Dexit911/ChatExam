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


def generate_questions_background(task_id: int, github_url: str, question_count: int, student_id: int) -> None:
    """
    This function happens on individual thread. Here is AI response cached.
    :param task_id: id of the cache
    :param github_url: url of students github code
    :param question_count: number of questions to generate on exam
    :param student_id: id of the student to generate questions for
    """
    try:
        content = fetch_github_code(github_url)
        examinator = AIExaminator(question_count=question_count)
        questions = examinator.create_questions(content)

        exam_cache[str(task_id)] =  {
            "status": "done",
            "questions": questions,
            "student_id": student_id,
        }
        print(f"===[ OK ] Questions ready for student: {student_id} id===")

    except Exception as e:
        exam_cache[str(task_id)] = {"status": "error", "error": str(e)}
        print(f"===[ ERROR ] Generating questions for student {student_id}: {e}===")


def generate_questions_async(github_link: str, question_count: int, student_id: int):
    """
    Starts a thread for individual question generation.
    Purpose of the thread is to prevent students wait in a line for every response.
    :param github_link: url of students github code
    :param question_count: number of questions to generate on exam
    :param student_id: id of the student to generate questions for
    """
    # === Generate unique task id ===
    task_id  = str(uuid.uuid4())

    # === Mark status as "ongoing" for this thread ===
    exam_cache[task_id] = {"status": "pending"}

    # === Generate Thread ===
    thread = Thread(
        target=generate_questions_background,
        args=(task_id, github_link, question_count, student_id),
    )
    thread.daemon = True
    thread.start()

    return task_id


def generate_verdict(code_string: str, questions_dict: dict, answers_dict: dict) -> tuple[str, int]:

    verdict, rating = AIExaminator().create_verdict(
        code=code_string,
        questions=questions_dict,
        answers=answers_dict,
    )

    return verdict, rating





