"""
Shared blueprint helpers — dataset access, settings, and guards.
"""

from __future__ import annotations

from functools import wraps

from flask import current_app, flash, jsonify, redirect, request, session, url_for

from app.services.classification_service import ClassificationService
from app.services.clustering_service import ClusteringService
from app.services.dashboard_service import DashboardService
from app.services.data_manager import DataManager
from app.services.descriptive_service import DescriptiveStatisticsService
from app.services.regression_service import RegressionService
from app.utils.i18n import get_language, t, translations_dict
from app.utils.spa import is_api_request, json_error

# Session-scoped service cache to avoid recomputing on every page load
_service_cache: dict = {}


def _cache_key(service_type: str) -> str:
    """Generate a cache key for the current dataset and seed."""
    dataset_path = session.get("dataset_path", "")
    seed = session.get("dataset_seed", 0)
    return f"{service_type}:{dataset_path}:{seed}"


def _get_cached_service(
    service_type: str, factory_func
) -> DashboardService | DescriptiveStatisticsService | RegressionService | ClusteringService | ClassificationService:
    """Get or create a cached service instance."""
    key = _cache_key(service_type)
    if key not in _service_cache:
        _service_cache[key] = factory_func()
    return _service_cache[key]


def get_data_manager() -> DataManager:
    """Return the application DataManager extension."""
    return current_app.extensions["data_manager"]


def clear_service_cache() -> None:
    """Clear all cached services when dataset changes."""
    global _service_cache
    _service_cache.clear()


def chart_colors() -> list[str]:
    """Return configured chart colour palette."""
    return current_app.config["CHART_COLORS"]


def random_state() -> int:
    """Return session seed or application default."""
    return session.get("dataset_seed", current_app.config.get("RANDOM_STATE", 42))


def require_dataset(view_func):
    """Decorator guarding routes that need a loaded dataset."""

    @wraps(view_func)
    def wrapper(*args, **kwargs):
        dm = get_data_manager()
        if not dm.has_dataset():
            if is_api_request() or request.headers.get("X-Partial-Request") == "1":
                return json_error(t("no_dataset"), 404, redirect="/dataset/")
            flash(t("no_dataset"), "warning")
            return redirect(url_for("dataset.index"))
        return view_func(*args, **kwargs)

    return wrapper


def get_dashboard_service() -> DashboardService:
    dm = get_data_manager()
    return _get_cached_service(
        "dashboard",
        lambda: DashboardService(dm.load(), chart_colors(), random_state()),
    )


def get_descriptive_service() -> DescriptiveStatisticsService:
    return _get_cached_service(
        "descriptive",
        lambda: DescriptiveStatisticsService(get_data_manager().load()),
    )


def get_regression_service() -> RegressionService:
    return _get_cached_service(
        "regression",
        lambda: RegressionService(get_data_manager().load()),
    )


def get_clustering_service() -> ClusteringService:
    return _get_cached_service(
        "clustering",
        lambda: ClusteringService(get_data_manager().load(), random_state()),
    )


def get_classification_service() -> ClassificationService:
    return _get_cached_service(
        "classification",
        lambda: ClassificationService(
            get_data_manager().load(), random_state=random_state()
        ),
    )


def user_settings() -> dict:
    """Return current user preferences from session."""
    return {
        "theme": session.get("theme", "light"),
        "language": get_language(),
        "animations": session.get("animations", True),
    }


def template_context() -> dict:
    """Common template variables injected via context processor."""
    dm = get_data_manager()
    return {
        "t": t,
        "translations": translations_dict(),
        "settings": user_settings(),
        "has_dataset": dm.has_dataset(),
        "session_meta": dm.session_meta(),
        "app_version": current_app.config["VERSION"],
        "chart_colors": chart_colors(),
    }
