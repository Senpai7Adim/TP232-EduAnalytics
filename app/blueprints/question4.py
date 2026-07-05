"""Question 4 — Supervised classification blueprint."""

from flask import Blueprint, render_template, request

from app.utils import charts
from app.utils.helpers import chart_colors, get_classification_service, require_dataset

q4_bp = Blueprint("q4", __name__)


@q4_bp.route("/", methods=["GET", "POST"])
@require_dataset
def index():
    svc = get_classification_service()
    colors = chart_colors()
    comparison = svc.comparison_table()
    best = svc.best_model_results()
    prediction = None

    if request.method == "POST":
        try:
            prediction = svc.predict_orientation(
                float(request.form["study_hours"]),
                float(request.form["attendance"]),
                float(request.form["homework_score"]),
            )
        except (ValueError, KeyError) as exc:
            prediction = {"error": str(exc)}

    roc_chart = ""
    if best.get("roc") and best.get("auc"):
        roc_chart = charts.roc_curve_chart(
            best["roc"]["fpr"], best["roc"]["tpr"], best["auc"], colors
        )

    fi_chart = ""
    if best.get("feature_importance"):
        fi_chart = charts.feature_importance_chart(best["feature_importance"], colors)

    return render_template(
        "question4/index.html",
        comparison=comparison,
        best=best,
        best_model_name=svc.best_model_name,
        prediction=prediction,
        form_data=request.form if request.method == "POST" else None,
        charts={
            "comparison": charts.model_comparison_chart(comparison, colors),
            "confusion": charts.confusion_matrix_chart(
                best["confusion_matrix"], ["Literary", "Scientific"], colors
            ),
            "roc": roc_chart,
            "feature_importance": fi_chart,
        },
    )
