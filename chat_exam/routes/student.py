# === Standard library ===
from functools import wraps
import json
import logging
# === Third-Party ===
from flask import (
    blueprints,
    render_template,
    session,
    redirect,
    flash,
    url_for,
    request,
)
# === Local ===
from chat_exam.models import StudentExam
from chat_exam.services import student_service, exam_service, ai_exam_service, seb_service
from chat_exam.templates import forms
from chat_exam.utils import session_manager as sm
from chat_exam.utils import seb_manager
from chat_exam.utils.generate_exam_form import generate_exam_form
from chat_exam.utils.git_fecther import fetch_github_repo
from chat_exam.repositories import exam_repo, get_by
from chat_exam.utils import security

logger = logging.getLogger(__name__)

# === BLUEPRINT FOR STUDENT ROUTES ===
student_bp = blueprints.Blueprint('student', __name__, url_prefix='/student')


# === Decorator - checking if student is logged in by their session ===
def student_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if "student_id" not in session or session.get("role") != "student":
            flash("You must be logged in as a student.", "danger")
            return redirect(url_for("student.login"))
        return func(*args, **kwargs)

    return decorated_function


@student_bp.route('/dashboard', methods=['GET', 'POST'])
@student_required
def dashboard():
    # === Get the form template ===
    form = forms.StudentExamCode()

    # === If submit is valid, (The code, and github link) ===
    if form.validate_on_submit():
        # Try to create student attempt
        try:
            # === CREATE ATTEMPT -> db===
            attempt = exam_service.create_attempt(
                student_id=sm.current_id("student"),
                code=form.code.data,
                github_link=form.github_link.data,
            )

            # === CREATE AND SAVE SEB CONFIG FILE WITH TOKENIZED URL -> seb-config folder===
            seb_service.generate_config(
                attempt=attempt,
                exam=exam_repo.get_exam_by_code(form.code.data),
                student_id=sm.current_id("student")
            )

            # === REDIRECT TO SEB ENV WITH EXAM ===
            seb_url = url_for(
                "main.exam_link",
                attempt_id=attempt.id,
                _external=True)
            return redirect(seb_url)

        except ValueError as e:
            flash(str(e), "danger")

    # === Render the page. Pass username and form ===
    return render_template(
        template_name_or_list="student_dashboard.html",
        title="Enter exam",
        form=form,
    )


@student_bp.route("/exam/<code>", methods=['GET', 'POST'])
def exam(code):
    # === Check if request happens from SEB env ===
    security.is_seb_request(request)

    # === Ensure session via token ===
    try:
        student_id = sm.ensure_student_session(request.args.get("token"))
    except Exception as e:
        logger.error(f"Session or token invalid: {e} ")
        flash("Invalid  or expired exam link", "danger")
        return redirect(url_for("student.dashboard"))

    # === Fetch exam + attempt ===
    exam = exam_repo.get_exam_by_code(code)
    attempt = get_by(StudentExam, exam_id=exam.id, student_id=sm.current_id("student"))

    # === Delete attempts seb configuration file ===
    seb_manager.Seb_manager().delete_seb_file(attempt.id)

    # === Get student content from gitHub repo etc. Code, files their names and type ===
    repo_data = fetch_github_repo(
        url=exam.github_link,
        max_files=4,
        remove_comments=True,
    )

    # === Ensure AI questions are ready (cached or async). If not - start generating questions ===
    task_id, data, status = ai_exam_service.ensure_questions_ready(
        student_id=student_id,
        data=repo_data,
        question_count=attempt.exam.question_count
    )

    if status == "pending":
        print(f"=Rendering loading page for student {student_id}=")
        return render_template("student/loading.html", status="pending")

    """EXAM PROCESS"""
    if status == "done":
        attempt.staus = "ongoing"

        print(f"=Got task id={task_id}")
        # === GET QUESTION FROM CACHE
        questions_dict = data["questions"]

        # === GENERATE FORM BASE ON QUESTIONS ===
        form = generate_exam_form(questions_dict)
        repo_data = fetch_github_repo(attempt.github_link, 3, True)
        files_json = json.dumps(repo_data)
        print(f"\n=== STUDENTS GITHUB LINK\n{attempt.github_link}\n===")

        # === THIS ERROR HAPPENS IF AI COULD NOT GIVE QUESTIONS IN THE RIGHT JSON FORMAT ===
        if "error" in questions_dict:
            print(f"\n[ ERROR ] Failed to generate questions for: {attempt.github_link}===")
            flash(questions_dict["error"], "danger")
            return redirect("student.dashboard")

        # === IF STUDENT SUBMITS ANSWERS ===
        if form.validate_on_submit():
            answers = {key: getattr(form, key).data for key in questions_dict.keys()}
            print(f"\n=== STUDENT ANSWERS\n{answers}\n===")

            # CREATE VERDICT
            verdict, rating = ai_exam_service.generate_verdict(
                data=data,
                questions_dict=questions_dict,
                answers_dict=answers,
            )

            # Save attempt results to db
            exam_service.save_attempt_results(
                attempt_id=attempt.id,
                questions_dict=questions_dict,
                answers_dict=answers,
                code=data,
                ai_verdict=verdict,
                ai_rating=rating,
            )
            print("\n=== ATTEMPT DATA SAVED ===")

            # === Quit seb env with build in protocol ===

            return render_template("student/exam_finished.html")

        return render_template("student/exam.html", form=form, code_json=files_json)
    return render_template("student/loading.html")


@student_bp.route("/exam/loading", methods=['GET', 'POST'])




@student_bp.route('/register', methods=['GET', 'POST'])
def register():
    # === Get form template ===
    form = forms.StudentRegistrationForm()

    # === If user submits registration ===
    if form.validate_on_submit():
        try:
            # Try register
            student = student_service.create_student(
                email=form.email.data,
                password=form.password.data,
                username=form.username.data,
            )

            # Set session and redirect to dashboard
            sm.start_session(
                user_id=student.id,
                role="student"
            )

            # Redirect student to dashboard
            flash(f"Account created for {form.username.data}!", "success")
            return redirect(url_for('student.dashboard'))

        except ValueError as e:
            flash(str(e), "danger")

    # === If no method -> render page ===
    return render_template("student_register.html", title="Test Register", form=form)


@student_bp.route('/login', methods=['GET', 'POST'])
def login():
    # === Get form template ===
    form = forms.StudentLoginForm()

    # === If form is submitted ===
    if form.validate_on_submit():
        try:
            # Try login
            student = student_service.login_student(
                email=form.email.data,
                password=form.password.data,
            )
            sm.start_session(
                user_id=student.id,
                role="student"
            )
            # If successful
            flash(f"Login successful!", "success")
            return redirect(url_for("student.dashboard"))

        except ValueError as e:
            # error (wrong/email password)
            flash(str(e), "danger")

    # === If no method, render the page ===
    return render_template("student_login.html", title="Test Login", form=form)
