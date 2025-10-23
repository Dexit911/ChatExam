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
from chat_exam.models import Attempt
from chat_exam.services import exam_service, user_service, ai_exam_service, seb_service
from chat_exam.templates import forms
from chat_exam.utils import session_manager as sm
from chat_exam.utils import seb_manager
from chat_exam.utils.generate_exam_form import generate_exam_form
from chat_exam.utils.git_fecther import fetch_github_repo
from chat_exam.repositories import exam_repo, get_by
from chat_exam.utils import security
from chat_exam.utils.validators import role_required

logger = logging.getLogger(__name__)

# === BLUEPRINT FOR STUDENT ROUTES ===
student_bp = blueprints.Blueprint('student', __name__, url_prefix='/student')

@student_bp.route('/dashboard', methods=['GET', 'POST'])
@role_required("student")
def dashboard():
    # === Get the form template ===
    form = forms.StudentExamCode()

    # === If submit is valid, (The code, and github link) ===
    if form.validate_on_submit():

        # === CREATE ATTEMPT -> db===
        attempt = exam_service.create_attempt(
            student_id=sm.current_id(),
            code=form.code.data,
            github_link=form.github_link.data,
        )

        # === CREATE AND SAVE SEB CONFIG FILE WITH TOKENIZED URL -> seb-config folder===
        seb_service.generate_config(
            attempt=attempt,
            exam=exam_repo.get_exam_by_code(form.code.data),
            student_id=sm.current_id()
        )

        # === REDIRECT TO SEB ENV WITH EXAM ===
        seb_url = url_for(
            "main.exam_link",
            attempt_id=attempt.id,
            _external=True)
        return redirect(seb_url)


    # === Render the page. Pass username and form ===
    return render_template(
        template_name_or_list="student_dashboard.html",
        title="Enter exam",
        form=form,
    )


@student_bp.route("/exam-test/<code>", methods=['GET', 'POST'])
def exam_test(code):
    """
    Local testing route for running the exam without SEB validation.
    Allows debugging exam generation, question rendering, and submission.
    """

    # === Mock current student session for testing ===
    student_id = sm.current_id() or 1  # fallback if no session
    # === Fetch exam and attempt ===
    exam = exam_repo.get_exam_by_code(code)
    attempt = get_by(Attempt, exam_id=exam.id, student_id=student_id)

    if not attempt:
        flash("No attempt found. Please create one from dashboard.", "danger")
        return redirect(url_for("student.dashboard"))

    # === Get repo data ===
    repo_data = fetch_github_repo(
        url=attempt.github_link,
        max_files=4,
        remove_comments=True,
    )

    # === Ensure AI questions are ready (cached or generate fresh) ===
    task_id, data, status = ai_exam_service.ensure_questions_ready(
        user_id=student_id,
        file_data=repo_data,
        question_count=attempt.exam.question_count
    )

    # === Handle pending status ===
    if status == "pending":
        print(f"=Rendering loading page for TEST student {student_id}=")
        return render_template("student/loading.html", status="pending")

    """EXAM TEST PROCESS"""
    if status == "done":
        attempt.status = "ongoing"

        print(f"=Got task id={task_id}")
        # === Get questions ===
        questions_dict = data["questions"]

        # === Generate form based on questions ===
        form = generate_exam_form(questions_dict)

        # === Handle bad JSON / AI error ===
        if "error" in questions_dict:
            print(f"[ ERROR ] Failed to generate questions for: {attempt.github_link}")
            flash(questions_dict["error"], "danger")
            return redirect(url_for("student.dashboard"))

        # === When submitting ===
        if form.validate_on_submit():
            answers = {key: getattr(form, key).data for key in questions_dict.keys()}
            print(f"\n=== STUDENT TEST ANSWERS ===\n{answers}\n===")

            verdict, rating = ai_exam_service.generate_verdict(
                data=data,
                questions_dict=questions_dict,
                answers_dict=answers,
            )

            # Save to DB for test
            exam_service.save_attempt_results(
                attempt_id=attempt.id,
                questions_dict=questions_dict,
                answers_dict=answers,
                code=data,
                ai_verdict=verdict,
                ai_rating=rating,
            )


            flash("Test exam finished successfully.", "success")
            return render_template("student/exam_finished.html")

        print("\n\nREPO JSON PASSED TO TEMPLATES: ", repo_data, "\n\n")

        return render_template("student/exam.html", form=form, files_json=repo_data)

    # === Fallback ===
    return render_template("student/loading.html")


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
    attempt = get_by(Attempt, exam_id=exam.id, student_id=sm.current_id())
    attempt_id = attempt.id

    # === Delete attempts seb configuration file ===
    seb_manager.Seb_manager().delete_seb_file(attempt.id)

    # === Get student content from gitHub repo etc. Code, files their names and type ===
    file_data = fetch_github_repo(
        url=attempt.github_link,
        max_files=5,
        remove_comments=True,
    )

    # === Ensure AI questions are ready (cached or async). If not - start generating questions ===
    task_id, data, status = ai_exam_service.ensure_questions_ready(
        user_id=student_id,
        file_data=file_data,
        question_count=attempt.exam.question_count
    )

    if status == "pending":
        return render_template("student/loading.html", message="Loading you exam.")

    """EXAM PROCESS"""
    if status == "done":
        exam_service.set_attempt_status(attempt_id, "ongoing")

        print(f"=Got task id={task_id}")

        # === GET QUESTIONS FROM CACHE ===
        questions_dict = data.get("questions", {})

        # === Handle bad JSON / AI error ===
        if "error" in questions_dict:
            flash(questions_dict["error"], "danger")
            return redirect(url_for("student.dashboard"))

        # === GENERATE EXAM FORM ===
        form = generate_exam_form(questions_dict)

        # === IF STUDENT SUBMITS ANSWERS ===
        if form.validate_on_submit():
            # === Collect student's answers ===
            answers = {key: getattr(form, key).data for key in questions_dict.keys()}

            # === Trigger async verdict generation ===
            verdict_task_id, verdict_data, verdict_status = ai_exam_service.ensure_verdict_ready(
                user_id=student_id,
                file_data=file_data,
                question_data=questions_dict,
                answer_data=answers,
            )

            if verdict_status == "pending":
                return render_template("student/loading.html", message="Grading your exam.")

            print("=== VERDICT STATUS: ", verdict_status, "===")

            if verdict_status == "done":

                # === Get values from cache ===
                verdict = verdict_data["verdict"]
                rating = verdict_data["rating"]

                # === Save results to database ===
                exam_service.save_attempt_results(
                    attempt_id=attempt.id,
                    questions_dict=questions_dict,
                    answers_dict=answers,
                    ai_verdict=verdict,
                    ai_rating=rating,
                    file_data=file_data,
                )

                # === Set status ===
                exam_service.set_attempt_status(attempt_id, "done")

                flash("Test exam finished successfully.", "success")
                return render_template("student/exam_finished.html")

        # === Render active exam page (if not submitted yet) ===
        return render_template("student/exam.html", form=form, attempt_files=file_data)

    # ===  Fallback ===
    return render_template("student/loading.html")


@student_bp.route('/register', methods=['GET', 'POST'])
def register():
    # === Get form template ===
    form = forms.StudentRegistrationForm()

    # === If user submits registration ===
    if form.validate_on_submit():
        try:
            # Try register
            student = user_service.create_student(
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
            student = user_service.login_student(
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
