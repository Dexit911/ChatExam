import itsdangerous

from flask import session, abort

import chat_exam.repositories as repo
from chat_exam.config import Config
from chat_exam.models import UsedToken
from chat_exam.exceptions import AuthError

serializer = itsdangerous.URLSafeTimedSerializer(Config.SECRET_KEY)


def end_session():
    """Clear the current session."""
    session.clear()


def start_session(user_id: int, role: str) -> None:
    """
    Start a new session.
    :param user_id: The primary key in database of the registered user.
    :param role: The role of the student.
    :raises ValueError: If role does not recognized.
    """
    session.clear()
    session['role'] = role
    session['user_id'] = user_id


def current_id(strict: bool = True) -> int | None:
    """Get current user's id."""
    user_id = session.get("user_id")
    if strict and not user_id:
        abort(403)
    return user_id


def current_role():
    """Get current user's role."""
    return session.get("role")


def create_temp_token(user_id: int) -> str:
    """Create short-lived token (valid 5 min) for student auto-login."""
    return serializer.dumps({"user_id": user_id})


def validate_temp_token(token, max_age=300):
    """Decode token and return student_id if valid."""
    data = serializer.loads(token, max_age=max_age)
    return data["user_id"]


def ensure_student_session(token: str | None) -> int:
    """Validate SEB token or use active session. Returns student_id."""
    if token:
        student_id = validate_temp_token(token)
        start_session(user_id=student_id, role="student")
    if not current_id():
        raise AuthError("You must be logged in as a student.", public=True)
    return current_id()


"""def validate_temp_token(token, max_age=300) -> int:
    Decode token and return user_id if valid, else raise AuthError.
    try:
        #  === Check if token already used ===
        if repo.filter_by(UsedToken, token=token):
            raise AuthError("Token already used", public=True)

        # === Validate signature and expiry ===
        data = serializer.loads(token, max_age=max_age)
        user_id = data["user_id"]

        # === Mark as used ===
        repo.commit(UsedToken(token=token))

        return user_id

    except Exception:
        raise AuthError("Invalid or expired token.", public=True)


# FOR STUDENT SEB ENV
def ensure_student_session(token: str | None) -> int:
    Validate SEB token or use active session. Returns user_id for a student.
    if token:
        user_id = validate_temp_token(token)
        start_session(user_id=user_id, role="student")

    user_id = session.get("user_id")
    role = session.get("role")

    if not user_id or role != "student":
        raise AuthError("You must be logged in as a student.", public=True)

    return user_id"""
