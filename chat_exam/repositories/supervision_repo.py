from chat_exam.models import User, Supervision
from chat_exam.repositories import get_by, filter_by, save, delete
from chat_exam.extensions import db


def link(teacher_id: int, student_id: int) -> None:
    """Create supervision relationship between teacher and student."""
    link = Supervision(teacher_id=teacher_id, student_id=student_id)
    save(link)
    return link


def unlink(teacher_id, student_id) -> None:
    """Remove supervision relationship between teacher and student."""
    link = Supervision.query.filter_by(
        teacher_id=teacher_id, student_id=student_id
    ).first()
    if link:
        delete(link)


def ensure_link(teacher_id: int, student_id: int) -> None:
    """Ensure supervision relationship between teacher and student."""
    if not link_exists(teacher_id, student_id):
        link(teacher_id=teacher_id, student_id=student_id)


def link_exists(student_id: int, teacher_id: int) -> bool:
    """Check if a link exists."""
    return (
            db.session.query(Supervision)
            .filter_by(student_id=student_id, teacher_id=teacher_id)
            .first()
            is not None
    )
