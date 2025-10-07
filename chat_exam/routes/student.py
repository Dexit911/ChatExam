# === Standard library ===
from functools import wraps
import json

# === Third-Party ===
from flask import (
    blueprints,
    render_template,
    session,
    redirect,
    flash,
    url_for,
)
# === Local ===
from chat_exam.extensions import db
from chat_exam.models import Exam, Student, StudentExam
from chat_exam.services import student_service, exam_service
from chat_exam.templates import forms
from chat_exam.utils import session_manager as sm
from chat_exam.utils.ai_examinator import AIExaminator
from chat_exam.utils.generate_exam_form import generate_exam_form
from chat_exam.utils.git_fecther import fetch_github_code
from chat_exam.repositories import exam_repo, get_by_id

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
    # === Check if the request happens from SEB protocol ===
    """ ua = request.headers.get("User-Agent", "")
    if "SafeExamBrowser" not in ua:
        abort(403, description="This exam must be taken in Safe Exam Browser")
    print("===THE EXAM IS TAKEN IN SEB ENV ===")"""

    # === GET STUDENTS GITHUB LINK ===
    exam_id = Exam.query.filter_by(code=code).first().id
    student_github_link = StudentExam.query.filter_by(exam_id=exam_id,
                                                      student_id=session["student_id"]).first().github_link
    print(f"\n\n===GITHUB LINK===\n\n{student_github_link}")

    # === FETCH CODE, CONVERT TO TEXT AND JSON. TEXT -> AI, JSON -> WEB PAGE ===
    code_text = fetch_github_code(student_github_link)
    code_json = json.dumps(code_text)
    print(f"\n\n===EXTRACTED CODE FROM GITHUB LINK===\n\n{code_text[0:100]}\n...")

    # === CREATE AI EXAMINATOR AND CREATE QUESTION BASED ON CODE ===
    question_count = 10  # Parse this from exam setting in future
    examinator = AIExaminator(question_count=question_count)
    questions_dict = examinator.create_questions(code_text)

    # === IF AI FAILED TO CREATE QUESTIONS -> SHOW ERROR ===
    if "error" in questions_dict:
        print("### AI FAILED TO CREATE QUESTIONS. QUESTIONS ARE NOT PASSED TO EXAM FORM ###")
        flash(questions_dict["error"], "danger")
        return redirect(url_for("student.dashboard"))

    # === IF QUESTIONS ARE VALID -> CREATE EXAM FORM ===
    form = generate_exam_form(questions_dict)
    print(f"\n\n===GENERATED VALID QUESTIONS===\n\n{questions_dict})")

    # === IF STUDENT SUBMITS QUESTIONS ===
    if form.validate_on_submit():
        # Get answers
        answers = {key: getattr(form, key).data for key in questions_dict.keys()}
        print("=== STUDENT ANSWERS ===")
        print(answers)

        # Create verdict and rating
        verdict, rating = examinator.create_verdict(
            code=code_text,
            questions=questions_dict,
            answers=answers
        )
        print("=== AI VERDICT, RATING ===")
        print(verdict, rating)

        # Update StudentExam status, verdict, rating
        exam_id = Exam.query.filter_by(code=code).first().id
        attempt = StudentExam.query.filter_by(student_id=session['student_id'], exam_id=exam_id).first()

        attempt.status = "submitted"
        attempt.ai_verdict = verdict
        attempt.ai_rating = str(rating)

        db.session.commit()
        print("=== STUDENT ANSWER ADDED TO EXAM, STATUS UPDATED ===")

        # Redirect back to dashboard
        return redirect(url_for("student.dashboard"))

    return render_template("student/exam.html", form=form, code_json=code_json)


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
