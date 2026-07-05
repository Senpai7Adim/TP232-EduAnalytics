"""
View context builders — shared between blueprints and SPA API routes.

Centralises data assembly so partial renders and JSON responses stay consistent.
"""

from __future__ import annotations

from flask import session

from app.services.report_service import ReportService
from app.utils import charts
from app.utils.helpers import (
    chart_colors,
    get_classification_service,
    get_clustering_service,
    get_dashboard_service,
    get_data_manager,
    get_descriptive_service,
    get_regression_service,
    random_state,
)
from app.utils.i18n import get_language


def dataset_context() -> dict:
    """Context for the dataset management view."""
    dm = get_data_manager()
    from app.services.dataset_generator import seed_from_leader_name

    meta = dm.session_meta()
    seed_preview = None
    if meta.get("leader_name"):
        seed_preview = seed_from_leader_name(meta["leader_name"])

    paginated = (
        dm.preview_paginated(page=1, per_page=15)
        if dm.has_dataset()
        else {"rows": [], "total": 0, "page": 1, "pages": 1}
    )

    return {
        "meta": meta,
        "preview": paginated["rows"],
        "pagination": paginated,
        "seed_preview": seed_preview,
    }


def dashboard_context() -> dict:
    """Context for the executive dashboard."""
    dm = get_data_manager()
    svc = get_dashboard_service()
    leader = session.get("leader_name", "Default")
    return {
        "kpis": svc.kpis(),
        "charts": svc.charts(leader),
        "preview": svc.preview(),
    }


def question1_context() -> dict:
    """Context for descriptive statistics (Question 1)."""
    svc = get_descriptive_service()
    df = svc.df
    colors = chart_colors()
    return {
        "stats": svc.compute(),
        "table_rows": svc.table_rows(),
        "explanation": svc.explanation(get_language()),
        "charts": {
            "histogram": charts.histogram(df, "Exam_Score", "Exam Score Histogram", colors),
            "boxplot": charts.box_plot(df, "Exam_Score", "Box Plot", colors),
            "violin": charts.violin_plot(df, "Exam_Score", "Violin Plot", colors),
            "density": charts.density_curve(df, "Exam_Score", "Density Curve", colors),
        },
    }


def question2_context(prediction: dict | None = None, form_data=None) -> dict:
    """Context for regression analysis (Question 2)."""
    svc = get_regression_service()
    df = svc.df
    colors = chart_colors()
    reg = svc.regression_results()
    return {
        "pearson": svc.pearson_matrix(),
        "spearman": svc.spearman_matrix(),
        "pairwise": svc.pairwise_correlations(),
        "regression": reg,
        "explanation": svc.explanation(get_language()),
        "prediction": prediction,
        "form_data": form_data,
        "charts": {
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
    }


def question3_context(n_clusters: int | None = None) -> dict:
    """Context for K-Means clustering (Question 3)."""
    svc = get_clustering_service()
    colors = chart_colors()
    result = svc.run(n_clusters)
    elbow = svc.elbow_data()
    silhouette = svc.silhouette_data()
    return {
        "result": result,
        "n_clusters": n_clusters or result["n_clusters"],
        "charts": {
            "elbow": charts.elbow_chart(
                elbow["k"], elbow["inertia"], result["optimal_k"], colors
            ),
            "silhouette": charts.silhouette_chart(
                silhouette["k"], silhouette["scores"], colors
            ),
            "clusters": charts.cluster_scatter(
                result["pca_x"],
                result["pca_y"],
                result["labels"],
                "Cluster Visualization (PCA)",
                colors,
            ),
            "radar": charts.radar_chart(result["profiles"], colors),
        },
    }


def question4_context(prediction: dict | None = None, form_data=None) -> dict:
    """Context for supervised classification (Question 4)."""
    svc = get_classification_service()
    colors = chart_colors()
    comparison = svc.comparison_table()
    best = svc.best_model_results()

    roc_chart = ""
    if best.get("roc") and best.get("auc"):
        roc_chart = charts.roc_curve_chart(
            best["roc"]["fpr"], best["roc"]["tpr"], best["auc"], colors
        )

    fi_chart = ""
    if best.get("feature_importance"):
        fi_chart = charts.feature_importance_chart(best["feature_importance"], colors)

    return {
        "comparison": comparison,
        "best": best,
        "best_model_name": svc.best_model_name,
        "prediction": prediction,
        "form_data": form_data,
        "charts": {
            "comparison": charts.model_comparison_chart(comparison, colors),
            "confusion": charts.confusion_matrix_chart(
                best["confusion_matrix"], ["Literary", "Scientific"], colors
            ),
            "roc": roc_chart,
            "feature_importance": fi_chart,
        },
    }


def reports_context() -> dict:
    """Context for the professional report view."""
    dm = get_data_manager()
    leader = session.get("leader_name", "Unknown")
    report = ReportService(
        dm.load(), leader, session.get("dataset_seed", 42)
    ).compile(get_language())
    return {"report": report}


def settings_context() -> dict:
    """Context for user settings."""
    return {
        "current_theme": session.get("theme", "light"),
        "current_language": session.get("language", "en"),
        "animations_enabled": session.get("animations", True),
    }
