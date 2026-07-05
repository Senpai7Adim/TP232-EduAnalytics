"""
Internationalisation helpers for English and French UI strings.
"""

from __future__ import annotations

from flask import session

TRANSLATIONS: dict[str, dict[str, str]] = {
    "en": {
        "nav_dashboard": "Dashboard",
        "nav_dataset": "Dataset",
        "nav_q1": "Question 1",
        "nav_q2": "Question 2",
        "nav_q3": "Question 3",
        "nav_q4": "Question 4",
        "nav_reports": "Reports",
        "nav_settings": "Settings",
        "nav_about": "About",
        "search_placeholder": "Search students, metrics, reports…",
        "no_dataset": "No dataset loaded. Please generate or import data first.",
        "generate_dataset": "Generate Dataset",
        "download_csv": "Download CSV",
        "total_students": "Total Students",
        "avg_exam": "Average Exam Score",
        "avg_study": "Average Study Hours",
        "highest": "Highest Score",
        "lowest": "Lowest Score",
        "scientific": "Scientific Students",
        "literary": "Literary Students",
        "accuracy": "Prediction Accuracy",
        "q1_title": "Descriptive Statistics",
        "q2_title": "Relation Between Variables",
        "q3_title": "Unsupervised Learning",
        "q4_title": "Supervised Learning",
        "reports_title": "Professional Report",
        "settings_title": "Settings",
        "about_title": "About the Platform",
        "theme": "Theme",
        "language": "Language",
        "animations": "Animations",
        "light": "Light",
        "dark": "Dark",
        "english": "English",
        "french": "French",
        "enabled": "Enabled",
        "disabled": "Disabled",
        "save_settings": "Save Settings",
        "leader_name": "Group Leader Name",
        "num_students": "Number of Students",
        "export_pdf": "Export PDF",
        "export_charts": "Export Charts",
    },
    "fr": {
        "nav_dashboard": "Tableau de bord",
        "nav_dataset": "Jeu de données",
        "nav_q1": "Question 1",
        "nav_q2": "Question 2",
        "nav_q3": "Question 3",
        "nav_q4": "Question 4",
        "nav_reports": "Rapports",
        "nav_settings": "Paramètres",
        "nav_about": "À propos",
        "search_placeholder": "Rechercher étudiants, métriques, rapports…",
        "no_dataset": "Aucun jeu de données. Veuillez générer ou importer des données.",
        "generate_dataset": "Générer le jeu de données",
        "download_csv": "Télécharger CSV",
        "total_students": "Total étudiants",
        "avg_exam": "Moyenne examen",
        "avg_study": "Moyenne heures d'étude",
        "highest": "Score maximum",
        "lowest": "Score minimum",
        "scientific": "Étudiants scientifiques",
        "literary": "Étudiants littéraires",
        "accuracy": "Précision de prédiction",
        "q1_title": "Statistiques descriptives",
        "q2_title": "Relation entre variables",
        "q3_title": "Apprentissage non supervisé",
        "q4_title": "Apprentissage supervisé",
        "reports_title": "Rapport professionnel",
        "settings_title": "Paramètres",
        "about_title": "À propos de la plateforme",
        "theme": "Thème",
        "language": "Langue",
        "animations": "Animations",
        "light": "Clair",
        "dark": "Sombre",
        "english": "Anglais",
        "french": "Français",
        "enabled": "Activé",
        "disabled": "Désactivé",
        "save_settings": "Enregistrer",
        "leader_name": "Nom du chef de groupe",
        "num_students": "Nombre d'étudiants",
        "export_pdf": "Exporter PDF",
        "export_charts": "Exporter graphiques",
    },
}


def get_language() -> str:
    """Return active UI language code."""
    return session.get("language", "en")


def t(key: str) -> str:
    """Translate a key for the active language."""
    lang = get_language()
    return TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(
        key, TRANSLATIONS["en"].get(key, key)
    )


def translations_dict() -> dict[str, str]:
    """Return full translation map for active language."""
    lang = get_language()
    return TRANSLATIONS.get(lang, TRANSLATIONS["en"])
