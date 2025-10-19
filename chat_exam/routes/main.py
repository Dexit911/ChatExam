from pathlib import Path
import logging
from flask import Blueprint, render_template, send_file, url_for, redirect, jsonify, request, flash

from chat_exam.exceptions import AppError
from chat_exam.routes.student import student_required

logger = logging.getLogger(__name__)

# === Setup blueprint ===
main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def index():
    return render_template("start.html")


@main_bp.route("/seb-config/<int:attempt_id>.seb")
# @student_required
def seb_config(attempt_id: int):
    path = Path(__file__).resolve().parents[2] / "instance" / "seb_config" / f"exam_{attempt_id}.seb"
    return send_file(path, as_attachment=True, mimetype="application/seb")


@main_bp.route("/exam-link/<int:attempt_id>")
# @student_required
def exam_link(attempt_id: int):
    https_url = url_for("main.seb_config", attempt_id=attempt_id, _external=True)
    sebs_url = https_url.replace("http://", "seb://").replace("https://", "seb://")

    logger.info(f"SEB link generated: {sebs_url}")
    return redirect(sebs_url)


# === Error handler for all AppError exceptions ===
@main_bp.app_errorhandler(AppError)
def handle_app_error(e: AppError):
    logger.error(f"{e.code}: {e.message}")

    # API responses
    if request.path.startswith("/api/"):
        return jsonify({"error": e.code, "message": e.message}), e.status_code

    # Flash only if public
    if e.public:
        flash(e.message, "danger")
    else:
        flash("An unexpected error occurred. Please try again later.", "danger")

    return redirect(url_for("main.index"))
