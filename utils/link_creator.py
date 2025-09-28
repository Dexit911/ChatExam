import socket

from flask import url_for

def create_exam_link() -> None:
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)

    # Build the URL (e.g. http://192.168.1.100:5000/student/login)
    return f"http://{local_ip}:5000" + url_for("student_login")



