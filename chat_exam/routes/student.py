# === FLASK AND OTHER IMPORTS ===
from flask import blueprints, render_template, session, redirect, flash, url_for, request, abort
from functools import wraps

# === CHAT_EXAM IMPORTS ===
from chat_exam.models import Student, Teacher, Exam, StudentExam, StudentTeacher
from chat_exam.extensions import db
from chat_exam.templates import forms
from chat_exam.config import DEBUG, TEST_LINK
from chat_exam.utils.git_fecther import fetch_github_code

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

@student_bp.route("/exam/<code>")
#@student_required
def exam(code):
    # === Check if the request happens from SEB protocol ===
    ua = request.headers.get("User-Agent", "")
    if "SafeExamBrowser" not in ua:
        abort(403, description="This exam must be taken in Safe Exam Browser")
    print("===THE EXAM IS TAKEN IN SEB ENV ===")

    student_github_link = TEST_LINK
    code_text = fetch_github_code(student_github_link)

    print(f"=== EXTRACTED CODE FROM GITHUB LINK ===\n\n{code_text}\n\n=============")

    return render_template("student/exam.html", code_text=code_text)







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








