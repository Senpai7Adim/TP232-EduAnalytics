"""
K-Means clustering service — Question 3.

Determines optimal K via elbow method and silhouette score,
profiles clusters with teacher recommendations.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler


class ClusteringService:
    """Business logic for Question 3: unsupervised student segmentation."""

    FEATURES = ["Study_Hours", "Exam_Score", "Attendance", "Homework_Score"]
    K_RANGE = range(2, 9)

    def __init__(self, df: pd.DataFrame, random_state: int = 42):
        self.df = df.dropna(subset=self.FEATURES).copy()
        self.random_state = random_state
        self.scaler = StandardScaler()
        self.scaled = self.scaler.fit_transform(self.df[self.FEATURES])
        self.optimal_k = self._find_optimal_k()

    def _find_optimal_k(self) -> int:
        """
        Select optimal cluster count using silhouette score.

        Elbow (inertia) is computed for visualisation; silhouette guides K selection.
        """
        best_k = 3
        best_score = -1.0
        for k in self.K_RANGE:
            km = KMeans(n_clusters=k, random_state=self.random_state, n_init=10)
            labels = km.fit_predict(self.scaled)
            score = silhouette_score(self.scaled, labels)
            if score > best_score:
                best_score = score
                best_k = k
        return best_k

    def elbow_data(self) -> dict:
        """Inertia values for elbow curve visualisation."""
        inertias = []
        for k in self.K_RANGE:
            km = KMeans(n_clusters=k, random_state=self.random_state, n_init=10)
            km.fit(self.scaled)
            inertias.append(round(float(km.inertia_), 2))
        return {"k": list(self.K_RANGE), "inertia": inertias}

    def silhouette_data(self) -> dict:
        """Silhouette scores across K values."""
        scores = []
        for k in self.K_RANGE:
            km = KMeans(n_clusters=k, random_state=self.random_state, n_init=10)
            labels = km.fit_predict(self.scaled)
            scores.append(round(float(silhouette_score(self.scaled, labels)), 4))
        return {"k": list(self.K_RANGE), "scores": scores}

    def run(self, n_clusters: int | None = None) -> dict:
        """Execute K-Means with optimal or specified K and profile each cluster."""
        k = n_clusters or self.optimal_k
        km = KMeans(n_clusters=k, random_state=self.random_state, n_init=10)
        labels = km.fit_predict(self.scaled)

        pca = PCA(n_components=2, random_state=self.random_state)
        components = pca.fit_transform(self.scaled)

        temp = self.df.copy()
        temp["Cluster"] = labels
        profiles = []
        recommendations = []

        overall_mean_score = temp["Exam_Score"].mean()

        for cluster_id in range(k):
            subset = temp[temp["Cluster"] == cluster_id]
            profile = {
                "cluster": cluster_id,
                "size": len(subset),
                "percentage": round(100 * len(subset) / len(temp), 1),
                "avg_study_hours": round(subset["Study_Hours"].mean(), 2),
                "avg_exam_score": round(subset["Exam_Score"].mean(), 2),
                "avg_attendance": round(subset["Attendance"].mean(), 2),
                "avg_homework": round(subset["Homework_Score"].mean(), 2),
                "scientific_pct": round(
                    100 * (subset["Orientation"] == "Scientific").sum() / len(subset), 1
                ),
            }
            profile["label"], profile["description"] = self._describe_cluster(
                profile, overall_mean_score
            )
            profiles.append(profile)
            recommendations.append(self._recommendation(profile))

        centers_original = self.scaler.inverse_transform(km.cluster_centers_)
        center_list = []
        for i, center in enumerate(centers_original):
            center_list.append(
                {
                    "cluster": i,
                    "Study_Hours": round(float(center[0]), 2),
                    "Exam_Score": round(float(center[1]), 2),
                    "Attendance": round(float(center[2]), 2),
                    "Homework_Score": round(float(center[3]), 2),
                }
            )

        return {
            "n_clusters": k,
            "optimal_k": self.optimal_k,
            "inertia": round(float(km.inertia_), 2),
            "silhouette": round(float(silhouette_score(self.scaled, labels)), 4),
            "profiles": profiles,
            "recommendations": recommendations,
            "pca_variance": [round(float(v), 4) for v in pca.explained_variance_ratio_],
            "pca_x": components[:, 0].tolist(),
            "pca_y": components[:, 1].tolist(),
            "labels": labels.tolist(),
            "centers": center_list,
        }

    @staticmethod
    def _describe_cluster(profile: dict, overall_mean: float) -> tuple[str, str]:
        """Assign human-readable cluster label and description."""
        score = profile["avg_exam_score"]
        attendance = profile["avg_attendance"]
        study = profile["avg_study_hours"]

        if score >= overall_mean + 8 and attendance >= 90:
            return (
                "Excellent Students",
                f"High achievers with strong attendance ({attendance}%) "
                f"and consistent study habits ({study}h/week).",
            )
        if score >= overall_mean:
            return (
                "Average Performers",
                f"Solid mid-range performance with room for targeted improvement.",
            )
        if attendance < 80 or study < 12:
            return (
                "Students Requiring Support",
                f"Lower scores linked to reduced attendance ({attendance}%) "
                f"or insufficient study time ({study}h/week).",
            )
        return (
            "Developing Students",
            f"Moderate engagement; benefit from structured study plans and mentoring.",
        )

    @staticmethod
    def _recommendation(profile: dict) -> str:
        """Generate actionable teacher recommendation per cluster."""
        label = profile.get("label", "")
        if "Excellent" in label:
            return (
                "Offer advanced enrichment projects and peer tutoring roles "
                "to maintain engagement and challenge high performers."
            )
        if "Requiring Support" in label:
            return (
                "Implement attendance monitoring, after-school tutoring, "
                "and parent conferences. Assign study coaches."
            )
        if "Average" in label:
            return (
                "Provide targeted revision workshops and homework support "
                "to push students toward excellence."
            )
        return (
            "Introduce structured study schedules and regular progress check-ins "
            "to build consistent academic habits."
        )
