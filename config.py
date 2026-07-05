"""Application configuration for INF232 Educational Analytics Platform."""

import os
from pathlib import Path


class Config:
    """Base configuration with design-system tokens and path layout."""

    BASE_DIR = Path(__file__).resolve().parent
    SECRET_KEY = os.environ.get("SECRET_KEY", "inf232-edu-analytics-secret")

    # Directory layout
    DATASET_DIR = BASE_DIR / "dataset"
    EXPORTS_DIR = BASE_DIR / "exports"
    REPORTS_DIR = BASE_DIR / "reports"

    # Application metadata
    APP_NAME = "EduAnalytics"
    APP_SUBTITLE = "Secondary School Performance Analysis"
    COURSE_CODE = "INF232"
    THEME_LABEL = "D"
    VERSION = "1.0.0"

    # Pagination & ML defaults
    ITEMS_PER_PAGE = 25
    TRAIN_TEST_SPLIT = 0.2
    RANDOM_STATE = 42

    # Design system — primary palette
    COLOR_PRIMARY = "#2563EB"
    COLOR_SECONDARY = "#1E40AF"
    COLOR_SUCCESS = "#22C55E"
    COLOR_WARNING = "#F59E0B"
    COLOR_DANGER = "#EF4444"
    COLOR_BACKGROUND = "#F8FAFC"
    COLOR_CARD = "#FFFFFF"
    BORDER_RADIUS = "20px"
    TRANSITION_MS = 300

    CHART_COLORS = [
        "#2563EB",
        "#1E40AF",
        "#22C55E",
        "#F59E0B",
        "#EF4444",
        "#8B5CF6",
        "#06B6D4",
    ]

    # Dataset column schema
    DATASET_COLUMNS = [
        "Student_ID",
        "Study_Hours",
        "Exam_Score",
        "Attendance",
        "Homework_Score",
        "Orientation",
    ]


class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.environ.get("SECRET_KEY")


class TestingConfig(Config):
    DEBUG = True
    TESTING = True


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}


def get_config(config_name: str | None = None) -> type[Config]:
    """Resolve configuration class from environment or explicit name."""
    name = config_name or os.environ.get("FLASK_ENV", "development")
    return config_by_name.get(name, DevelopmentConfig)
