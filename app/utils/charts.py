"""
Reusable Plotly chart builders for the educational analytics platform.

All functions return JSON strings suitable for frontend Plotly rendering.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def fig_to_json(fig: go.Figure) -> str:
    """Serialize a Plotly figure to JSON."""
    return fig.to_json()


def _base_layout(fig: go.Figure, height: int = 380) -> go.Figure:
    """Apply consistent layout styling."""
    fig.update_layout(
        template="plotly_white",
        margin=dict(l=48, r=24, t=48, b=48),
        height=height,
        font=dict(family="Inter, system-ui, sans-serif", size=12),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def histogram(df: pd.DataFrame, column: str, title: str, colors: list[str]) -> str:
    """Interactive histogram with KDE overlay."""
    fig = px.histogram(
        df, x=column, nbins=25,
        color_discrete_sequence=[colors[0]],
        labels={column: column.replace("_", " ")},
    )
    fig.update_traces(marker_line_width=0, opacity=0.85)
    fig.update_layout(title=title, bargap=0.05)
    return fig_to_json(_base_layout(fig))


def pie_chart(df: pd.DataFrame, column: str, title: str, colors: list[str]) -> str:
    """Donut chart for categorical distribution."""
    counts = df[column].value_counts().reset_index()
    counts.columns = [column, "count"]
    fig = px.pie(
        counts, names=column, values="count",
        hole=0.55, color_discrete_sequence=colors,
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    fig.update_layout(title=title, showlegend=False)
    return fig_to_json(_base_layout(fig, 360))


def line_chart(df: pd.DataFrame, x: str, y: str, title: str, colors: list[str]) -> str:
    """Line chart with markers for trend visualisation."""
    fig = px.line(df, x=x, y=y, markers=True, color_discrete_sequence=[colors[0]])
    fig.update_traces(line_width=3, marker_size=8)
    fig.update_layout(title=title)
    return fig_to_json(_base_layout(fig))


def correlation_heatmap(df: pd.DataFrame, columns: list[str], colors: list[str]) -> str:
    """Pearson correlation heatmap."""
    corr = df[columns].corr()
    fig = go.Figure(
        data=go.Heatmap(
            z=corr.values,
            x=corr.columns,
            y=corr.columns,
            colorscale=[[0, "#EF4444"], [0.5, "#F8FAFC"], [1, colors[0]]],
            zmin=-1, zmax=1,
            text=np.round(corr.values, 2),
            texttemplate="%{text}",
        )
    )
    fig.update_layout(title="Correlation Heatmap")
    return fig_to_json(_base_layout(fig, 420))


def box_plot(df: pd.DataFrame, column: str, title: str, colors: list[str]) -> str:
    """Box plot for outlier visualisation."""
    fig = px.box(df, y=column, color_discrete_sequence=[colors[0]])
    fig.update_layout(title=title, showlegend=False)
    return fig_to_json(_base_layout(fig))


def violin_plot(df: pd.DataFrame, column: str, title: str, colors: list[str]) -> str:
    """Violin plot showing distribution density."""
    fig = px.violin(df, y=column, box=True, color_discrete_sequence=[colors[0]])
    fig.update_layout(title=title, showlegend=False)
    return fig_to_json(_base_layout(fig))


def density_curve(df: pd.DataFrame, column: str, title: str, colors: list[str]) -> str:
    """Kernel density estimate curve."""
    fig = px.histogram(
        df, x=column, nbins=30, histnorm="probability density",
        color_discrete_sequence=[colors[0]], opacity=0.5,
    )
    fig.update_layout(title=title, bargap=0.02)
    return fig_to_json(_base_layout(fig))


def scatter_regression(
    df: pd.DataFrame, x: str, y: str, title: str, colors: list[str]
) -> str:
    """Scatter plot with OLS regression line."""
    fig = px.scatter(
        df, x=x, y=y, trendline="ols",
        color_discrete_sequence=[colors[0]], opacity=0.65,
    )
    fig.update_layout(title=title)
    return fig_to_json(_base_layout(fig, 400))


def residual_plot(actual: list, fitted: list, title: str, colors: list[str]) -> str:
    """Residuals vs fitted values plot."""
    residuals = np.array(actual) - np.array(fitted)
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=fitted, y=residuals, mode="markers",
            marker=dict(color=colors[0], opacity=0.6, size=7),
        )
    )
    fig.add_hline(y=0, line_dash="dash", line_color=colors[3])
    fig.update_layout(
        title=title,
        xaxis_title="Fitted Values",
        yaxis_title="Residuals",
    )
    return fig_to_json(_base_layout(fig))


def elbow_chart(k_values: list, inertias: list, optimal_k: int, colors: list[str]) -> str:
    """Elbow method curve with optimal K marker."""
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=k_values, y=inertias, mode="lines+markers",
            line=dict(color=colors[0], width=3),
            marker=dict(size=10),
            name="Inertia",
        )
    )
    fig.add_vline(x=optimal_k, line_dash="dash", line_color=colors[3], annotation_text=f"K={optimal_k}")
    fig.update_layout(title="Elbow Method", xaxis_title="K", yaxis_title="Inertia")
    return fig_to_json(_base_layout(fig))


def silhouette_chart(k_values: list, scores: list, colors: list[str]) -> str:
    """Silhouette score by cluster count."""
    fig = go.Figure(
        go.Bar(x=[str(k) for k in k_values], y=scores, marker_color=colors[0])
    )
    fig.update_layout(title="Silhouette Score by K", xaxis_title="K", yaxis_title="Score")
    return fig_to_json(_base_layout(fig))


def cluster_scatter(
    x: list, y: list, labels: list, title: str, colors: list[str]
) -> str:
    """2D PCA scatter coloured by cluster."""
    fig = px.scatter(
        x=x, y=y, color=[str(c) for c in labels],
        labels={"x": "PC1", "y": "PC2", "color": "Cluster"},
        color_discrete_sequence=colors, opacity=0.75,
    )
    fig.update_layout(title=title)
    return fig_to_json(_base_layout(fig, 420))


def radar_chart(profiles: list[dict], colors: list[str]) -> str:
    """Radar chart comparing cluster centroids (normalised)."""
    categories = ["Study_Hours", "Exam_Score", "Attendance", "Homework_Score"]
    fig = go.Figure()
    for i, profile in enumerate(profiles):
        values = [
            profile["avg_study_hours"],
            profile["avg_exam_score"],
            profile["avg_attendance"],
            profile["avg_homework"],
        ]
        fig.add_trace(
            go.Scatterpolar(
                r=values + [values[0]],
                theta=categories + [categories[0]],
                fill="toself",
                name=f"Cluster {profile['cluster']}: {profile['label']}",
                line_color=colors[i % len(colors)],
                opacity=0.7,
            )
        )
    fig.update_layout(
        title="Cluster Profiles",
        polar=dict(radialaxis=dict(visible=True)),
        showlegend=True,
    )
    return fig_to_json(_base_layout(fig, 440))


def confusion_matrix_chart(matrix: list, labels: list, colors: list[str]) -> str:
    """Heatmap confusion matrix."""
    fig = go.Figure(
        data=go.Heatmap(
            z=matrix, x=labels, y=labels,
            colorscale=[[0, "#F8FAFC"], [1, colors[0]]],
            text=matrix, texttemplate="%{text}",
        )
    )
    fig.update_layout(title="Confusion Matrix", xaxis_title="Predicted", yaxis_title="Actual")
    return fig_to_json(_base_layout(fig, 400))


def roc_curve_chart(fpr: list, tpr: list, auc: float, colors: list[str]) -> str:
    """ROC curve with AUC annotation."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=fpr, y=tpr, mode="lines", line=dict(color=colors[0], width=3), name=f"AUC={auc}"))
    fig.add_trace(go.Scatter(x=[0, 1], y=[0, 1], mode="lines", line=dict(dash="dash", color="#94A3B8")))
    fig.update_layout(title="ROC Curve", xaxis_title="FPR", yaxis_title="TPR")
    return fig_to_json(_base_layout(fig))


def feature_importance_chart(importances: dict[str, float], colors: list[str]) -> str:
    """Horizontal bar chart of feature importances."""
    items = sorted(importances.items(), key=lambda x: x[1], reverse=True)
    fig = go.Figure(
        go.Bar(
            x=[v for _, v in items],
            y=[k for k, _ in items],
            orientation="h",
            marker_color=colors[0],
        )
    )
    fig.update_layout(title="Feature Importance", xaxis_title="Importance")
    return fig_to_json(_base_layout(fig))


def model_comparison_chart(models: list[dict], colors: list[str]) -> str:
    """Grouped bar chart comparing model metrics."""
    names = [m["model"] for m in models]
    fig = go.Figure()
    for metric, color in zip(["accuracy", "precision", "recall", "f1"], colors[:4]):
        fig.add_trace(
            go.Bar(name=metric.title(), x=names, y=[m[metric] for m in models], marker_color=color)
        )
    fig.update_layout(barmode="group", title="Model Comparison")
    return fig_to_json(_base_layout(fig, 400))
