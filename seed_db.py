from chat_exam import db
from run import app
from chat_exam.models import Student, Teacher, Exam, StudentExam
import secrets
from datetime import datetime

def create_start_db():
    with app.app_context():
        db.drop_all()
        db.create_all()

        # === Create test teacher ===
        teacher = Teacher(
            username="admin",
            email="admin@exam.com"
        )
        teacher.set_password("Daniel")
        db.session.add(teacher)
        db.session.commit()

        # === Create test students ===
        students = []
        for i in range(1, 6):
            s = Student(
                username=f"student{i}",
                email=f"{i}@{i}.com"
            )
            s.set_password("Daniel")
            db.session.add(s)
            students.append(s)
        db.session.commit()

        # === Create 10 exams ===
        exams = []
        for i in range(1, 11):
            exam = Exam(
                title=f"Exam {i}",
                teacher_id=teacher.id,
                question_count=5,
                date=datetime.now()
            )
            exam.generate_code()
            db.session.add(exam)
            exams.append(exam)
        db.session.commit()

        # === Create StudentExam attempts (every student → every exam) ===
        for student in students:
            for exam in exams:
                attempt = StudentExam(
                    exam_id=exam.id,
                    student_id=student.id,
                    github_link=f"https://github.com/test/{student.username}-exam{exam.id}",
                    ai_verdict=None,
                    ai_conversation=None,
                    ai_rating=None,
                    status="ongoing"
                )
                db.session.add(attempt)
        db.session.commit()

        print("✅ Created 1 teacher, 5 students, 10 exams, and all student attempts!")

if __name__ == '__main__':
    create_start_db()
