from flask import blueprints, render_template, session, redirect, flash, url_for
from chat_exam.models import Student, Teacher
from chat_exam.extensions import db

from chat_exam.templates import forms

student_bp = blueprints.Blueprint('student', __name__, url_prefix='/student')


@student_bp.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    # === If there is no id or role in session ===
    if 'student_id' not in session or session["role"] != "student":
        return redirect('/student/login')

    # === Get the username by the session user id ===
    student = Student.query.filter_by(id=session['student_id']).first()  # Else get student id from session
    username = student.username

    # === Render the page and pass the username ===
    form = forms.StudentExamCode()
    return render_template("student_dashboard.html", title="Enter exam", username=username, form=form)


@student_bp.route('/register', methods=['GET', 'POST'])
def register():
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



