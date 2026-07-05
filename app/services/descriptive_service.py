"""
Descriptive statistics service — Question 1.

Computes comprehensive univariate statistics and generates educational
interpretations for exam score distributions.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats


class DescriptiveStatisticsService:
    """Business logic for Question 1: descriptive analysis of Exam_Score."""

    TARGET = "Exam_Score"

    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.series = df[self.TARGET].dropna().astype(float)

    def compute(self) -> dict:
        """Calculate all required descriptive statistics."""
        s = self.series
        q1, q2, q3 = s.quantile([0.25, 0.5, 0.75])
        iqr = q3 - q1
        lower_fence = q1 - 1.5 * iqr
        upper_fence = q3 + 1.5 * iqr
        outliers = s[(s < lower_fence) | (s > upper_fence)]

        mode_result = stats.mode(s, keepdims=True)
        mode_val = float(mode_result.mode[0]) if len(mode_result.mode) else float(s.iloc[0])
        mean_val = float(s.mean())
        std_val = float(s.std(ddof=1))
        cv = (std_val / mean_val * 100) if mean_val else 0.0

        return {
            "variable": self.TARGET,
            "count": int(s.count()),
            "mean": round(mean_val, 3),
            "median": round(float(s.median()), 3),
            "mode": round(mode_val, 3),
            "min": round(float(s.min()), 3),
            "max": round(float(s.max()), 3),
            "variance": round(float(s.var(ddof=1)), 3),
            "std": round(std_val, 3),
            "q1": round(float(q1), 3),
            "q2": round(float(q2), 3),
            "q3": round(float(q3), 3),
            "iqr": round(float(iqr), 3),
            "cv": round(cv, 3),
            "skewness": round(float(stats.skew(s)), 4),
            "kurtosis": round(float(stats.kurtosis(s)), 4),
            "outliers": outliers.tolist(),
            "outlier_count": len(outliers),
            "lower_fence": round(float(lower_fence), 3),
            "upper_fence": round(float(upper_fence), 3),
        }

    def table_rows(self) -> list[dict]:
        """Format statistics as table rows for the UI."""
        stats_dict = self.compute()
        labels = [
            ("Mean", "mean"),
            ("Median", "median"),
            ("Mode", "mode"),
            ("Minimum", "min"),
            ("Maximum", "max"),
            ("Variance", "variance"),
            ("Standard Deviation", "std"),
            ("Q1 (25th percentile)", "q1"),
            ("Q2 (Median)", "q2"),
            ("Q3 (75th percentile)", "q3"),
            ("Interquartile Range", "iqr"),
            ("Coefficient of Variation (%)", "cv"),
            ("Skewness", "skewness"),
            ("Kurtosis", "kurtosis"),
            ("Outlier Count", "outlier_count"),
        ]
        return [{"metric": label, "value": stats_dict[key]} for label, key in labels]

    def explanation(self, lang: str = "en") -> dict:
        """
        Generate human-readable educational interpretation of the distribution.

        Covers central tendency, spread, shape, outliers, and pedagogical insight.
        """
        s = self.compute()
        mean, median, std = s["mean"], s["median"], s["std"]
        skew, kurt = s["skewness"], s["kurtosis"]

        if abs(mean - median) < 1.5:
            tendency = (
                "La distribution est approximativement symétrique autour de la moyenne."
                if lang == "fr"
                else "The distribution is approximately symmetric around the mean."
            )
        elif mean > median:
            tendency = (
                "La moyenne dépasse la médiane, indiquant une asymétrie positive "
                "(quelques scores élevés tirent la moyenne vers le haut)."
                if lang == "fr"
                else "The mean exceeds the median, indicating positive skew "
                "(a few high scores pull the average upward)."
            )
        else:
            tendency = (
                "La médiane dépasse la moyenne, indiquant une asymétrie négative "
                "(quelques scores faibles abaissent la moyenne)."
                if lang == "fr"
                else "The median exceeds the mean, indicating negative skew "
                "(a few low scores pull the average downward)."
            )

        if std < 8:
            spread = (
                "La dispersion est faible : les performances sont homogènes."
                if lang == "fr"
                else "Spread is low: student performances are relatively homogeneous."
            )
        elif std < 15:
            spread = (
                "La dispersion est modérée, reflétant une diversité normale des niveaux."
                if lang == "fr"
                else "Spread is moderate, reflecting normal diversity in achievement levels."
            )
        else:
            spread = (
                "La dispersion est élevée : un écart significatif existe entre les élèves."
                if lang == "fr"
                else "Spread is high: a significant performance gap exists among students."
            )

        if abs(skew) < 0.5:
            shape = "Distribution quasi-normale." if lang == "fr" else "Distribution is near-normal."
        elif skew > 0:
            shape = (
                "Asymétrie positive : plus d'élèves en dessous de la moyenne avec "
                "quelques excellents résultats."
                if lang == "fr"
                else "Positive skew: more students below average with a few excellent results."
            )
        else:
            shape = (
                "Asymétrie négative : concentration vers les scores élevés."
                if lang == "fr"
                else "Negative skew: concentration toward higher scores."
            )

        if s["outlier_count"] == 0:
            outliers_text = (
                "Aucun outlier détecté (méthode IQR × 1.5)."
                if lang == "fr"
                else "No outliers detected (IQR × 1.5 method)."
            )
        else:
            outliers_text = (
                f"{s['outlier_count']} outlier(s) détecté(s) : {s['outliers']}. "
                "Ces cas méritent une attention individualisée."
                if lang == "fr"
                else f"{s['outlier_count']} outlier(s) detected: {s['outliers']}. "
                "These cases warrant individualized attention."
            )

        education = (
            f"Avec une moyenne de {mean} et un écart-type de {std}, "
            "les enseignants peuvent cibler les élèves sous la médiane "
            f"({median}) pour un soutien renforcé, tout en maintenant "
            "les programmes d'excellence pour les profils performants."
            if lang == "fr"
            else f"With a mean of {mean} and standard deviation of {std}, "
            "teachers can target students below the median "
            f"({median}) for reinforced support while maintaining "
            "excellence programs for high performers."
        )

        return {
            "central_tendency": tendency,
            "spread": spread,
            "distribution_shape": shape,
            "outliers": outliers_text,
            "educational_interpretation": education,
            "kurtosis_note": (
                f"Aplatissement (kurtosis = {kurt}): "
                + (
                    "distribution légèrement plus pointue que la normale."
                    if kurt > 0
                    else "distribution plus plate que la normale."
                )
                if lang == "fr"
                else f"Kurtosis = {kurt}: "
                + ("slightly more peaked than normal." if kurt > 0 else "flatter than normal.")
            ),
        }
