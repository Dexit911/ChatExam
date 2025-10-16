import logging

from flask import Flask

from chat_exam.extensions import db
from chat_exam.routes import blueprints



def create_app():
    app = Flask(__name__)
    app.config.from_object("chat_exam.config.Config")

    # --- Logging setup (runs once) ---
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler("app.log"),
            logging.StreamHandler()
        ]
    )
    logging.info("Logging configured")






    # === DB setup ===
    db.init_app(app)

    with app.app_context():
        db.create_all()

    # === Blueprint ===
    for blueprint in blueprints:
        app.register_blueprint(blueprint)

    # === Return whole app ===
    return app
