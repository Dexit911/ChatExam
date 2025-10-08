# === Standard library ===
import os
from functools import wraps

# === Third-Party ===
from flask import (
    blueprints,
    render_template,
    session,
    redirect,
    url_for,
    flash
)

# ===Local===
from chat_exam.models import Exam, StudentTeacher, Student, StudentExam, Teacher
from chat_exam.templates import forms
from chat_exam.services import teacher_service, exam_service
from chat_exam.utils import session_manager as sm
from chat_exam.repositories import get_by

# === Blueprint for teache route ===
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
    print("Form validated:", form.validate_on_submit())
    print("Errors:", form.errors)
    if form.validate_on_submit():
        try:
            # Try login
            teacher = teacher_service.login_teacher(
                email=form.email.data,
                password=form.password.data
            )
            sm.start_session(
                user_id=teacher.id,
                role="teacher",
            )

            # If successful redirect to dashboard
            flash("You have successfully logged in.", "success")
            return redirect(url_for("teacher.dashboard"))

        except ValueError as e:
            flash(str(e), "danger")

    # === If no method, render the page ===
    return render_template("teacher_login.html", title="Test Login", form=form)


"""DASHBOARD ROUTES"""


# noinspection PyUnreachableCode
@teacher_bp.route("/dashboard", methods=["GET", "POST"])
@teacher_required
def dashboard() -> str:
    """
    Render the teacher dashboard if the account exists.
    """
    teacher_id = sm.current_id("teacher")
    teacher = get_by(Teacher, id=teacher_id)

    if not teacher:
        flash("Your account no longer exists.", "danger")
        sm.end_session()
        return redirect(url_for("main.index"))

    return render_template(
        "teacher/teacher_dashboard.html",
        username=teacher.username
    )


@teacher_bp.route('/create-exam', methods=['GET', 'POST'])
@teacher_required
def create_exam():
    # === Get form template ===
    form = forms.CreatExamForm()

    # === If submit is valid ===
    if form.validate_on_submit():  # If teacher clicks on create exam -> POST

        try:
            # Try to create exam
            exam_service.create_exam(
                title=form.title.data,
                teacher_id=sm.current_id("teacher"),
                question_count=form.question_count.data,
                settings={
                    "browserViewMode": form.browser_view_mode.data,
                    "allowQuit": form.allow_quit.data,
                    "allowClipboard": form.allow_clipboard.data,
                }
            )

            # If created exam, redirect to dashboard
            flash("You have successfully created a new exam.")
            return redirect(url_for("teacher.dashboard"))

        except ValueError as e:
            flash(str(e), "danger")

    return render_template("teacher/create_exam.html", form=form)

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

@teacher_bp.route("/delete-attempt/<int:attempt_id>", methods=["POST"])
@teacher_required
def delete_attempt(attempt_id):
    """Delete student exam attempt"""

    try:
        attempt = get_by(StudentExam, id=attempt_id)
        exam_service.delete_attempt(attempt_id)

        flash("Attempt deleted", "success")
        return redirect(url_for("teacher.view_exam_attempts", exam_id=attempt.exam_id))

    except ValueError as e:
        flash(str(e), "danger")

    return redirect(url_for("teacher.view_exams"))






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
