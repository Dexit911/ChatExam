from flask import Flask
from chat_exam.extensions import db
from chat_exam.routes import blueprints



def create_app():
    app = Flask(__name__)
    app.config.from_object("chat_exam.config.Config")

    # here we connect the db to the app
    db.init_app(app)

    # register routes
    for blueprint in blueprints:
        app.register_blueprint(blueprint)

    with app.app_context():
        db.create_all()

    return app
