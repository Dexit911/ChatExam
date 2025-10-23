import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))  # chat_exam/
DB_PATH = os.path.join(BASE_DIR, "..", "instance", "app.db")
DEBUG = True



ATTEMPT_FILES_PATH = f"instance/attempt_data/" # {attempt_id}.json"




class Config:

    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'aee7d73d54fb1a5b16f94a693ee0c26f'
    GITHUB_FETCH_TOKEN = "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"
    AI_KEY = "AIzaSyALxtsSkFVyLiHJLRmJXlkC1JJYRY1jiwI"


