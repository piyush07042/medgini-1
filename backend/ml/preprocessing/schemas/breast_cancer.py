"""
Breast Cancer Dataset Schema

Dataset:
Wisconsin Breast Cancer Dataset (simplified schema for the sample model)
"""

SCHEMA = {
    "name": "Breast Cancer",
    "header": 0,
    "columns": [
        "radius_mean",
        "texture_mean",
        "perimeter_mean",
        "area_mean",
        "smoothness_mean",
        "target",
    ],
    "target_column": "target",
    "required_columns": [
        "radius_mean",
        "texture_mean",
        "perimeter_mean",
        "area_mean",
        "smoothness_mean",
        "target",
    ],
    "numeric_columns": [
        "radius_mean",
        "texture_mean",
        "perimeter_mean",
        "area_mean",
        "smoothness_mean",
    ],
    "categorical_columns": [],
    "numeric_ranges": {
        "radius_mean": (0.0, 100.0),
        "texture_mean": (0.0, 100.0),
        "perimeter_mean": (0.0, 300.0),
        "area_mean": (0.0, 2500.0),
        "smoothness_mean": (0.0, 1.0),
    },
    "allowed_categories": {},
    "metadata": {
        "dataset": "Wisconsin Breast Cancer",
        "source": "UCI Machine Learning Repository",
        "description": "Sample breast cancer dataset schema for model validation and preprocessing.",
    },
}
