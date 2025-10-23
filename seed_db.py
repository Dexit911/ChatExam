from chat_exam import db
from run import app
from chat_exam.models import User, Exam, Attempt, Supervision
from datetime import datetime
import secrets


def create_start_db():
    with app.app_context():
        db.drop_all()
        db.create_all()

        # === Create teacher ===
        teacher = User(username="admin", email="admin@exam.com", role="teacher")
        teacher.set_password("Daniel")
        db.session.add(teacher)
        db.session.commit()

        # === Create students ===
        students = []
        for i in range(1, 20):
            s = User(
                username=f"student{i}",
                email=f"{i}@{i}.com",
                role="student"
            )
            s.set_password("Daniel")
            db.session.add(s)
            students.append(s)
        db.session.commit()

        # === Link students to teacher (Supervision) ===
        for s in students:
            supervision = Supervision(teacher_id=teacher.id, student_id=s.id)
            db.session.add(supervision)
        db.session.commit()

        # === Create exams ===
        """exams = []
        for i in range(1, 6):
            exam = Exam(
                title=f"Exam {i}",
                teacher_id=teacher.id,
                question_count=5,
                type="code_github"
            )
            exam.generate_code()
            db.session.add(exam)
            exams.append(exam)
        db.session.commit()"""

        # === Create attempts (each student → each exam) ===
        """for s in students:
            for e in exams:
                attempt = Attempt(
                    exam_id=e.id,
                    student_id=s.id,
                    github_link=f"https://github.com/test/{s.username}-exam{e.id}",
                    status="ready"
                )
                db.session.add(attempt)
        db.session.commit()"""

        print("✅ Created 1 teacher, 5 students, 5 exams, and linked all attempts!")


if __name__ == '__main__':
    create_start_db()
