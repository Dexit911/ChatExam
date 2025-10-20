import logging
import re
import requests

from chat_exam.repositories import get_by_id
from chat_exam.repositories import user_repo
from chat_exam.models import User
from chat_exam.exceptions import ValidationError, AuthError

logger = logging.getLogger(__name__)

def validate_user(user_id: int, required_role: str) -> User:
    """Raises ValueError if user is missing or invalid."""
    user = user_repo.get_user_by_id(user_id)
    if not user:
        raise AuthError("Missing teacher id ID - unauthorized request")
    if user.role != required_role:
        raise AuthError("Invalid or non-existent user ID - could not find user in database")
    return user






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


