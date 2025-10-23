import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))  # chat_exam/
DB_PATH = os.path.join(BASE_DIR, "..", "instance", "app.db")
DEBUG = True

AI_KEY = "AIzaSyALxtsSkFVyLiHJLRmJXlkC1JJYRY1jiwI"
SINGLE_GITHUB_TEST_LINK = "https://github.com/Dexit911/StudentTest/blob/master/main.py"

ATTEMPT_FILES_PATH = f"instance/attempt_data/" # {attempt_id}.json"




class Config:
    SECRET_KEY = 'aee7d73d54fb1a5b16f94a693ee0c26f'
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
