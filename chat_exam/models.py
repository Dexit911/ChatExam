import secrets
from datetime import datetime
from sqlalchemy.orm import validates
from chat_exam.extensions import db
from chat_exam.utils import security
from chat_exam.exceptions import ValidationError


# === USER MODEL ===
class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(80), nullable=False)  # "teacher", "student", "admin"

    def set_password(self, password):
        self.password_hash = security.hash_password(password)

    def check_password(self, password):
        return security.verify_password(password, self.password_hash)

    def __repr__(self):
        return f"<User {self.username}, role: {self.role}>"


# === ATTEMPT MODEL ===
class Attempt(db.Model):
    __tablename__ = 'attempts'

    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey("exams.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)  # ✅ fixed FK

    github_link = db.Column(db.String(200))
    questions_json = db.Column(db.JSON)
    answers_json = db.Column(db.JSON)

    ai_verdict = db.Column(db.String(80))
    ai_conversation = db.Column(db.Text)
    ai_rating = db.Column(db.String(1))

    status = db.Column(db.String(80), default="ready", nullable=False)

    exam = db.relationship("Exam", backref="attempts")
    user = db.relationship("User", backref="attempts")  # ✅ fixed relationship

    @validates("status")
    def validate_status(self, key, value):
        allowed = {"ready", "ongoing", "done"}
        if value not in allowed:
            raise ValidationError(f"Invalid status '{value}'. Must be one of {allowed}.")
        return value


# === EXAM MODEL ===
class Exam(db.Model):
    __tablename__ = "exams"

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default=datetime.now)
    code = db.Column(db.String(8), unique=True, nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(30), default="code_github", nullable=False)

    question_count = db.Column(db.Integer, default=1, nullable=False)

    seb_settings = db.Column(db.JSON, default={})
    logic_settings = db.Column(db.JSON, default={})

    teacher = db.relationship("User", backref="exams", foreign_keys=[teacher_id])

    def generate_code(self):
        self.code = secrets.token_hex(3)


# === SUPERVISION MODEL ===
class Supervision(db.Model):
    __tablename__ = "supervisions"

    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    teacher = db.relationship("User", foreign_keys=[teacher_id], backref="students")
    student = db.relationship("User", foreign_keys=[student_id], backref="teachers")


class UsedToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(255), unique=True)
