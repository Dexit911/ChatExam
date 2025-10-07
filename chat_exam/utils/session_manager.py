from annotated_types.test_cases import cases
from flask import session



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
    """Get users id by role"""
    return session.get(f"{role}_id")



