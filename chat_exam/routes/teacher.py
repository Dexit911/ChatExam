from flask import blueprints, render_template, session, redirect, request, url_for, flash
from datetime import datetime

# ===MODELS AND EXTENSIONS===
from chat_exam.models import Teacher, Exam
from chat_exam.extensions import db
from chat_exam.templates import forms

# ===UTILS===
from chat_exam.utils.seb_manager import Seb_manager
from chat_exam.utils.link_creator import create_exam_link

teacher_bp = blueprints.Blueprint('teacher', __name__, url_prefix='/teacher')


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


@teacher_bp.route("/dashboard", methods=['GET', 'POST'])
def dashboard():
    if "teacher_id" not in session and session["role"] != "teacher":
        return redirect(url_for('teacher.login'))

    teacher = Teacher.query.filter_by(id=session["teacher_id"]).first()
    username = teacher.username
    return render_template("teacher_dashboard.html")

@teacher_bp.route('/create-exam', methods=['GET', 'POST'])
def create_exam():
    if "teacher_id" not in session:  # If there is no teacher id in session
        return redirect('/teacher/login')  # Go back to login page

    teacher = Teacher.query.filter_by(id=session["teacher_id"]).first()  # Find teacher in DataBase by id
    username = teacher.username

    if request.method == 'POST':  # If teacher clicks on create exam -> POST
        config = {  # Write down values from form checkboxes
            "browserViewMode": request.form.get('browserViewMode'),
            "allowQuit": request.form.get('allowQuit'),
            "allowClipboard": request.form.get('allowClipboard'),
        }

        # ==CREATE ENCRYPTED SEB CONFIG ==
        seb_config = Seb_manager().create_config(config)  # create xml string
        Seb_manager.create_configuration_file(seb_config)  # Save .seb file

        # ==SAVE EXAM TO DB==
        new_exam = Exam(title=request.form.get("title"), date=datetime.now())
        db.session.add(new_exam)
        db.session.commit()

        link = create_exam_link()
        print(link)

    return render_template("create_exam.html", username=username)  # When no method -> render page

