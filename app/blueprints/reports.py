"""Reports blueprint — compile and export analytical reports."""

from datetime import datetime
from pathlib import Path

from flask import Blueprint, current_app, flash, redirect, render_template, send_file, session, url_for

from app.services.report_service import ReportService
from app.utils.helpers import get_data_manager, require_dataset
from app.utils.i18n import get_language, t

reports_bp = Blueprint("reports", __name__)


@reports_bp.route("/")
@require_dataset
def index():
    dm = get_data_manager()
    leader = session.get("leader_name", "Unknown")
    report = ReportService(dm.load(), leader, session.get("dataset_seed", 42)).compile(
        get_language()
    )
    return render_template("reports/index.html", report=report)


@reports_bp.route("/export/pdf")
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
    flash("PDF report generated.", "success")
    return send_file(path, as_attachment=True, download_name=filename)


@reports_bp.route("/export/csv")
@require_dataset
def export_csv():
    dm = get_data_manager()
    path = dm.export_csv_path()
    return send_file(path, as_attachment=True, download_name=path.name)


@reports_bp.route("/export/charts")
@require_dataset
def export_charts():
    """Export analytical charts as a ZIP of PNG images."""
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
    flash("Chart images exported.", "success")
    return send_file(path, as_attachment=True, download_name=filename)
