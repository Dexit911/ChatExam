from flask import Flask, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///exam.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    app.secret_key = "super secret key"

    db.init_app(app)

    from student.routes import student_bp
    from teacher.routes import teacher_bp

    app.register_blueprint(student_bp)
    app.register_blueprint(teacher_bp)

    @app.route("/")
    def index():
        return redirect(url_for("student.student_login"))
    return app




if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)



