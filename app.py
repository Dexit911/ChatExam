from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from utils.link_creator import create_exam_link

from utils.SEB_manager import SEB_manager

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///exam.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

app.secret_key = "supersecret"


class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.username}>"


class Teacher(db.Model):
    __tablename__ = 'teachers'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Exam(db.Model):
    __tablename__ = 'exams'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), unique=True, nullable=False)
    date = db.Column(db.DateTime, default=datetime.now)


class StudentExam(db.Model):
    __tablename__ = 'student_exams'
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey("exams.id"))
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"))
    link = db.Column(db.String(80), unique=True, nullable=False)
    ai_verdict = db.Column(db.String(80), nullable=False)
    ai_conversation = db.Column(db.String(256), nullable=False)


"""
Student
id | name | email | password_hash

Teacher
id | username | password_hash

Exams
id | title | type | time_limit | description | created_at

Exam student
id | exam_id | student_id | started_at | finished_at | ai_verdict | git_link 
^
dialoge
id | exam_student_id | question | answer | timestamp

"""

"seb://quit"


@app.route('/')
def root():
    return redirect('/teacher/login')


"""---TEACHER---"""


@app.route('/teacher/login', methods=['GET', 'POST'])
def teacher_login():
    if request.method == 'POST':

        username = request.form['username']  # Get username from form
        password = request.form['password']  # Get password from form

        teacher = Teacher.query.filter_by(username=username).first()  # Find teacher by username in DataBase

        if teacher and teacher.check_password(password):  # If found teacher and password is correct
            session["teacher_id"] = teacher.id  # Set current session teacher id
            return redirect('/teacher/create-exam')  # Redirect to page where you can create your exam
        else:
            print("invalid username or password")  # Else wrong logins

    return render_template("teacher_login.html")  # If no post method -> render the login page


@app.route('/teacher/create-exam', methods=['GET', 'POST'])
def create_exam():
    if "teacher_id" not in session:  # If there is no teacher id in session
        return redirect('/teacher/login')  # Go back to login page

    teacher = Teacher.query.filter_by(id=session["teacher_id"]).first()  # Find teacher in DataBase by id
    username = teacher.username

    if request.method == 'POST':  # If teacher clicks on create exam -> POST
        config = {  # Write down values from form checkboxes
            "browserViewMode": request.form.get('browserViewMode'),
            "allowQuit": request.form.get('allowQuit'),
            "allowClipboard": request.form.get('allowClipboard'),
        }

        # ==CREATE ENCRYPTED SEB CONFIG ==
        seb_config = SEB_manager().create_config(config)  # create xml string
        SEB_manager.create_configuration_file(seb_config)  # Save .seb file

        # ==SAVE EXAM TO DB==
        new_exam = Exam(title=request.form.get("title"), date=datetime.now())
        db.session.add(new_exam)
        db.session.commit()

        link = create_exam_link()
        print(link)

    return render_template("create_exam.html", username=username)  # When no method -> render page


"""---STUDENT---"""


@app.route('/student/login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':  # If the form is submitted
        email = request.form['email']  # Get email from the form
        password = request.form['password']  # Get password from the form

        student = Student.query.filter_by(email=email).first()  # Find the student by email

        if student and student.check_password(password):  # If there is student and the password is correct
            session['student_id'] = student.id  # Save student id in the session
            return redirect('/student/start-exam')  # Go to next page
        else:
            print("invalid password or email")

    return render_template("student_login.html")  # If the form is not submitted render the website


@app.route('/student/register', methods=['GET', 'POST'])
def student_register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        new_user = Student(username=username, email=email)
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        teacher = Teacher(username="admin")
        teacher.set_password("123")

        db.session.add(teacher)
        db.session.commit()

        return redirect('/student/login')
    return render_template("student_register.html")


@app.route('/student/start-exam', methods=['GET', 'POST'])
def student_start_exam():
    if 'student_id' not in session:  # If no student id in session redirect back to login
        return redirect('/student/login')

    student = Student.query.filter_by(id=session['student_id']).first()  # Else get student id from session
    return render_template("student_start_exam.html")


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
