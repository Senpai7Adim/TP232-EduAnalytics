"""
Dashboard aggregation service.

Combines dataset summary, classification accuracy, and chart payloads
for the executive dashboard view.
"""

from __future__ import annotations

from flask import session

import pandas as pd

from app.services.classification_service import ClassificationService
from app.services.dataset_generator import weekly_trend_data
from app.utils import charts


class DashboardService:
    """Assemble KPIs and visualisations for the main dashboard."""

    def __init__(self, df: pd.DataFrame, colors: list[str], random_state: int = 42):
        self.df = df
        self.colors = colors
        self.random_state = random_state
        self._classifier: ClassificationService | None = None

    def _get_classifier(self) -> ClassificationService:
        if self._classifier is None:
            self._classifier = ClassificationService(
                self.df, random_state=self.random_state
            )
        return self._classifier

    def kpis(self) -> dict:
        """Animated KPI card values."""
        df = self.df
        try:
            accuracy = round(self._get_classifier().best_accuracy * 100, 1)
        except Exception:
            accuracy = 0.0

        return {
            "total_students": len(df),
            "avg_exam_score": round(df["Exam_Score"].mean(), 1),
            "avg_study_hours": round(df["Study_Hours"].mean(), 1),
            "highest_score": int(df["Exam_Score"].max()),
            "lowest_score": int(df["Exam_Score"].min()),
            "scientific_count": int((df["Orientation"] == "Scientific").sum()),
            "literary_count": int((df["Orientation"] == "Literary").sum()),
            "prediction_accuracy": accuracy,
        }

    def charts(self, leader_name: str) -> dict[str, str]:
        """Generate all dashboard Plotly chart JSON payloads."""
        weekly = weekly_trend_data(self.df, leader_name)
        return {
            "study_hours_dist": charts.histogram(
                self.df, "Study_Hours", "Study Hours Distribution", self.colors
            ),
            "exam_score_dist": charts.histogram(
                self.df, "Exam_Score", "Exam Score Distribution", self.colors
            ),
            "orientation_pie": charts.pie_chart(
                self.df, "Orientation", "Student Orientation", self.colors
            ),
            "weekly_trend": charts.line_chart(
                weekly,
                "Week",
                "Average_Exam_Score",
                "Weekly Performance Trend",
                self.colors,
            ),
            "correlation_heatmap": charts.correlation_heatmap(
                self.df,
                ["Study_Hours", "Exam_Score", "Attendance", "Homework_Score"],
                self.colors,
            ),
        }

    def preview(self, limit: int = 8) -> list[dict]:
        """Recent dataset records for dashboard table."""
        return self.df.head(limit).to_dict(orient="records")
