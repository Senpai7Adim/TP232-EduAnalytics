"""
Classification service — Question 4.

Trains and compares Decision Tree, Random Forest, KNN, and Logistic Regression
to predict student orientation (Scientific vs Literary).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier


class ClassificationService:
    """Business logic for Question 4: orientation classification."""

    FEATURES = ["Study_Hours", "Attendance", "Homework_Score"]
    TARGET = "Orientation"
    LABELS = ["Literary", "Scientific"]

    def __init__(self, df: pd.DataFrame, test_size: float = 0.2, random_state: int = 42):
        self.df = df.dropna(subset=self.FEATURES + [self.TARGET])
        self.random_state = random_state
        self.X = self.df[self.FEATURES].values
        self.y = self.df[self.TARGET].values

        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            self.X,
            self.y,
            test_size=test_size,
            random_state=random_state,
            stratify=self.y,
        )

        self.models: dict[str, Pipeline] = {
            "Decision Tree": Pipeline(
                [
                    ("scaler", StandardScaler()),
                    (
                        "clf",
                        DecisionTreeClassifier(
                            max_depth=6,
                            min_samples_leaf=5,
                            random_state=random_state,
                        ),
                    ),
                ]
            ),
            "Random Forest": Pipeline(
                [
                    ("scaler", StandardScaler()),
                    (
                        "clf",
                        RandomForestClassifier(
                            n_estimators=200,
                            max_depth=8,
                            random_state=random_state,
                            n_jobs=-1,
                        ),
                    ),
                ]
            ),
            "KNN": Pipeline(
                [
                    ("scaler", StandardScaler()),
                    ("clf", KNeighborsClassifier(n_neighbors=7)),
                ]
            ),
            "Logistic Regression": Pipeline(
                [
                    ("scaler", StandardScaler()),
                    (
                        "clf",
                        LogisticRegression(
                            max_iter=1000,
                            random_state=random_state,
                        ),
                    ),
                ]
            ),
        }

        self.results: dict[str, dict] = {}
        self._train_all()
        self.best_model_name = max(
            self.results,
            key=lambda name: self.results[name]["f1"],
        )

    def _train_all(self) -> None:
        """Fit all models and store evaluation metrics."""
        for name, pipeline in self.models.items():
            pipeline.fit(self.X_train, self.y_train)
            y_pred = pipeline.predict(self.X_test)
            y_proba = (
                pipeline.predict_proba(self.X_test)[:, 1]
                if hasattr(pipeline.named_steps["clf"], "predict_proba")
                else None
            )

            cv_scores = cross_val_score(
                pipeline,
                self.X,
                self.y,
                cv=5,
                scoring="f1_weighted",
                n_jobs=-1,
            )

            cm = confusion_matrix(self.y_test, y_pred, labels=self.LABELS)
            report = classification_report(
                self.y_test, y_pred, output_dict=True, zero_division=0
            )

            roc_data = None
            auc = None
            if y_proba is not None:
                y_binary = (self.y_test == "Scientific").astype(int)
                fpr, tpr, _ = roc_curve(y_binary, y_proba)
                auc = float(roc_auc_score(y_binary, y_proba))
                roc_data = {
                    "fpr": fpr.tolist(),
                    "tpr": tpr.tolist(),
                }

            importances = None
            clf = pipeline.named_steps["clf"]
            if hasattr(clf, "feature_importances_"):
                importances = dict(
                    zip(self.FEATURES, clf.feature_importances_.tolist())
                )
            elif hasattr(clf, "coef_"):
                importances = dict(
                    zip(self.FEATURES, np.abs(clf.coef_[0]).tolist())
                )

            self.results[name] = {
                "accuracy": round(float(accuracy_score(self.y_test, y_pred)), 4),
                "precision": round(float(precision_score(self.y_test, y_pred, average="weighted", zero_division=0)), 4),
                "recall": round(float(recall_score(self.y_test, y_pred, average="weighted", zero_division=0)), 4),
                "f1": round(float(f1_score(self.y_test, y_pred, average="weighted", zero_division=0)), 4),
                "cv_f1_mean": round(float(cv_scores.mean()), 4),
                "cv_f1_std": round(float(cv_scores.std()), 4),
                "confusion_matrix": cm.tolist(),
                "classification_report": report,
                "roc": roc_data,
                "auc": round(auc, 4) if auc else None,
                "feature_importance": importances,
            }

    def comparison_table(self) -> list[dict]:
        """Side-by-side model comparison for the UI."""
        rows = []
        for name, metrics in self.results.items():
            rows.append(
                {
                    "model": name,
                    "accuracy": metrics["accuracy"],
                    "precision": metrics["precision"],
                    "recall": metrics["recall"],
                    "f1": metrics["f1"],
                    "cv_f1": metrics["cv_f1_mean"],
                    "is_best": name == self.best_model_name,
                }
            )
        return sorted(rows, key=lambda r: r["f1"], reverse=True)

    def best_model_results(self) -> dict:
        """Return full results for the automatically selected best model."""
        return {
            "model_name": self.best_model_name,
            **self.results[self.best_model_name],
        }

    def predict_orientation(
        self,
        study_hours: float,
        attendance: float,
        homework_score: float,
    ) -> dict:
        """Predict orientation with probability and explanation."""
        pipeline = self.models[self.best_model_name]
        X_new = np.array([[study_hours, attendance, homework_score]])
        prediction = pipeline.predict(X_new)[0]
        proba = pipeline.predict_proba(X_new)[0]
        classes = pipeline.named_steps["clf"].classes_
        probabilities = {
            cls: round(float(p), 4) for cls, p in zip(classes, proba)
        }

        clf = pipeline.named_steps["clf"]
        explanation_parts = []
        if hasattr(clf, "feature_importances_"):
            imp = dict(zip(self.FEATURES, clf.feature_importances_))
            top_feat = max(imp, key=imp.get)
            explanation_parts.append(
                f"The {self.best_model_name} model weights {top_feat} "
                f"as the most influential feature (importance = {imp[top_feat]:.3f})."
            )

        explanation_parts.append(
            f"Given study hours = {study_hours}, attendance = {attendance}%, "
            f"and homework score = {homework_score}, the model predicts "
            f"**{prediction}** orientation with "
            f"{probabilities[prediction]*100:.1f}% confidence."
        )

        if study_hours >= 20 and homework_score >= 75:
            explanation_parts.append(
                "Strong academic engagement patterns typically align with Scientific orientation."
            )
        elif study_hours < 14:
            explanation_parts.append(
                "Lower study intensity may correlate with Literary orientation in this cohort."
            )

        return {
            "prediction": prediction,
            "probabilities": probabilities,
            "model": self.best_model_name,
            "explanation": " ".join(explanation_parts),
        }

    @property
    def best_accuracy(self) -> float:
        """Accuracy of the best model for dashboard KPI."""
        return self.results[self.best_model_name]["accuracy"]
