"""REST API blueprint — JSON endpoints and SPA partial views."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from flask import Blueprint, current_app, jsonify, render_template, request, send_file, session

from app.services.dataset_generator import seed_from_leader_name
from app.services.report_service import ReportService
from app.services.view_context import (
    dashboard_context,
    dataset_context,
    question1_context,
    question2_context,
    question3_context,
    question4_context,
    reports_context,
    settings_context,
)
from app.utils.helpers import (
    get_classification_service,
    get_dashboard_service,
    get_data_manager,
    get_regression_service,
    require_dataset,
    template_context,
)
from app.utils.i18n import get_language, t
from app.utils.spa import json_error

api_bp = Blueprint("api", __name__)

PARTIAL_MAP = {
    "dashboard": ("partials/dashboard.html", dashboard_context),
    "dataset": ("partials/dataset.html", dataset_context),
    "question-1": ("partials/question1.html", question1_context),
    "question-2": ("partials/question2.html", question2_context),
    "question-3": ("partials/question3.html", question3_context),
    "question-4": ("partials/question4.html", question4_context),
    "reports": ("partials/reports.html", reports_context),
    "settings": ("partials/settings.html", settings_context),
    "about": ("partials/about.html", lambda: {}),
}


@api_bp.route("/health")
def health():
    return jsonify({"status": "ok", "version": current_app.config["VERSION"]})


@api_bp.route("/session")
def session_info():
    """Return session metadata for topbar/sidebar updates."""
    dm = get_data_manager()
    return jsonify(
        {
            "has_dataset": dm.has_dataset(),
            "meta": dm.session_meta(),
            "settings": {
                "theme": session.get("theme", "light"),
                "language": session.get("language", "en"),
                "animations": session.get("animations", True),
            },
        }
    )


@api_bp.route("/views/<page>")
def partial_view(page: str):
    """Return rendered HTML partial for SPA navigation."""
    if page not in PARTIAL_MAP:
        return json_error("Page not found", 404)

    dm = get_data_manager()
    needs_dataset = page not in ("dataset", "settings", "about")
    if needs_dataset and not dm.has_dataset():
        return json_error(t("no_dataset"), 404, redirect="/dataset/")

    template_name, builder = PARTIAL_MAP[page]
    ctx = builder()

    if page == "question-3":
        k = request.args.get("k", type=int)
        if k:
            ctx = question3_context(k)

    html = render_template(template_name, **template_context(), **ctx)
    titles = {
        "dashboard": t("nav_dashboard"),
        "dataset": t("nav_dataset"),
        "question-1": t("q1_title"),
        "question-2": t("q2_title"),
        "question-3": t("q3_title"),
        "question-4": t("q4_title"),
        "reports": t("reports_title"),
        "settings": t("settings_title"),
        "about": t("about_title"),
    }
    return jsonify({"success": True, "html": html, "title": titles.get(page, page), "page": page})


@api_bp.route("/kpis")
@require_dataset
def kpis():
    return jsonify({"success": True, "kpis": get_dashboard_service().kpis()})


@api_bp.route("/dataset/preview")
def dataset_preview():
    """Paginated dataset table data."""
    dm = get_data_manager()
    if not dm.has_dataset():
        return jsonify({"success": True, "rows": [], "total": 0, "page": 1, "pages": 1})
    data = dm.preview_paginated(
        page=request.args.get("page", 1, type=int),
        per_page=request.args.get("per_page", 15, type=int),
        search=request.args.get("search", "", type=str),
        sort=request.args.get("sort", "Student_ID", type=str),
        order=request.args.get("order", "asc", type=str),
    )
    return jsonify({"success": True, **data})


@api_bp.route("/dataset/generate", methods=["POST"])
def generate_dataset():
    """Generate dataset asynchronously without page reload."""
    data = request.get_json(silent=True) or {}
    try:
        leader = str(data.get("leader_name", "")).strip()
        num_students = int(data.get("num_students", 100))
        if not leader:
            raise ValueError("Group leader name is required.")

        dm = get_data_manager()
        dm.generate(leader, num_students)
        seed = seed_from_leader_name(leader)
        paginated = dm.preview_paginated(page=1, per_page=15)

        return jsonify(
            {
                "success": True,
                "message": f"Dataset generated: {num_students} students (seed: {seed})",
                "meta": dm.session_meta(),
                "seed": seed,
                "preview": paginated["rows"],
                "pagination": paginated,
            }
        )
    except (ValueError, TypeError) as exc:
        return json_error(str(exc), 400)


@api_bp.route("/dataset/import", methods=["POST"])
def import_dataset():
    """Import CSV without page reload."""
    try:
        if "csv_file" not in request.files:
            raise ValueError("Please select a CSV file.")
        file = request.files["csv_file"]
        if not file.filename:
            raise ValueError("Please select a CSV file.")

        dm = get_data_manager()
        dm.import_csv(file)
        paginated = dm.preview_paginated(page=1, per_page=15)

        return jsonify(
            {
                "success": True,
                "message": "Dataset imported successfully.",
                "meta": dm.session_meta(),
                "preview": paginated["rows"],
                "pagination": paginated,
            }
        )
    except (ValueError, TypeError) as exc:
        return json_error(str(exc), 400)


@api_bp.route("/dataset/download")
def download_dataset():
    dm = get_data_manager()
    if not dm.has_dataset():
        return json_error(t("no_dataset"), 404)
    path = dm.export_csv_path()
    return send_file(path, as_attachment=True, download_name=path.name)


@api_bp.route("/predict/exam", methods=["POST"])
@require_dataset
def predict_exam():
    data = request.get_json(silent=True) or {}
    try:
        result = get_regression_service().predict(
            float(data["study_hours"]),
            float(data["attendance"]),
            float(data["homework_score"]),
        )
        return jsonify({"success": True, "prediction": result})
    except (KeyError, ValueError, TypeError) as exc:
        return json_error(str(exc), 400)


@api_bp.route("/predict/orientation", methods=["POST"])
@require_dataset
def predict_orientation():
    data = request.get_json(silent=True) or {}
    try:
        result = get_classification_service().predict_orientation(
            float(data["study_hours"]),
            float(data["attendance"]),
            float(data["homework_score"]),
        )
        return jsonify({"success": True, "prediction": result})
    except (KeyError, ValueError, TypeError) as exc:
        return json_error(str(exc), 400)


@api_bp.route("/settings", methods=["POST"])
def save_settings():
    data = request.get_json(silent=True) or {}
    session["theme"] = data.get("theme", "light")
    session["language"] = data.get("language", "en")
    session["animations"] = bool(data.get("animations", True))
    session.modified = True
    return jsonify(
        {
            "success": True,
            "message": "Settings saved.",
            "settings": {
                "theme": session["theme"],
                "language": session["language"],
                "animations": session["animations"],
            },
        }
    )


@api_bp.route("/reports/export/pdf")
@require_dataset
def export_pdf():
    dm = get_data_manager()
    leader = session.get("leader_name", "report")
    reports_dir = Path(current_app.config["REPORTS_DIR"])
    filename = f"report_{leader.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    path = reports_dir / filename
    ReportService(dm.load(), leader, session.get("dataset_seed", 42)).export_pdf(
        path, get_language()
    )
    return send_file(path, as_attachment=True, download_name=filename)


@api_bp.route("/reports/export/csv")
@require_dataset
def export_csv():
    dm = get_data_manager()
    path = dm.export_csv_path()
    return send_file(path, as_attachment=True, download_name=path.name)


@api_bp.route("/reports/export/charts")
@require_dataset
def export_charts():
    dm = get_data_manager()
    leader = session.get("leader_name", "report")
    exports_dir = Path(current_app.config["EXPORTS_DIR"])
    filename = f"charts_{leader.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.zip"
    path = exports_dir / filename
    ReportService(
        dm.load(),
        leader,
        session.get("dataset_seed", 42),
        current_app.config.get("CHART_COLORS"),
    ).export_charts_zip(path)
    return send_file(path, as_attachment=True, download_name=filename)


@api_bp.route("/seed/<leader_name>")
def preview_seed(leader_name: str):
    return jsonify({"seed": seed_from_leader_name(leader_name)})


@api_bp.route("/search")
def search():
    dm = get_data_manager()
    if not dm.has_dataset():
        return jsonify({"results": []})
    q = request.args.get("q", "").strip().lower()
    if not q:
        return jsonify({"results": []})
    df = dm.load()
    mask = (
        df["Student_ID"].str.lower().str.contains(q, na=False)
        | df["Orientation"].str.lower().str.contains(q, na=False)
    )
    results = df[mask].head(20).to_dict(orient="records")
    return jsonify({"results": results})
