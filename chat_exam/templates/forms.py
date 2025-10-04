from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError

#  === APPS MODELS AND UTILS ===
from chat_exam.models import Student, Exam
from chat_exam.utils.git_validator import check_github_link


class StudentRegistrationForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=4)])
    confirm_password = PasswordField("", validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField("Sign Up")

    def validate_username(self, username):
        student = Student.query.filter_by(username=username.data).first()
        if student:
            raise ValidationError("Username already in use.")

    def validate_email(self, email):
        student = Student.query.filter_by(email=email.data).first()
        if student:
            raise ValidationError("Email already registered")


class StudentLoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=4)])
    remember = BooleanField("Remember Me")
    submit = SubmitField("Login")


class TeacherLoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=4)])
    remember = BooleanField("Remember Me")
    submit = SubmitField("Login")


class StudentExamCode(FlaskForm):
    code = StringField("Code", validators=[DataRequired()])
    github_link = StringField("GitHub link", validators=[DataRequired()])
    submit = SubmitField("Enter Exam")

    def validate_code(self, field):
        exam = Exam.query.filter_by(code=field.data).first()
        if not exam:
            raise ValidationError("Invalid code")

    """def validate_github_link(self, field):
        ok, msg = check_github_link(field.data)
        if not ok:
            raise ValidationError(msg)"""


class CreatExamForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    browser_view_mode = BooleanField("Lock Down")
    allow_quit = BooleanField("Allow Quit")
    allow_clipboard = BooleanField("Allow Clipboard")

    submit = SubmitField("Create Exam")
