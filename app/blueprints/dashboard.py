"""Dashboard blueprint — executive KPIs and charts."""

from flask import Blueprint, render_template, session

from app.utils.helpers import get_dashboard_service, require_dataset

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
@require_dataset
def index():
    svc = get_dashboard_service()
    leader = session.get("leader_name", "Default")
    return render_template(
        "dashboard/index.html",
        kpis=svc.kpis(),
        charts=svc.charts(leader),
        preview=svc.preview(),
    )
