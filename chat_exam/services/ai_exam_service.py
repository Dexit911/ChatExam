"""
AI Exam Service
===============

Core logic for AI examinator management.

Responsibilities:
- Handle fetching for exam content
-



"""

from threading import Thread

from chat_exam.utils import git_fecther
from chat_exam.utils.ai_examinator import AIExaminator
from chat_exam.utils.git_fecther import fetch_github_code


def generate_questions_background(url: str, question_count: int, student_id: int):
    """Runs in the background — slow AI work happens here."""
    content = fetch_github_code(url)
    examinator = AIExaminator(question_count=question_count)
    questions = examinator.create_questions(content)


    print(f"✅ Questions ready for student {student_id}")

def generate_questions_async(url: str, question_count: int, student_id: int):
    """Starts a single thread for the background generation."""
    thread = Thread(target=generate_questions_background, args=(url, question_count, student_id))
    thread.daemon = True   # closes automatically if server stops
    thread.start()