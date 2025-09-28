from flask import Blueprint

student_bp = Blueprint('student', __name__, url_prefix='/student')

from . import routes # attach routes to this blueprint