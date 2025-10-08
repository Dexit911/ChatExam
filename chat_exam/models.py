import secrets

from datetime import datetime

from chat_exam.extensions import db
from chat_exam.utils import security


"""STUDENT DATABASE"""
class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    def set_password(self, password):
        self.password_hash = security.hash_password(password)

    def check_password(self, password):
        return security.verify_password(password, self.password_hash)

    def __repr__(self):
        return f"<User {self.username}>"

"""TEACHER DATABASE"""
class Teacher(db.Model):
    __tablename__ = 'teachers'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    def set_password(self, password):
        self.password_hash = security.hash_password(password)

    def check_password(self, password):
        return security.verify_password(password, self.password_hash)

"""EXAMS DATABASE"""
class Exam(db.Model):
    __tablename__ = 'exams'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), unique=True, nullable=False)
    code = db.Column(db.String(8), unique=True, nullable=False)
    date = db.Column(db.DateTime, default=datetime.now)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False)
    question_count = db.Column(db.Integer, nullable=False)

    def generate_code(self):
        self.code = secrets.token_hex(3)


"""STUDENT LINKED TO EXAM"""
class StudentExam(db.Model):
    __tablename__ = 'student_exams'
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey("exams.id"))
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"))

    github_link = db.Column(db.String(80), nullable=False)

    ai_verdict = db.Column(db.String(80), nullable=True)
    ai_conversation = db.Column(db.String(256), nullable=True)
    ai_rating =  db.Column(db.String(1), nullable=True)

    status = db.Column(db.String(80), nullable=False)

    student = db.relationship("Student", backref="student_exams", lazy=True)
    exam = db.relationship("Exam", backref="exam_attempts", lazy=True)

"""STUDENT LINKED TO TEACHER"""
class StudentTeacher(db.Model):
    __tablename__ = 'student_teachers'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"))
    teacher_id = db.Column(db.Integer, db.ForeignKey("teachers.id"))

    student = db.relationship("Student", backref="teacher_links", lazy=True)
    teacher = db.relationship("Teacher", backref="student_links", lazy=True)

