import itsdangerous

from flask import session

from chat_exam.config import Config

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
    match role:
        case "student": session["student_id"] = user_id
        case "teacher": session["teacher_id"] = user_id
        case _: raise ValueError(f"Unknown role {role}")


def current_id(role: str) -> int:
    """Get users id from session by role."""
    return session.get(f"{role}_id")

def current_role():
    return session.get("role")


# WORKS ONLY FOR STUDENT
def create_temp_token(student_id: int):
    """Create short-lived token (valid 5 min) for student auto-login."""
    return serializer.dumps({"student_id": student_id})

def validate_temp_token(token, max_age=300):
    """Decode token and return student_id if valid."""
    data = serializer.loads(token, max_age=max_age)
    return data["student_id"]


def ensure_student_session(token: str | None) -> int:
    """Validate SEB token or use active session. Returns student_id."""
    if token:
        student_id = validate_temp_token(token)
        start_session(user_id=student_id, role="student")
        print(f"[ OK ] Auto logged student {student_id}")
    if not current_id("student"):
        raise PermissionError("You must be logged in as a student.")
    return current_id("student")

