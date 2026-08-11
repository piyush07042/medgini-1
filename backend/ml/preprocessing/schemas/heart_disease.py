"""
Heart Disease Dataset Schema

Dataset:
UCI Heart Disease Dataset

Source:
https://archive.ics.uci.edu/dataset/45/heart+disease
"""

SCHEMA = {
    # ------------------------------------------------------------------
    # Basic Information
    # ------------------------------------------------------------------
    "name": "Heart Disease",

    # Raw input CSV has no header row; pipeline-cleaned output is written with headers.
    "header": None,

    # ------------------------------------------------------------------
    # Dataset Columns
    # ------------------------------------------------------------------
    "columns": [
        "age",
        "sex",
        "cp",
        "trestbps",
        "chol",
        "fbs",
        "restecg",
        "thalach",
        "exang",
        "oldpeak",
        "slope",
        "ca",
        "thal",
        "target",
    ],

    # ------------------------------------------------------------------
    # Target Column
    # ------------------------------------------------------------------
    "target_column": "target",

    # ------------------------------------------------------------------
    # Required Columns
    # ------------------------------------------------------------------
    "required_columns": [
        "age",
        "sex",
        "cp",
        "trestbps",
        "chol",
        "fbs",
        "restecg",
        "thalach",
        "exang",
        "oldpeak",
        "slope",
        "ca",
        "thal",
        "target",
    ],

    # ------------------------------------------------------------------
    # Numeric Columns
    # ------------------------------------------------------------------
    "numeric_columns": [
        "age",
        "trestbps",
        "chol",
        "thalach",
        "oldpeak",
        "ca",
    ],

    # ------------------------------------------------------------------
    # Categorical Columns
    # ------------------------------------------------------------------
    "categorical_columns": [
        "sex",
        "cp",
        "fbs",
        "restecg",
        "exang",
        "slope",
        "thal",
    ],

    # ------------------------------------------------------------------
    # Numeric Validation Ranges
    # ------------------------------------------------------------------
    "numeric_ranges": {
        "age": (1, 120),
        "trestbps": (50, 300),
        "chol": (50, 700),
        "thalach": (50, 250),
        "oldpeak": (0.0, 10.0),
        "ca": (0, 4),
    },

    # ------------------------------------------------------------------
    # Allowed Categories
    # ------------------------------------------------------------------
    "allowed_categories": {
        "sex": [0, 1],
        "cp": [1, 2, 3, 4],
        "fbs": [0, 1],
        "restecg": [0, 1, 2],
        "exang": [0, 1],
        "slope": [1, 2, 3],
        "thal": [3, 6, 7],
    },

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------
    "metadata": {
        "dataset": "UCI Heart Disease",
        "source": "UCI Machine Learning Repository",
        "samples": 303,
        "features": 13,
        "target_classes": [0, 1, 2, 3, 4],
        "description": (
            "Heart disease diagnosis dataset used for "
            "classification and risk prediction."
        ),
    },
}