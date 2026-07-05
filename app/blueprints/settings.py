"""Settings blueprint — theme, language, animations."""

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app.utils.i18n import t

settings_bp = Blueprint("settings", __name__)


@settings_bp.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        session["theme"] = request.form.get("theme", "light")
        session["language"] = request.form.get("language", "en")
        session["animations"] = request.form.get("animations") == "on"
        session.modified = True
        flash("Settings saved.", "success")
        return redirect(url_for("settings.index"))

    return render_template(
        "settings/index.html",
        current_theme=session.get("theme", "light"),
        current_language=session.get("language", "en"),
        animations_enabled=session.get("animations", True),
    )
