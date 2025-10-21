from flask_wtf import FlaskForm
from wtforms import SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length


def generate_exam_form(questions: dict) -> FlaskForm:
    """
    Dynamically creates a Flask-WTF form class
    with one TextAreaField per question.

    :param questions: dict with questions
    :return: Flask form, with one TextAreaField per question

    """
    class DynamicExamForm(FlaskForm):
        class Meta:
            csrf = False
        submit = SubmitField("Submit Answers")

    for key, text in questions.items():
        setattr(DynamicExamForm, key, TextAreaField(text, validators=[DataRequired(), Length(min=1, max=100)]))

    return DynamicExamForm()