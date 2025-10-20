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
    flash,
    abort
)

# ===Local===
from chat_exam.models import Exam, Attempt, User, Supervision
from chat_exam.templates import forms
from chat_exam.services import user_service, exam_service
from chat_exam.utils import session_manager as sm
from chat_exam.repositories import get_by, delete, user_repo
from chat_exam.utils.validators import role_required

# === Blueprint for teache route ===
teacher_bp = blueprints.Blueprint('teacher', __name__, url_prefix='/teacher')


@teacher_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = forms.TeacherLoginForm()
    print("Created forms")

    # === If form is submitted ===
    print("Form validated:", form.validate_on_submit())
    print("Errors:", form.errors)
    if form.validate_on_submit():
        try:
            # Try login
            teacher = user_service.login_teacher(
                email=form.email.data,
                password=form.password.data
            )
            print("User logged in:", teacher)
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
    return render_template("teacher_login.html", title="TeacherLogin", form=form)


# === Dashboard routes ===

# noinspection PyUnreachableCode
@teacher_bp.route("/dashboard", methods=["GET", "POST"])
@role_required("teacher")
def dashboard() -> str:
    """
    Render the teacher dashboard if the account exists.
    """
    teacher_id = sm.current_id()
    teacher = user_repo.get_user_by_id(teacher_id)

    if not teacher:
        flash("Your account no longer exists.", "danger")
        sm.end_session()
        return redirect(url_for("main.index"))

    return render_template(
        "teacher/teacher_dashboard.html",
        username=teacher.username
    )


@teacher_bp.route('/create-exam', methods=['GET', 'POST'])
@role_required("teacher")
def create_exam():
    # === Get form template ===
    form = forms.CreatExamForm()

    # === If submit is valid ===
    if form.validate_on_submit():  # If teacher clicks on create exam -> POST

        try:
            # Try to create exam
            exam_service.create_exam(
                title=form.title.data,
                teacher_id=sm.current_id(),
                question_count=form.question_count.data,
                seb_settings={
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
@role_required("teacher")
def view_exams():
    # === Get list of all exams created by current teacher ===
    exams = exam_service.view_exams(sm.current_id())
    return render_template("teacher/view_exams.html", exams=exams)


@teacher_bp.route("/delete-exam/<exam_id>", methods=['POST'])
@role_required("teacher")
def delete_exam(exam_id):
    # === Deletes exam that teacher have created ===
    exam_service.delete_exam(sm.current_id(), exam_id)
    flash("Successfully deleted exam", "success")
    return redirect(url_for("teacher.view_exams"))

@teacher_bp.route("/view-exams/<int:exam_id>/attempts", methods=['GET', 'POST'])
@role_required("teacher")
def view_exam_attempts(exam_id):
    # === View all attempts for current viewed exam ===
    exam, attempts = exam_service.get_attempts(sm.current_id(), exam_id)
    return render_template(
        "teacher/view_exam_attempts.html",
        exam=exam,
        attempts=attempts
    )


@teacher_bp.route("/view-students", methods=['GET', 'POST'])
@role_required("teacher")
def view_students():
    # === Get list of all Students that belongs to current teacher ===
    students = user_service.get_students(sm.current_id())
    return render_template("teacher/view_students.html", students=students)
