"""REST API blueprint for AJAX interactions."""

from flask import Blueprint, jsonify, request, send_file, session

from app.services.dataset_generator import seed_from_leader_name
from app.utils.helpers import (
    get_classification_service,
    get_clustering_service,
    get_dashboard_service,
    get_data_manager,
    get_descriptive_service,
    get_regression_service,
    require_dataset,
)

api_bp = Blueprint("api", __name__)


@api_bp.route("/health")
def health():
    return jsonify({"status": "ok", "version": "1.0.0"})


@api_bp.route("/kpis")
def kpis():
    dm = get_data_manager()
    if not dm.has_dataset():
        return jsonify({"error": "No dataset"}), 404
    return jsonify(get_dashboard_service().kpis())


@api_bp.route("/predict/exam", methods=["POST"])
def predict_exam():
    dm = get_data_manager()
    if not dm.has_dataset():
        return jsonify({"error": "No dataset"}), 404
    data = request.get_json(silent=True) or {}
    try:
        result = get_regression_service().predict(
            float(data["study_hours"]),
            float(data["attendance"]),
            float(data["homework_score"]),
        )
        return jsonify(result)
    except (KeyError, ValueError, TypeError) as exc:
        return jsonify({"error": str(exc)}), 400


@api_bp.route("/predict/orientation", methods=["POST"])
def predict_orientation():
    dm = get_data_manager()
    if not dm.has_dataset():
        return jsonify({"error": "No dataset"}), 404
    data = request.get_json(silent=True) or {}
    try:
        result = get_classification_service().predict_orientation(
            float(data["study_hours"]),
            float(data["attendance"]),
            float(data["homework_score"]),
        )
        return jsonify(result)
    except (KeyError, ValueError, TypeError) as exc:
        return jsonify({"error": str(exc)}), 400


@api_bp.route("/seed/<leader_name>")
def preview_seed(leader_name: str):
    return jsonify({"seed": seed_from_leader_name(leader_name)})


@api_bp.route("/search")
def search():
    """Search students by ID or orientation."""
    dm = get_data_manager()
    if not dm.has_dataset():
        return jsonify({"results": []})
    q = request.args.get("q", "").strip().lower()
    if not q:
        return jsonify({"results": []})
    df = dm.load()
    mask = (
        df["Student_ID"].str.lower().str.contains(q, na=False)
        | df["Orientation"].str.lower().str.contains(q, na=False)
    )
    results = df[mask].head(20).to_dict(orient="records")
    return jsonify({"results": results})
