from flask import Blueprint, render_template, send_file, url_for, redirect
from pathlib import Path
from .student import student_required

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def index():
    return render_template("start.html")


@main_bp.route("/seb-config/<int:attempt_id>.seb")
#@student_required
def seb_config(attempt_id: int):

    path = Path(__file__).resolve().parents[2] / "instance" / "seb_config" / f"exam_{attempt_id}.seb"

    return send_file(
        path,
        as_attachment=True,
        mimetype="application/seb"
    )


@main_bp.route("/exam-link/<int:attempt_id>")
#@student_required
def exam_link(attempt_id: int):
    # Normal HTTPS URL for config
    https_url = url_for("main.seb_config", attempt_id=attempt_id, _external=True)

    # Replace protocol so SEB handles it
    sebs_url = https_url.replace("http://", "seb://").replace("http://", "seb://")

    print("=== SEB LINK GENERATED ===")
    print(sebs_url)

    # Redirect browser to SEB protocol
    return redirect(sebs_url)

#