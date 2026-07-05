"""Flask application factory."""

from pathlib import Path

from flask import Flask

from config import Config, get_config


def create_app(config_class: type[Config] | None = None) -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)
    cfg = config_class or get_config()
    app.config.from_object(cfg)

    # Ensure directory layout exists
    for directory in (cfg.DATASET_DIR, cfg.EXPORTS_DIR, cfg.REPORTS_DIR):
        Path(directory).mkdir(parents=True, exist_ok=True)

    from app.services.data_manager import DataManager

    app.extensions["data_manager"] = DataManager(cfg.DATASET_DIR, cfg.EXPORTS_DIR)

    from app.blueprints.dashboard import dashboard_bp
    from app.blueprints.dataset import dataset_bp
    from app.blueprints.question1 import q1_bp
    from app.blueprints.question2 import q2_bp
    from app.blueprints.question3 import q3_bp
    from app.blueprints.question4 import q4_bp
    from app.blueprints.reports import reports_bp
    from app.blueprints.settings import settings_bp
    from app.blueprints.about import about_bp
    from app.blueprints.api import api_bp

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(dataset_bp, url_prefix="/dataset")
    app.register_blueprint(q1_bp, url_prefix="/question-1")
    app.register_blueprint(q2_bp, url_prefix="/question-2")
    app.register_blueprint(q3_bp, url_prefix="/question-3")
    app.register_blueprint(q4_bp, url_prefix="/question-4")
    app.register_blueprint(reports_bp, url_prefix="/reports")
    app.register_blueprint(settings_bp, url_prefix="/settings")
    app.register_blueprint(about_bp, url_prefix="/about")
    app.register_blueprint(api_bp, url_prefix="/api")

    from app.utils.helpers import template_context

    @app.context_processor
    def inject_globals():
        ctx = template_context()
        ctx.update(
            {
                "app_name": app.config["APP_NAME"],
                "app_subtitle": app.config["APP_SUBTITLE"],
                "course_code": app.config["COURSE_CODE"],
                "theme_label": app.config["THEME_LABEL"],
            }
        )
        return ctx

    return app
