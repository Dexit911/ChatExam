import logging
import re
import requests

from chat_exam.models import User, Exam, Attempt
from chat_exam.exceptions import AuthError
from functools import wraps
from flask import session, redirect, url_for, flash
from chat_exam.repositories import user_repo

logger = logging.getLogger(__name__)


def validate_user(user_id: int, required_role: str) -> User | None:
    """Raises ValueError if user is missing or invalid."""
    user = user_repo.get_user_by_id(user_id)
    if not user:
        raise AuthError("Missing teacher id ID - unauthorized request")
    if user.role != required_role:
        raise AuthError("Invalid or non-existent user ID - could not find user in database")
    return user


def validate_exam_ownership(teacher_id: int, exam_id: int) -> Exam | None:
    """Ensure the exam belongs to the given teacher."""
    exam = exam_repo.get_exam_by_id(exam_id)
    if not exam:
        raise ValidationError("Exam not found.")
    if exam.teacher_id != teacher_id:
        raise AuthError("You do not own this exam.")
    return exam


def role_required(required_role):
    """Restrict route to users with a specific role."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user_id = session.get("user_id")
            if not user_id:
                flash("You must be logged in.", "danger")
                return redirect(url_for("main.login"))

            user = user_repo.get_user_by_id(user_id)
            if not user or user.role != required_role:
                flash(f"Access restricted to {required_role}s.", "danger")
                return redirect(url_for("main.index"))

            return func(*args, **kwargs)

        return wrapper

    return decorator


"""SPECIFIC VALIDATORS"""


def validate_github_url(url: str) -> tuple[bool, str]:
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
