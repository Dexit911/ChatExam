import logging
import re
import requests

from chat_exam.repositories import get_by_id
from chat_exam.models import Teacher, Student
from chat_exam.exceptions import ValidationError, AuthError

logger = logging.getLogger(__name__)


"""AUTH VALIDATORS"""
def validate_teacher(teacher_id: int):
    """Raises ValueError if teacher is missing or invalid."""
    if not teacher_id:
        raise AuthError("Missing teacher id ID - unauthorized request")

    teacher = get_by_id(Teacher, teacher_id)
    if not teacher:
        raise ValidationError("Invalid or non-existent teacher ID - could not find teacher in database")


def validate_student(student_id: int):
    """Raises ValueError if student is missing or invalid."""
    if not student_id:
        raise AuthError("Missing student id ID - unauthorized request")

    teacher = get_by_id(Student, student_id)
    if not teacher:
        raise ValidationError("Invalid or non-existent student ID - could not find student in database")



"""SPECIFIC VALIDATORS"""
def check_github_link(url: str) -> tuple[bool, str]:
    """
    Validate if a string is a valid GitHub link and check if it exists.
    :param url: (str) The URL of the GitHub link to CODE!.
    :return: (status (bool), message (str))
    """
    if not url:
        return False, "No link provided"

    # Regex for github.com/user/repo or deeper
    pattern = re.compile(
        r"^https:\/\/github\.com\/[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+(\/.*)?$"
    )
    if not pattern.match(url):
        return False, "Not a valid GitHub URL format"

    try:
        response = requests.head(url, allow_redirects=True, timeout=5)
        if response.status_code == 200:
            return True, "Valid and reachable"
        elif response.status_code == 404:
            return False, "GitHub link not found (404)"
        else:
            return False, f"GitHub returned {response.status_code}"
    except requests.RequestException as e:
        return False, f"Request failed: {e}"


