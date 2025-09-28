from flask import blueprints, render_template, session, redirect, request
from datetime import datetime

# ===MODELS AND EXTENSIONS===
from chat_exam.models import Teacher, Exam
from chat_exam.extensions import db

# ===UTILS===
from chat_exam.utils.seb_manager import Seb_manager
from chat_exam.utils.link_creator import create_exam_link

teacher_bp = blueprints.Blueprint('teacher', __name__, url_prefix='/teacher')


@teacher_bp.route('/login', methods=['GET', 'POST'])
def teacher_login():
    if request.method == 'POST':

        username = request.form['username']  # Get username from form
        password = request.form['password']  # Get password from form

        teacher = Teacher.query.filter_by(username=username).first()  # Find teacher by username in DataBase

        if teacher and teacher.check_password(password):  # If found teacher and password is correct
            session["teacher_id"] = teacher.id  # Set current session teacher id
            return redirect('/teacher/create-exam')  # Redirect to page where you can create your exam
        else:
            print("invalid username or password")  # Else wrong logins

    return render_template("teacher_login.html")  # If no post method -> render the login page


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
