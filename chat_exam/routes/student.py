# === FLASK AND OTHER IMPORTS ===
from flask import blueprints, render_template, session, redirect, flash, url_for, request, abort
from functools import wraps
import json

# === CHAT_EXAM IMPORTS ===
from chat_exam.models import Student, Teacher, Exam, StudentExam, StudentTeacher
from chat_exam.extensions import db
from chat_exam.templates import forms
from chat_exam.config import TEST_LINK
from chat_exam.utils.git_fecther import fetch_github_code
from chat_exam.utils.generate_exam_form import generate_exam_form
from chat_exam.utils.ai_examinator import AIExaminator

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
        # === Get exam_id and github_link from form ===
        print("Success! Entering exam")
        exam_id = Exam.query.filter_by(code=form.code.data).first().id
        teacher_id = Exam.query.filter_by(code=form.code.data).first().teacher_id

        github_link = form.github_link.data

        # === Save student linked to exam ===
        attempt = StudentExam(
            exam_id=exam_id,
            student_id=session["student_id"],
            github_link=github_link,
            status = "ongoing",
        )
        db.session.add(attempt)
        print("===NEW ATTEMPT ADDED===")

        # === Check if the Teacher had this student, if not: link student to teacher ===
        old_student = StudentTeacher.query.filter_by(student_id=session["student_id"]).first()
        if not old_student:
            student_to_teacher = StudentTeacher(
                student_id=session["student_id"],
                teacher_id=teacher_id,
            )
            db.session.add(student_to_teacher)
            print("===NEW STUDENT ADDED TO TEACHER===")

        db.session.commit()

        # === Redirect student to exam by the exam code ===
        seb_url = url_for("main.exam_link", exam_id=exam_id, _external=True)
        return redirect(seb_url)

    # === Get the username by the session user id ===
    student = Student.query.filter_by(id=session['student_id']).first()  # Else get student id from session
    username = student.username

    # === Render the page and pass the username ===
    return render_template("student_dashboard.html", title="Enter exam", username=username, form=form)


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
    student_github_link = StudentExam.query.filter_by(exam_id=exam_id, student_id=session["student_id"]).first().github_link
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

        # === Save student to db ===
        email = form.email.data
        username = form.username.data
        password = form.password.data
        new_student = Student(username=username, email=email)
        new_student.set_password(password)
        db.session.add(new_student)
        db.session.commit()

        # === DEBUG ===
        teacher = Teacher(username="admin", email="admin@exam.com")
        teacher.set_password("123456")
        db.session.add(teacher)
        db.session.commit()

        # === If valid saved registration, set session to current user and redirect to dashboard ===
        student = Student.query.filter_by(email=email).first()
        if student:
            session['student_id'] = student.id
            session['role'] = "student"

            flash(f"Account created for {form.username.data}!", "success")
            return redirect(url_for('student.dashboard'))

    # === If no method -> render page ===
    return render_template("student_register.html", title="Test Register", form=form)


@student_bp.route('/login', methods=['GET', 'POST'])
def login():
    # === Get form template ===
    form = forms.StudentLoginForm()

    # === If form is submitted ===
    if form.validate_on_submit():
        """# === Check if admin ===
        if form.email.data == "admin@exam.com" and form.password.data == "1234":
            flash("Login successful", "success")
            return redirect(url_for('student.dashboard'))"""

        # === Get data from form and search for user in db ===
        email = form.email.data
        password = form.password.data
        student = Student.query.filter_by(email=email).first()  # Find the student by email

        # === If there is student and the password is matching, set session id and role ===
        if student and student.check_password(password):
            session['student_id'] = student.id
            session['role'] = "student"
            return redirect(url_for('student.dashboard'))

        # === If login fails, give message to user ===
        else:
            flash("Login unsuccessful", "danger")

    # === If no method, render the page ===
    return render_template("student_login.html", title="Test Login", form=form)
