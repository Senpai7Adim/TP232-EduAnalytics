"""
Deterministic dataset generation for secondary school performance analysis.

The same group leader name always produces the identical dataset; different
names produce different datasets. The seed is derived via SHA-256 hashing.

Data-generation model (causal chain)
------------------------------------
1. Latent academic engagement is drawn per student (small noise only).
2. Study_Hours is driven by engagement (+ noise).
3. Attendance is positively influenced by Study_Hours (+ noise).
4. Homework_Score is positively influenced by Study_Hours and Attendance (+ noise).
5. Exam_Score is positively influenced by Study_Hours, Attendance, and Homework (+ noise).

Orientation (never random)
--------------------------
Recommended orientation is computed deterministically from outcomes:

    Academic_Index = 0.60 × Exam_Score + 0.25 × Homework_Score + 0.15 × Attendance

Students at or above the cohort median index are labelled **Scientific**;
below the median are labelled **Literary**. This guarantees that high
performers are never misclassified and preserves class balance for ML.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

import numpy as np
import pandas as pd

# Orientation decision weights (must sum to 1.0)
ORIENTATION_WEIGHT_EXAM = 0.60
ORIENTATION_WEIGHT_HOMEWORK = 0.25
ORIENTATION_WEIGHT_ATTENDANCE = 0.15

VALID_ORIENTATIONS = ("Scientific", "Literary")


def seed_from_leader_name(leader_name: str) -> int:
    """
    Derive a deterministic integer seed from the full group leader name.

    Normalises whitespace and case so minor formatting differences do not
    change the generated dataset.
    """
    normalised = re.sub(r"\s+", " ", leader_name.strip().lower())
    digest = hashlib.sha256(normalised.encode("utf-8")).hexdigest()
    return int(digest[:12], 16) % (2**32 - 1)


def slug_from_leader_name(leader_name: str) -> str:
    """Create a filesystem-safe slug for persisting the dataset."""
    normalised = re.sub(r"[^a-zA-Z0-9]+", "_", leader_name.strip().lower()).strip("_")
    return normalised or "default_group"


def compute_academic_index(
    exam_score: float | np.ndarray,
    homework_score: float | np.ndarray,
    attendance: float | np.ndarray,
) -> float | np.ndarray:
    """
    Weighted academic index used for orientation recommendation.

    Weights: Exam 60%, Homework 25%, Attendance 15%.
    """
    return (
        ORIENTATION_WEIGHT_EXAM * exam_score
        + ORIENTATION_WEIGHT_HOMEWORK * homework_score
        + ORIENTATION_WEIGHT_ATTENDANCE * attendance
    )


def compute_orientation(
    exam_score: float,
    homework_score: float,
    attendance: float,
    threshold: float,
) -> str:
    """Assign Scientific/Literary orientation from the weighted academic index."""
    index = compute_academic_index(exam_score, homework_score, attendance)
    return "Scientific" if index >= threshold else "Literary"


def assign_orientations(
    exam_scores: np.ndarray,
    homework_scores: np.ndarray,
    attendances: np.ndarray,
) -> tuple[np.ndarray, float]:
    """
    Vectorised orientation assignment using cohort median as threshold.

    Returns orientation labels and the threshold used.
    """
    indices = compute_academic_index(exam_scores, homework_scores, attendances)
    threshold = float(np.median(indices))
    orientations = np.where(indices >= threshold, "Scientific", "Literary")
    return orientations, threshold


def _validate_dataset(df: pd.DataFrame) -> None:
    """
    Assert structural integrity and expected positive correlations.

    Raises RuntimeError if generated data violates modelling constraints.
    """
    if df["Student_ID"].duplicated().any():
        raise RuntimeError("Duplicate student IDs detected during generation.")

    # Minimum positive correlations required for meaningful analytics
    min_corr = 0.25
    pairs = [
        ("Study_Hours", "Attendance"),
        ("Study_Hours", "Homework_Score"),
        ("Study_Hours", "Exam_Score"),
        ("Attendance", "Homework_Score"),
        ("Attendance", "Exam_Score"),
        ("Homework_Score", "Exam_Score"),
    ]
    for col_a, col_b in pairs:
        corr = df[col_a].corr(df[col_b])
        if corr < min_corr:
            raise RuntimeError(
                f"Expected positive correlation between {col_a} and {col_b}, got {corr:.3f}"
            )

    # High performers (top quartile index) must never be Literary
    indices = compute_academic_index(
        df["Exam_Score"].values,
        df["Homework_Score"].values,
        df["Attendance"].values,
    )
    q3_threshold = float(np.percentile(indices, 75))
    top_mask = indices >= q3_threshold
    literary_in_top = df.loc[top_mask, "Orientation"].eq("Literary").any()
    if literary_in_top:
        raise RuntimeError(
            "Contradictory records: high academic index students classified as Literary."
        )

    # Low performers (bottom quartile) should not be Scientific
    q1_threshold = float(np.percentile(indices, 25))
    bottom_mask = indices <= q1_threshold
    scientific_in_bottom = df.loc[bottom_mask, "Orientation"].eq("Scientific").any()
    if scientific_in_bottom:
        raise RuntimeError(
            "Contradictory records: low academic index students classified as Scientific."
        )


def generate_student_dataset(
    leader_name: str,
    num_students: int,
) -> pd.DataFrame:
    """
    Generate a realistic, correlated student performance dataset.

    Causal relationships preserved with small Gaussian noise:
    Study_Hours → Attendance → Homework_Score → Exam_Score → Orientation
    """
    if not leader_name or not leader_name.strip():
        raise ValueError("Group leader name is required.")
    if num_students < 10:
        raise ValueError("At least 10 students are required.")
    if num_students > 5000:
        raise ValueError("Maximum 5000 students allowed.")

    seed = seed_from_leader_name(leader_name)
    rng = np.random.default_rng(seed)

    # Latent engagement trait (0–1) — only source of between-student heterogeneity
    engagement = np.clip(rng.beta(5, 4, num_students), 0.15, 0.95)

    # Study hours: primary driver, moderated by engagement
    study_hours = (
        8.0
        + 28.0 * engagement
        + rng.normal(0, 2.2, num_students)
    )
    study_hours = np.clip(study_hours, 4.0, 45.0)

    # Attendance: positively driven by study hours and engagement
    attendance = (
        68.0
        + 0.55 * (study_hours - 12.0)
        + 18.0 * engagement
        + rng.normal(0, 1.8, num_students)
    )
    attendance = np.clip(attendance, 65.0, 100.0)

    # Homework: driven by study hours and attendance
    homework_score = (
        38.0
        + 0.85 * (study_hours - 10.0)
        + 0.22 * (attendance - 70.0)
        + 12.0 * engagement
        + rng.normal(0, 3.5, num_students)
    )
    homework_score = np.clip(homework_score, 25.0, 100.0)

    # Exam score: cumulative effect of all behavioural indicators
    exam_raw = (
        28.0
        + 1.05 * (study_hours - 10.0)
        + 0.32 * (attendance - 70.0)
        + 0.30 * homework_score
        + 8.0 * engagement
        + rng.normal(0, 4.5, num_students)
    )
    exam_scores = np.clip(np.round(exam_raw), 20, 100).astype(int)

    # Orientation: deterministic weighted decision (never random)
    orientations, _ = assign_orientations(
        exam_scores.astype(float),
        homework_score,
        attendance,
    )

    df = pd.DataFrame(
        {
            "Student_ID": [
                f"STU-{seed % 10000:04d}-{i + 1:05d}" for i in range(num_students)
            ],
            "Study_Hours": np.round(study_hours, 1),
            "Exam_Score": exam_scores,
            "Attendance": np.round(attendance, 1),
            "Homework_Score": np.round(homework_score, 1),
            "Orientation": orientations,
        }
    )

    _validate_dataset(df)
    return df


def save_dataset(df: pd.DataFrame, path: Path) -> Path:
    """Persist dataset to CSV and return the resolved path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    return path


def generate_and_save(
    leader_name: str,
    num_students: int,
    dataset_dir: Path,
) -> tuple[pd.DataFrame, Path, int]:
    """Generate dataset, save to dataset directory, return df, path, and seed."""
    df = generate_student_dataset(leader_name, num_students)
    slug = slug_from_leader_name(leader_name)
    path = dataset_dir / f"{slug}_{num_students}.csv"
    save_dataset(df, path)
    seed = seed_from_leader_name(leader_name)
    return df, path, seed


def weekly_trend_data(df: pd.DataFrame, leader_name: str, weeks: int = 12) -> pd.DataFrame:
    """
    Build a deterministic weekly performance trend from the dataset seed.

    Simulates gradual academic improvement across the semester while preserving
    the overall statistical profile of the generated cohort.
    """
    seed = seed_from_leader_name(leader_name)
    rng = np.random.default_rng(seed + 7)
    base_mean = df["Exam_Score"].mean()
    trend = []
    for week in range(1, weeks + 1):
        progression = (week - 1) * 0.35
        noise = rng.normal(0, 1.8)
        avg_score = round(base_mean - 4 + progression + noise, 2)
        avg_hours = round(df["Study_Hours"].mean() + rng.normal(0, 0.8), 2)
        trend.append(
            {
                "Week": week,
                "Average_Exam_Score": avg_score,
                "Average_Study_Hours": avg_hours,
            }
        )
    return pd.DataFrame(trend)
