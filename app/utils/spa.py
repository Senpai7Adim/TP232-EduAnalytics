"""SPA request detection and response helpers."""

from __future__ import annotations

from flask import jsonify, render_template, request


def is_partial_request() -> bool:
    """Return True when the client expects a partial HTML fragment."""
    return (
        request.headers.get("X-Partial-Request") == "1"
        or request.args.get("partial") == "1"
    )


def is_api_request() -> bool:
    """Return True when the client expects a JSON API response."""
    return (
        request.headers.get("X-Requested-With") == "XMLHttpRequest"
        or request.is_json
        or request.path.startswith("/api/")
        or request.accept_mimetypes.best_match(["application/json", "text/html"]) == "application/json"
    )


def render_page_or_partial(full_template: str, partial_template: str, **context):
    """Render full page or partial based on request type."""
    if is_partial_request():
        return render_template(partial_template, **context)
    return render_template(full_template, **context)


def json_error(message: str, status: int = 400, **extra):
    """Standard JSON error payload."""
    payload = {"success": False, "error": message, **extra}
    return jsonify(payload), status
