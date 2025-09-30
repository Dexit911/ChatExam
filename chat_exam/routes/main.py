from flask import Blueprint, redirect, render_template

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def index():
    return render_template("start.html")
