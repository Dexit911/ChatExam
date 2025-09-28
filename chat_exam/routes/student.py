from flask import blueprints, render_template, session, redirect, request
from chat_exam.models import Student
from chat_exam.extensions import db

student_bp = blueprints.Blueprint('student', __name__, url_prefix='/student')



"""---STUDENT---"""
@student_bp.route('/login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':  # If the form is submitted
        email = request.form['email']  # Get email from the form
        password = request.form['password']  # Get password from the form

        student = Student.query.filter_by(email=email).first()  # Find the student by email

        if student and student.check_password(password):  # If there is student and the password is correct
            session['student_id'] = student.id  # Save student id in the session
            return redirect('/student/start-exam')  # Go to next page
        else:
            print("invalid password or email")

    return render_template("student_login.html")  # If the form is not submitted render the website


@student_bp.route('/register', methods=['GET', 'POST'])
def student_register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        new_user = Student(username=username, email=email)
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        teacher = Teacher(username="admin")
        teacher.set_password("123")

        db.session.add(teacher)
        db.session.commit()

        return redirect('/student/login')
    return render_template("student_register.html")


@student_bp.route('/start-exam', methods=['GET', 'POST'])
def student_start_exam():
    if 'student_id' not in session:  # If no student id in session redirect back to login
        return redirect('/student/login')

    student = Student.query.filter_by(id=session['student_id']).first()  # Else get student id from session
    return render_template("student_start_exam.html")
