"""
Professional report generation service.

Assembles all analytical modules into a structured report and exports
to PDF, CSV, and PNG chart formats.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import zipfile

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.services.classification_service import ClassificationService
from app.services.clustering_service import ClusteringService
from app.services.descriptive_service import DescriptiveStatisticsService
from app.services.regression_service import RegressionService
from app.utils import charts


class ReportService:
    """Compile and export comprehensive analytical reports."""

    def __init__(
        self,
        df: pd.DataFrame,
        leader_name: str,
        random_state: int = 42,
        colors: list[str] | None = None,
    ):
        self.df = df
        self.leader_name = leader_name
        self.random_state = random_state
        self.colors = colors or [
            "#2563EB",
            "#1E40AF",
            "#22C55E",
            "#F59E0B",
            "#EF4444",
        ]

    def compile(self, lang: str = "en") -> dict:
        """Gather all analysis sections into a single report dict."""
        desc = DescriptiveStatisticsService(self.df)
        reg = RegressionService(self.df)
        cluster = ClusteringService(self.df, self.random_state).run()
        clf = ClassificationService(self.df, random_state=self.random_state)

        return {
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "leader_name": self.leader_name,
            "dataset_summary": {
                "total_students": len(self.df),
                "avg_exam": round(self.df["Exam_Score"].mean(), 2),
                "avg_study": round(self.df["Study_Hours"].mean(), 2),
                "scientific": int((self.df["Orientation"] == "Scientific").sum()),
                "literary": int((self.df["Orientation"] == "Literary").sum()),
            },
            "descriptive": desc.compute(),
            "descriptive_explanation": desc.explanation(lang),
            "regression": reg.regression_results(),
            "regression_explanation": reg.explanation(lang),
            "clustering": {
                "n_clusters": cluster["n_clusters"],
                "silhouette": cluster["silhouette"],
                "profiles": cluster["profiles"],
                "recommendations": cluster["recommendations"],
            },
            "classification": {
                "best_model": clf.best_model_name,
                "comparison": clf.comparison_table(),
                "best_results": clf.best_model_results(),
            },
            "conclusions": self._conclusions(lang),
            "recommendations": self._recommendations(lang, cluster),
        }

    def _conclusions(self, lang: str) -> list[str]:
        avg = self.df["Exam_Score"].mean()
        if lang == "fr":
            return [
                f"L'analyse porte sur {len(self.df)} étudiants du groupe de {self.leader_name}.",
                f"Le score moyen aux examens est de {avg:.1f}/100.",
                "Les heures d'étude et l'assiduité sont positivement corrélées aux performances.",
                "La segmentation par clusters révèle des profils distincts nécessitant des interventions différenciées.",
                "Le modèle de classification permet de prédire l'orientation avec une précision acceptable.",
            ]
        return [
            f"Analysis covers {len(self.df)} students in {self.leader_name}'s group.",
            f"Average exam score is {avg:.1f}/100.",
            "Study hours and attendance are positively correlated with performance.",
            "Cluster segmentation reveals distinct student profiles requiring differentiated interventions.",
            "The classification model predicts orientation with acceptable accuracy.",
        ]

    def _recommendations(self, lang: str, cluster: dict) -> list[str]:
        recs = cluster.get("recommendations", [])
        if lang == "fr":
            general = [
                "Mettre en place un suivi hebdomadaire de l'assiduité.",
                "Proposer des ateliers de méthodologie pour les élèves à faibles heures d'étude.",
                "Utiliser les clusters pour organiser des groupes de travail homogènes.",
            ]
        else:
            general = [
                "Implement weekly attendance monitoring dashboards.",
                "Offer study methodology workshops for low study-hour students.",
                "Use cluster assignments to organise homogeneous study groups.",
            ]
        return general + list(recs)

    def export_pdf(self, output_path: Path, lang: str = "en") -> Path:
        """Generate a professional PDF report."""
        report = self.compile(lang)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            rightMargin=2 * cm,
            leftMargin=2 * cm,
            topMargin=2 * cm,
            bottomMargin=2 * cm,
        )
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "Title",
            parent=styles["Heading1"],
            fontSize=18,
            spaceAfter=12,
            textColor=colors.HexColor("#2563EB"),
        )
        heading_style = ParagraphStyle(
            "Section",
            parent=styles["Heading2"],
            fontSize=14,
            spaceBefore=16,
            spaceAfter=8,
            textColor=colors.HexColor("#1E40AF"),
        )
        body_style = styles["BodyText"]

        story = []
        story.append(Paragraph("INF232 — Educational Analytics Report", title_style))
        story.append(Paragraph(f"Group Leader: {report['leader_name']}", body_style))
        story.append(Paragraph(f"Generated: {report['generated_at']}", body_style))
        story.append(Spacer(1, 0.5 * cm))

        # Dataset summary
        story.append(Paragraph("1. Dataset Summary", heading_style))
        ds = report["dataset_summary"]
        summary_data = [
            ["Metric", "Value"],
            ["Total Students", str(ds["total_students"])],
            ["Average Exam Score", str(ds["avg_exam"])],
            ["Average Study Hours", str(ds["avg_study"])],
            ["Scientific", str(ds["scientific"])],
            ["Literary", str(ds["literary"])],
        ]
        t = Table(summary_data, colWidths=[8 * cm, 6 * cm])
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563EB")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
                ]
            )
        )
        story.append(t)
        story.append(Spacer(1, 0.3 * cm))

        # Descriptive stats
        story.append(Paragraph("2. Descriptive Statistics", heading_style))
        desc = report["descriptive"]
        desc_rows = [["Statistic", "Value"]]
        for key in ["mean", "median", "std", "min", "max", "skewness", "kurtosis"]:
            desc_rows.append([key.title(), str(desc[key])])
        t2 = Table(desc_rows, colWidths=[8 * cm, 6 * cm])
        t2.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.grey)]))
        story.append(t2)

        exp = report["descriptive_explanation"]
        story.append(Paragraph(exp["educational_interpretation"], body_style))
        story.append(Spacer(1, 0.3 * cm))

        # Regression
        story.append(Paragraph("3. Regression Analysis", heading_style))
        reg = report["regression"]
        story.append(Paragraph(reg["equation"], body_style))
        story.append(Paragraph(f"R² = {reg['r_squared']}", body_style))
        story.append(Paragraph(report["regression_explanation"], body_style))
        story.append(Spacer(1, 0.3 * cm))

        # Clustering
        story.append(Paragraph("4. Clustering Analysis", heading_style))
        for profile in report["clustering"]["profiles"]:
            story.append(
                Paragraph(
                    f"Cluster {profile['cluster']}: {profile['label']} "
                    f"(n={profile['size']}, avg score={profile['avg_exam_score']})",
                    body_style,
                )
            )
        story.append(Spacer(1, 0.3 * cm))

        # Classification
        story.append(Paragraph("5. Classification Results", heading_style))
        clf = report["classification"]
        story.append(Paragraph(f"Best Model: {clf['best_model']}", body_style))
        comp_data = [["Model", "Accuracy", "F1"]]
        for row in clf["comparison"]:
            comp_data.append([row["model"], str(row["accuracy"]), str(row["f1"])])
        t3 = Table(comp_data, colWidths=[6 * cm, 4 * cm, 4 * cm])
        t3.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.grey)]))
        story.append(t3)
        story.append(Spacer(1, 0.3 * cm))

        # Conclusions
        story.append(Paragraph("6. Conclusions & Recommendations", heading_style))
        for item in report["conclusions"] + report["recommendations"]:
            story.append(Paragraph(f"• {item}", body_style))

        doc.build(story)
        return output_path

    def export_charts_zip(self, output_path: Path) -> Path:
        """
        Export key analytical charts as PNG files bundled in a ZIP archive.

        Uses Plotly/Kaleido for high-quality static chart images suitable for
        reports and presentations.
        """
        import plotly.io as pio
        import time

        output_path.parent.mkdir(parents=True, exist_ok=True)
        reg = RegressionService(self.df)
        reg_results = reg.regression_results()
        cluster = ClusteringService(self.df, self.random_state).run()
        clf = ClassificationService(self.df, random_state=self.random_state)
        best = clf.best_model_results()

        chart_builders: list[tuple[str, str]] = [
            (
                "01_exam_score_histogram.png",
                charts.histogram(
                    self.df, "Exam_Score", "Exam Score Distribution", self.colors
                ),
            ),
            (
                "02_correlation_heatmap.png",
                charts.correlation_heatmap(
                    self.df,
                    ["Study_Hours", "Exam_Score", "Attendance", "Homework_Score"],
                    self.colors,
                ),
            ),
            (
                "03_regression_residuals.png",
                charts.residual_plot(
                    reg_results["actual"],
                    reg_results["fitted"],
                    "Residual Plot",
                    self.colors,
                ),
            ),
            (
                "04_cluster_visualization.png",
                charts.cluster_scatter(
                    cluster["pca_x"],
                    cluster["pca_y"],
                    cluster["labels"],
                    "Cluster Visualization",
                    self.colors,
                ),
            ),
            (
                "05_cluster_radar.png",
                charts.radar_chart(cluster["profiles"], self.colors),
            ),
            (
                "06_confusion_matrix.png",
                charts.confusion_matrix_chart(
                    best["confusion_matrix"],
                    ["Literary", "Scientific"],
                    self.colors,
                ),
            ),
        ]

        if best.get("roc") and best.get("auc"):
            chart_builders.append(
                (
                    "07_roc_curve.png",
                    charts.roc_curve_chart(
                        best["roc"]["fpr"],
                        best["roc"]["tpr"],
                        best["auc"],
                        self.colors,
                    ),
                )
            )

        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as archive:
            for filename, fig_json in chart_builders:
                fig = pio.from_json(fig_json)
                
                # Retry logic for Kaleido browser issues
                png_bytes = None
                for attempt in range(3):
                    try:
                        # Use a longer timeout and pass engine_kwargs for more reliable behavior
                        png_bytes = pio.to_image(
                            fig, 
                            format="png", 
                            width=1200, 
                            height=700, 
                            scale=2,
                            engine="kaleido"
                        )
                        break  # Success
                    except Exception as e:
                        if attempt < 2:  # Not the last attempt
                            print(f"Chart export attempt {attempt + 1} failed for {filename}, retrying...")
                            time.sleep(1)  # Wait before retry
                        else:
                            # Last attempt failed, raise error
                            raise RuntimeError(
                                f"Failed to export chart {filename} after 3 attempts. "
                                f"This is a Kaleido/Chrome issue. Try:\n"
                                f"1. Run: pip install --upgrade kaleido\n"
                                f"2. Restart your application\n"
                                f"3. Or run: python -m pip install choreographer && choreo_get_chrome\n"
                                f"Original error: {str(e)}"
                            ) from e
                
                if png_bytes:
                    archive.writestr(filename, png_bytes)

        return output_path
