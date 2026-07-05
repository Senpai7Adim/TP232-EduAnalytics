"""Question 2 — Regression and correlation blueprint."""

from flask import Blueprint, render_template, request

from app.utils import charts
from app.utils.helpers import chart_colors, get_regression_service, require_dataset
from app.utils.i18n import get_language

q2_bp = Blueprint("q2", __name__)


@q2_bp.route("/", methods=["GET", "POST"])
@require_dataset
def index():
    svc = get_regression_service()
    df = svc.df
    colors = chart_colors()
    reg = svc.regression_results()
    prediction = None

    if request.method == "POST":
        try:
            prediction = svc.predict(
                float(request.form["study_hours"]),
                float(request.form["attendance"]),
                float(request.form["homework_score"]),
            )
        except (ValueError, KeyError) as exc:
            prediction = {"error": str(exc)}

    return render_template(
        "question2/index.html",
        pearson=svc.pearson_matrix(),
        spearman=svc.spearman_matrix(),
        pairwise=svc.pairwise_correlations(),
        regression=reg,
        explanation=svc.explanation(get_language()),
        prediction=prediction,
        form_data=request.form if request.method == "POST" else None,
        charts={
            "scatter_study": charts.scatter_regression(
                df, "Study_Hours", "Exam_Score", "Study Hours vs Exam Score", colors
            ),
            "scatter_attendance": charts.scatter_regression(
                df, "Attendance", "Exam_Score", "Attendance vs Exam Score", colors
            ),
            "scatter_homework": charts.scatter_regression(
                df, "Homework_Score", "Exam_Score", "Homework vs Exam Score", colors
            ),
            "residuals": charts.residual_plot(
                reg["actual"], reg["fitted"], "Residual Plot", colors
            ),
            "correlation": charts.correlation_heatmap(
                df,
                ["Study_Hours", "Exam_Score", "Attendance", "Homework_Score"],
                colors,
            ),
        },
    )
