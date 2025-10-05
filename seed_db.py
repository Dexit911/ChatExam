from chat_exam import db
from run import app
from chat_exam.models import Student, Teacher

# Run inside app context
def create_start_db():
    with app.app_context():
        # === Create test teacher ===
        teacher = Teacher(
            username="admin",
            email="admin@exam.com"
        )
        teacher.set_password("Daniel")

        # === Create test students ===
        students = []
        for i in range(1, 6):
            s = Student(
                username=f"student{i}",
                email=f"{i}@{i}.com"
            )
            s.set_password("Daniel")
            students.append(s)

        # === Add to DB ===
        db.session.add(teacher)
        db.session.add_all(students)
        db.session.commit()

        print("✅ Test accounts created successfully!")

if __name__ == '__main__':
    create_start_db()