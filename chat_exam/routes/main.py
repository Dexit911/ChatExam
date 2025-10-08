from flask import Blueprint, render_template, send_file, url_for, request, redirect, flash, session
from .student import student_required
import os

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def index():
    return render_template("start.html")

@main_bp.route("/seb-config/<int:exam_id>.seb")
@student_required
def seb_config(exam_id):
    """if "student_id" not in session or session.get("role") != "student":
        flash("You must be logged in as a student to access this exam.", "danger")
        return redirect(url_for("student.login"))"""

    return send_file(
        os.path.join("seb_config", f"exam_{exam_id}.seb"),
        as_attachment=True,
        mimetype="application/seb"
    )
@main_bp.route("/exam-link/<int:exam_id>")
@student_required
def exam_link(exam_id):
    # normal https URL for config
    https_url = url_for("main.seb_config", exam_id=exam_id, _external=True)
    # turn into SEB protocol link
    sebs_url = https_url.replace("http://", "seb://").replace("https://", "seb://")
    # redirect student’s browser to sebs://
    print("===SEB URL===")
    print(sebs_url)
    return redirect(sebs_url)
