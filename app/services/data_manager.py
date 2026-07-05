"""
Data loading, session management, and CSV import/export utilities.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pandas as pd
from flask import session

from app.services.dataset_generator import generate_and_save, slug_from_leader_name

NUMERIC_COLUMNS = [
    "Study_Hours",
    "Exam_Score",
    "Attendance",
    "Homework_Score",
]


class DataManager:
    """Central data access layer with session-aware dataset resolution."""

    def __init__(self, dataset_dir: Path, exports_dir: Path):
        self.dataset_dir = Path(dataset_dir)
        self.exports_dir = Path(exports_dir)
        self.dataset_dir.mkdir(parents=True, exist_ok=True)
        self.exports_dir.mkdir(parents=True, exist_ok=True)

    def session_meta(self) -> dict:
        """Return current session dataset metadata."""
        return {
            "leader_name": session.get("leader_name", ""),
            "num_students": session.get("num_students", 0),
            "dataset_path": session.get("dataset_path", ""),
            "seed": session.get("dataset_seed", 0),
        }

    def has_dataset(self) -> bool:
        """Check whether a valid dataset is loaded in the session."""
        path = session.get("dataset_path")
        return bool(path and Path(path).exists())

    def generate(
        self,
        leader_name: str,
        num_students: int,
    ) -> pd.DataFrame:
        """Generate a new dataset and store session metadata."""
        from app.utils.helpers import clear_service_cache
        
        df, path, seed = generate_and_save(
            leader_name,
            int(num_students),
            self.dataset_dir,
        )
        session["leader_name"] = leader_name.strip()
        session["num_students"] = int(num_students)
        session["dataset_path"] = str(path)
        session["dataset_seed"] = seed
        self._load_cached.cache_clear()
        clear_service_cache()
        return df

    def import_csv(self, file_storage) -> pd.DataFrame:
        """Import an external CSV file after schema validation."""
        from app.utils.helpers import clear_service_cache
        
        df = pd.read_csv(file_storage)
        required = {
            "Student_ID",
            "Study_Hours",
            "Exam_Score",
            "Attendance",
            "Homework_Score",
            "Orientation",
        }
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")

        if df["Student_ID"].duplicated().any():
            raise ValueError("Duplicate Student_ID values are not allowed.")

        valid_orientations = {"Scientific", "Literary"}
        invalid = set(df["Orientation"].dropna().unique()) - valid_orientations
        if invalid:
            raise ValueError(f"Invalid Orientation values: {', '.join(invalid)}")

        for col in NUMERIC_COLUMNS:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        if df[NUMERIC_COLUMNS].isna().any().any():
            raise ValueError("Numeric columns contain invalid values.")

        slug = slug_from_leader_name(session.get("leader_name", "imported"))
        path = self.dataset_dir / f"{slug}_imported.csv"
        df.to_csv(path, index=False)

        session["leader_name"] = session.get("leader_name", "Imported Dataset")
        session["num_students"] = len(df)
        session["dataset_path"] = str(path)
        session["dataset_seed"] = 0
        self._load_cached.cache_clear()
        clear_service_cache()
        return df

    def load(self) -> pd.DataFrame:
        """Load the active dataset from session."""
        if not self.has_dataset():
            raise FileNotFoundError(
                "No dataset loaded. Generate or import a dataset first."
            )
        return self._load_cached(session.get("dataset_path"))

    @lru_cache(maxsize=4)
    def _load_cached(self, path: str) -> pd.DataFrame:
        df = pd.read_csv(path)
        for col in NUMERIC_COLUMNS:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        return df

    def export_csv_path(self) -> Path:
        """Copy active dataset to exports directory for download."""
        df = self.load()
        leader = slug_from_leader_name(session.get("leader_name", "dataset"))
        export_path = self.exports_dir / f"{leader}_export.csv"
        df.to_csv(export_path, index=False)
        return export_path

    def preview(self, limit: int = 10) -> list[dict]:
        """Return the first N records for dashboard preview."""
        return self.load().head(limit).to_dict(orient="records")

    def preview_paginated(
        self,
        page: int = 1,
        per_page: int = 15,
        search: str = "",
        sort: str = "Student_ID",
        order: str = "asc",
    ) -> dict:
        """Paginated, searchable, sortable dataset preview."""
        df = self.load()
        allowed_sort = {
            "Student_ID",
            "Study_Hours",
            "Exam_Score",
            "Attendance",
            "Homework_Score",
            "Orientation",
        }
        if sort not in allowed_sort:
            sort = "Student_ID"
        order = "desc" if order.lower() == "desc" else "asc"

        if search:
            mask = (
                df["Student_ID"].str.contains(search, case=False, na=False)
                | df["Orientation"].str.contains(search, case=False, na=False)
            )
            df = df[mask]

        df = df.sort_values(sort, ascending=(order == "asc"))
        total = len(df)
        pages = max(1, (total + per_page - 1) // per_page)
        page = max(1, min(page, pages))
        start = (page - 1) * per_page
        rows = df.iloc[start : start + per_page].to_dict(orient="records")

        return {
            "rows": rows,
            "total": total,
            "page": page,
            "pages": pages,
            "per_page": per_page,
            "sort": sort,
            "order": order,
            "search": search,
        }

    def summary(self) -> dict:
        """High-level dataset summary statistics."""
        df = self.load()
        return {
            "total_students": len(df),
            "avg_exam_score": round(df["Exam_Score"].mean(), 2),
            "avg_study_hours": round(df["Study_Hours"].mean(), 2),
            "highest_score": int(df["Exam_Score"].max()),
            "lowest_score": int(df["Exam_Score"].min()),
            "scientific_count": int((df["Orientation"] == "Scientific").sum()),
            "literary_count": int((df["Orientation"] == "Literary").sum()),
            "columns": df.columns.tolist(),
        }
