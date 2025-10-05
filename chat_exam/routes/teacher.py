import flask
from functools import wraps
from flask import blueprints, render_template, session, redirect, url_for, flash
import os

# ===MODELS AND EXTENSIONS===
from chat_exam.models import Teacher, Exam, StudentTeacher, Student, StudentExam
from chat_exam.extensions import db
from chat_exam.templates import forms
from chat_exam.utils.seb_encryptor import encrypt_seb_config

# ===UTILS===
from chat_exam.utils.seb_manager import Seb_manager

teacher_bp = blueprints.Blueprint('teacher', __name__, url_prefix='/teacher')


def teacher_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if "teacher_id" not in session or session.get("role") != "teacher":
            flash("You must be logged in as a teacher.", "danger")
            return redirect(url_for("teacher.login"))
        return func(*args, **kwargs)

    return decorated_function


@teacher_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = forms.TeacherLoginForm()

    # === If form is submitted ===
    if form.validate_on_submit():

        # === Get data from form and search for user in db ===
        email = form.email.data
        password = form.password.data
        teacher = Teacher.query.filter_by(email=email).first()  # Find the student by email

        # === If there is student and the password is matching, set session id and role ===
        if teacher and teacher.check_password(password):
            session['teacher_id'] = teacher.id
            session['role'] = "teacher"
            return redirect(url_for('teacher.dashboard'))

        # === If login fails, give message to user ===
        else:
            flash("Login unsuccessful", "danger")

    # === If no method, render the page ===
    return render_template("teacher_login.html", title="Test Login", form=form)


"""DASHBOARD ROUTES"""


@teacher_bp.route("/dashboard", methods=['GET', 'POST'])
@teacher_required
def dashboard():
    teacher = Teacher.query.filter_by(id=session["teacher_id"]).first()
    username = teacher.username
    return render_template("teacher/teacher_dashboard.html")


@teacher_bp.route('/create-exam', methods=['GET', 'POST'])
@teacher_required
def create_exam():
    # === Get form template ===
    form = forms.CreatExamForm()

    # === If submit is valid ===
    if form.validate_on_submit():  # If teacher clicks on create exam -> POST
        settings = {  # Write down values from form checkboxes
            "browserViewMode": form.browser_view_mode.data,
            "allowQuit": form.allow_quit.data,
            "allowClipboard": form.allow_clipboard.data,
        }

        # ==SAVE EXAM TO DB==
        new_exam = Exam(title=form.title.data)
        new_exam.generate_code()
        new_exam.teacher_id = session["teacher_id"]

        db.session.add(new_exam)
        db.session.flush()  # ensures new_exam.id is generated

        # === CREATE EXAM URL AND SEB CONFIG ===
        exam_url = url_for("student.exam", code=new_exam.code, _external=True)
        seb_config = Seb_manager().create_config(settings=settings, exam_url=exam_url)
        encrypted = encrypt_seb_config(seb_config)

        # === SAVE .SEB FILE ===
        seb_dir = "seb_config"
        os.makedirs(seb_dir, exist_ok=True)
        seb_path = os.path.join(seb_dir, f"exam_{new_exam.id}.seb")

        with open(seb_path, "w") as f:
            f.write(seb_config)

        # === Fina commit() ===
        db.session.commit()

        # Debug
        print(new_exam.code)

        # === When exam created redirect teacher to dashboard ===
        return redirect(url_for('teacher.dashboard'))
    else:
        # === GIVE ERROR ===
        flask.flash("Create exam failed", "danger")

    # === If nothing happens render page ===
    return render_template("teacher/create_exam.html", form=form)  # When no method -> render page


@teacher_bp.route("/view-exams", methods=['GET', 'POST'])
@teacher_required
def view_exams():
    # === Get list of all exams created by current teacher ===
    exams = Exam.query.filter_by(teacher_id=session["teacher_id"]).all()
    return render_template("teacher/view_exams.html", exams=exams)


@teacher_bp.route("/view-exams/<int:exam_id>/attempts", methods=['GET', 'POST'])
@teacher_required
def view_exam_attempts(exam_id):
    exam = Exam.query.filter_by(id=exam_id, teacher_id=session["teacher_id"]).first_or_404()
    attempts = StudentExam.query.filter_by(exam_id=exam.id).all()

    return render_template(
        "teacher/view_exam_attempts.html",
        exam=exam,
        attempts=attempts
    )


@teacher_bp.route("/view-students", methods=['GET', 'POST'])
@teacher_required
def view_students():
    # === Get list of all Students that belongs to current teacher ===
    students = (
        Student.query
        .join(StudentTeacher, Student.id == StudentTeacher.student_id)
        .filter(StudentTeacher.teacher_id == session["teacher_id"])
        .all()
    )

    return render_template("teacher/view_students.html", students=students)
