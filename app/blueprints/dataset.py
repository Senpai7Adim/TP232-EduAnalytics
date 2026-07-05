"""Dataset generation, import, and export blueprint."""

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)

from app.services.dataset_generator import seed_from_leader_name
from app.utils.helpers import get_data_manager
from app.utils.i18n import t

dataset_bp = Blueprint("dataset", __name__)


@dataset_bp.route("/", methods=["GET", "POST"])
def index():
    dm = get_data_manager()
    meta = dm.session_meta()
    preview = dm.preview(15) if dm.has_dataset() else []
    seed_preview = None

    if request.method == "POST":
        action = request.form.get("action", "generate")
        try:
            if action == "generate":
                leader = request.form.get("leader_name", "").strip()
                num_students = int(request.form.get("num_students", 100))
                if not leader:
                    raise ValueError("Group leader name is required.")
                dm.generate(leader, num_students)
                flash(
                    f"Dataset generated: {num_students} students (seed: {seed_from_leader_name(leader)})",
                    "success",
                )
                return redirect(url_for("dashboard.index"))

            if action == "import" and "csv_file" in request.files:
                file = request.files["csv_file"]
                if not file.filename:
                    raise ValueError("Please select a CSV file.")
                dm.import_csv(file)
                flash("Dataset imported successfully.", "success")
                return redirect(url_for("dashboard.index"))

        except (ValueError, TypeError) as exc:
            flash(str(exc), "danger")

    if meta.get("leader_name"):
        seed_preview = seed_from_leader_name(meta["leader_name"])

    return render_template(
        "dataset/index.html",
        meta=meta,
        preview=preview,
        seed_preview=seed_preview,
    )


@dataset_bp.route("/download")
def download():
    dm = get_data_manager()
    if not dm.has_dataset():
        flash(t("no_dataset"), "warning")
        return redirect(url_for("dataset.index"))
    path = dm.export_csv_path()
    return send_file(path, as_attachment=True, download_name=path.name)
