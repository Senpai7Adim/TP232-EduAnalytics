"""
Regression and correlation service — Question 2.

Analyses relationships between study behaviours and exam performance,
provides prediction simulator with range warnings.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score


class RegressionService:
    """Business logic for Question 2: multivariate regression analysis."""

    FEATURES = ["Study_Hours", "Attendance", "Homework_Score"]
    TARGET = "Exam_Score"

    def __init__(self, df: pd.DataFrame):
        self.df = df.dropna(subset=self.FEATURES + [self.TARGET])
        self.X = self.df[self.FEATURES].values
        self.y = self.df[self.TARGET].values
        self.model = LinearRegression()
        self.model.fit(self.X, self.y)
        self.y_pred = self.model.predict(self.X)
        self.ranges = {
            col: (float(self.df[col].min()), float(self.df[col].max()))
            for col in self.FEATURES
        }

    def pearson_matrix(self) -> dict:
        """Pearson correlation matrix for numeric variables."""
        cols = self.FEATURES + [self.TARGET]
        corr = self.df[cols].corr(method="pearson")
        return {"columns": cols, "values": corr.round(4).values.tolist()}

    def spearman_matrix(self) -> dict:
        """Spearman rank correlation matrix."""
        cols = self.FEATURES + [self.TARGET]
        corr = self.df[cols].corr(method="spearman")
        return {"columns": cols, "values": corr.round(4).values.tolist()}

    def regression_results(self) -> dict:
        """OLS regression coefficients, equation, and goodness-of-fit."""
        coefs = self.model.coef_
        intercept = float(self.model.intercept_)
        r2 = float(r2_score(self.y, self.y_pred))

        terms = [f"{coefs[i]:.4f}·{self.FEATURES[i]}" for i in range(len(self.FEATURES))]
        equation = f"Exam_Score = {intercept:.4f} + " + " + ".join(terms)

        residuals = self.y - self.y_pred

        return {
            "intercept": round(intercept, 4),
            "coefficients": {
                feat: round(float(coefs[i]), 4)
                for i, feat in enumerate(self.FEATURES)
            },
            "equation": equation,
            "r_squared": round(r2, 4),
            "adjusted_r_squared": round(
                1 - (1 - r2) * (len(self.y) - 1) / (len(self.y) - len(self.FEATURES) - 1),
                4,
            ),
            "residuals": residuals.tolist(),
            "fitted": self.y_pred.tolist(),
            "actual": self.y.tolist(),
        }

    def pairwise_correlations(self) -> list[dict]:
        """Pearson and Spearman correlations with exam score."""
        results = []
        for feat in self.FEATURES:
            pearson_r, pearson_p = stats.pearsonr(self.df[feat], self.df[self.TARGET])
            spearman_r, spearman_p = stats.spearmanr(self.df[feat], self.df[self.TARGET])
            results.append(
                {
                    "feature": feat,
                    "pearson_r": round(float(pearson_r), 4),
                    "pearson_p": round(float(pearson_p), 6),
                    "spearman_r": round(float(spearman_r), 4),
                    "spearman_p": round(float(spearman_p), 6),
                }
            )
        return results

    def predict(self, study_hours: float, attendance: float, homework_score: float) -> dict:
        """
        Predict exam score from input features.

        Warns when inputs fall outside the training data range (extrapolation).
        """
        inputs = {
            "Study_Hours": float(study_hours),
            "Attendance": float(attendance),
            "Homework_Score": float(homework_score),
        }
        warnings = []
        for feat, val in inputs.items():
            lo, hi = self.ranges[feat]
            if val < lo or val > hi:
                warnings.append(
                    f"{feat} = {val} is outside training range [{lo:.1f}, {hi:.1f}]. "
                    "Prediction may be unreliable (extrapolation)."
                )

        X_new = np.array([[inputs[f] for f in self.FEATURES]])
        predicted = float(self.model.predict(X_new)[0])
        predicted = round(np.clip(predicted, 0, 100), 2)

        r2 = self.regression_results()["r_squared"]
        if r2 >= 0.7:
            reliability = "High — model explains most score variance."
        elif r2 >= 0.4:
            reliability = "Moderate — useful trend but substantial unexplained variance."
        else:
            reliability = "Low — consider additional factors beyond these three variables."

        if warnings:
            reliability += " Extrapolation warning active."

        return {
            "predicted_score": predicted,
            "reliability": reliability,
            "r_squared": r2,
            "warnings": warnings,
            "inputs": inputs,
        }

    def explanation(self, lang: str = "en") -> str:
        """Narrative explanation of regression findings."""
        reg = self.regression_results()
        pairs = self.pairwise_correlations()
        strongest = max(pairs, key=lambda x: abs(x["pearson_r"]))

        if lang == "fr":
            return (
                f"Le modèle de régression linéaire multiple explique {reg['r_squared']*100:.1f}% "
                f"de la variance des scores d'examen (R² = {reg['r_squared']}). "
                f"La variable la plus corrélée est {strongest['feature']} "
                f"(r = {strongest['pearson_r']}). "
                f"L'équation estimée : {reg['equation']}. "
                "Une hausse des heures d'étude, de l'assiduité et des devoirs "
                "est associée à de meilleurs résultats aux examens."
            )
        return (
            f"The multiple linear regression model explains {reg['r_squared']*100:.1f}% "
            f"of exam score variance (R² = {reg['r_squared']}). "
            f"The strongest correlate is {strongest['feature']} "
            f"(r = {strongest['pearson_r']}). "
            f"Estimated equation: {reg['equation']}. "
            "Increased study hours, attendance, and homework completion "
            "are associated with higher exam performance."
        )
