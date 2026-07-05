"""Question 1 — Descriptive statistics blueprint."""

from flask import Blueprint, render_template, session

from app.utils import charts
from app.utils.helpers import chart_colors, get_descriptive_service, require_dataset
from app.utils.i18n import get_language

q1_bp = Blueprint("q1", __name__)


@q1_bp.route("/")
@require_dataset
def index():
    svc = get_descriptive_service()
    df = svc.df
    colors = chart_colors()
    stats = svc.compute()
    return render_template(
        "question1/index.html",
        stats=stats,
        table_rows=svc.table_rows(),
        explanation=svc.explanation(get_language()),
        charts={
            "histogram": charts.histogram(df, "Exam_Score", "Exam Score Histogram", colors),
            "boxplot": charts.box_plot(df, "Exam_Score", "Box Plot", colors),
            "violin": charts.violin_plot(df, "Exam_Score", "Violin Plot", colors),
            "density": charts.density_curve(df, "Exam_Score", "Density Curve", colors),
        },
    )
