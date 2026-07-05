"""Question 3 — K-Means clustering blueprint."""

from flask import Blueprint, render_template, request

from app.utils import charts
from app.utils.helpers import chart_colors, get_clustering_service, require_dataset

q3_bp = Blueprint("q3", __name__)


@q3_bp.route("/")
@require_dataset
def index():
    svc = get_clustering_service()
    colors = chart_colors()
    n_clusters = request.args.get("k", type=int)
    result = svc.run(n_clusters)
    elbow = svc.elbow_data()
    silhouette = svc.silhouette_data()

    return render_template(
        "question3/index.html",
        result=result,
        charts={
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
    )
