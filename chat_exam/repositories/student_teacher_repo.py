from chat_exam.models import StudentTeacher
from chat_exam.extensions import db

def link(student_id: int, teacher_id: int, auto_commit: bool = True) -> StudentTeacher:
    """Link a student to a teacher."""
    link = StudentTeacher(student_id=student_id, teacher_id=teacher_id)
    db.session.add(link)
    if auto_commit:
        db.session.commit()
    return link

def unlink(student_id: int, teacher_id: int, auto_commit: bool = True) -> None:
    """Unlink a student to a teacher."""
    link = StudentTeacher.query.filter_by(
        student_id=student_id,
        teacher_id=teacher_id
    ).first()
    if link:
        db.session.delete(link)
        if auto_commit:
            db.session.commit()

def exists_link(student_id: int, teacher_id: int) -> bool:
    """Check if a link exists."""
    return (
        db.session.query(StudentTeacher)
        .filter_by(student_id=student_id, teacher_id=teacher_id)
        .first()
        is not None
    )
