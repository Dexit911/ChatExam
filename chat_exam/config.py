import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))  # chat_exam/
DB_PATH = os.path.join(BASE_DIR, "..", "instance", "app.db")
DEBUG = True



ATTEMPT_FILES_PATH = f"instance/attempt_data/" # {attempt_id}.json"




class Config:

    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False


