import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))  # chat_exam/
DB_PATH = os.path.join(BASE_DIR, "..", "instance", "app.db")
DEBUG = True

AI_KEY = "AIzaSyDot3SEP_yoBihXNvS55k7TB4AscgF546c"
TEST_LINK = "https://github.com/Dexit911/StudentTest/blob/master/main.py"

MAX_QUESTION_COUNT = 10



class Config:
    SECRET_KEY = 'aee7d73d54fb1a5b16f94a693ee0c26f'
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
