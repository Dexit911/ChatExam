# === Standard library ===
from functools import wraps
import json

import flask
# === Third-Party ===
from flask import (
    blueprints,
    render_template,
    session,
    redirect,
    flash,
    url_for,
    request,
    abort,
)
# === Local ===
from chat_exam.extensions import db
from chat_exam.models import Exam, Student, StudentExam
from chat_exam.services import student_service, exam_service, ai_exam_service
from chat_exam.services.ai_exam_service import exam_cache
from chat_exam.templates import forms
from chat_exam.utils import session_manager as sm
from chat_exam.utils.ai_examinator import AIExaminator
from chat_exam.utils.generate_exam_form import generate_exam_form
from chat_exam.utils.git_fecther import fetch_github_code
from chat_exam.repositories import exam_repo, get_by_id, get_by

# === BLUEPRINT FOR STUDENT ROUTES ===
student_bp = blueprints.Blueprint('student', __name__, url_prefix='/student')


# === Decorator: checking if student logged by its session ===
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
            exam_service.create_attempt(
                student_id=sm.current_id("student"),
                code=form.code.data,
                github_link=form.github_link.data,
            )
            print("===NEW ATTEMPT ADDED! ENTERING EXAM===")

            seb_url = url_for(
                "main.exam_link",
                exam_id=exam_repo.get_exam_by_code(form.code.data).id,
                _external=True)
            return redirect(seb_url)

        # Attempt already exists
        except ValueError as e:
            flash(str(e), "danger")

    # Get student username by id
    username = (
        get_by_id(Student, sm.current_id("student"))
        .username
    )

    # === Render the page. Pass username and form ===
    return render_template(
        template_name_or_list="student_dashboard.html",
        title="Enter exam",
        username=username,
        form=form
    )


@student_bp.route("/exam/<code>", methods=['GET', 'POST'])
# @student_required
def exam(code):
    # === VALIDATION FOR SEB ENV AND TOKEN ===
    # === Check SEB environment ===
    ua = request.headers.get("User-Agent", "")
    if "SafeExamBrowser" not in ua:
        abort(403, description="This exam must be taken in Safe Exam Browser")
    print("===THE EXAM IS TAKEN IN SEB ENV ===")

    # === Token-based logic ===
    token = request.args.get("token")
    if token:
       try:
           student_id  = sm.validate_temp_token(token)
           sm.start_session(user_id=student_id, role="student")
           print(f"[ OK ] auto logged student {student_id} from SEB token")
       except Exception as e:
           print(f"[ ERROR ] could not auto login student: {e}")
           flash("Invalid exam link", "danger")
           return redirect(url_for("student.dashboard"))

    # === Fetch exam and attempt ===
    exam = exam_repo.get_exam_by_code(code)
    attempt = get_by(StudentExam, exam_id=exam.id, student_id=sm.current_id("student"))
    print(attempt)

    # === Create task for generating ai response ===
    existing_task = next(
        (tid for tid, data in exam_cache.items() if data.get("student_id") == student_id),
        None
    )
    if existing_task:
        task_id = existing_task
    else:
        task_id = ai_exam_service.generate_questions_async(
            github_link=attempt.github_link,
            question_count=attempt.exam.question_count,
            student_id=sm.current_id("student"),
        )

    # === If no response load "loading" page ===
    data = exam_cache.get(task_id)
    if not data:
        print(f"=Failed to fetch task id={task_id}")
        print(f"=Rendering wait page=")
        return render_template("student/loading.html", status="pending")

    # === When task is done - create form, fetch code and render exam page ===
    if data["status"] == "done":
        print(f"=Got task id={task_id}")
        # === GET QUESTION FROM CACHE
        questions_dict = data["questions"]

        # === GENERATE FORM BASE ON QUESTIONS ===
        form = generate_exam_form(questions_dict)
        code_string = fetch_github_code(attempt.github_link)
        code_json = json.dumps(code_string)
        print(f"\n=== STUDENTS GITHUB LINK\n{attempt.github_link}\n===")
        print(f"\n=== STUDENTS CODE\n{code_string[0:100]}\n===")

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
                code_string=code_string,
                questions_dict=questions_dict,
                answers_dict=answers,
            )

            # Save attempt results to db
            exam_service.save_attempt_results(
                attempt_id=attempt.id,
                questions_dict=questions_dict,
                answers_dict=answers,
                code=code_string,
                ai_verdict=verdict,
                ai_rating=rating,
            )
            print("\n=== ATTEMPT DATA SAVED ===")

            # === REDIRECT TO DASHBOARD ===
            return redirect(url_for("student.dashboard"))

        return render_template("student/exam.html", form=form, code_json=code_json)
    return render_template("student/loading.html")


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
