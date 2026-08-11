"""
schema_loader.py

Production-ready schema loader for MediGenie.

Loads dataset schemas dynamically and provides a unified interface
to validation, cleaning, feature engineering, training, and inference.

Supported datasets
------------------
- Heart Disease
- Diabetes
- Chronic Kidney Disease
- Liver Disease
- Parkinson's
- Breast Cancer
- Thyroid Disease
- Hepatitis
- Heart Failure
"""

from __future__ import annotations

import importlib
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# ==============================================================================
# Logging
# ==============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)

# ==============================================================================
# Exceptions
# ==============================================================================


class SchemaLoaderError(Exception):
    """Base schema loader exception."""


class SchemaNotFoundError(SchemaLoaderError):
    """Raised when schema module does not exist."""


class InvalidSchemaError(SchemaLoaderError):
    """Raised when schema is invalid."""


# ==============================================================================
# Dataset Schema
# ==============================================================================


@dataclass(slots=True)
class DatasetSchema:
    """
    Standard dataset schema used throughout MediGenie.
    """

    name: str

    header: int | None

    columns: list[str]

    target_column: str

    required_columns: list[str]

    numeric_columns: list[str]

    categorical_columns: list[str]

    numeric_ranges: dict[str, tuple[float | None, float | None]]

    allowed_categories: dict[str, list[Any]]

    metadata: dict[str, Any]


# ==============================================================================
# Schema Loader
# ==============================================================================


class SchemaLoader:
    """
    Loads schemas dynamically from preprocessing.schemas.
    """

    SCHEMA_PACKAGE = (
        "backend.ml.preprocessing.schemas"
    )

    def __init__(self):

        self._cache: dict[
            str,
            DatasetSchema,
        ] = {}

    # -------------------------------------------------------------------------

    @staticmethod
    def normalize_name(
        dataset_name: str,
    ) -> str:
        """
        Normalize dataset names.

        Example

        Heart Disease

        ->

        heart_disease
        """

        return (
            dataset_name
            .strip()
            .lower()
            .replace("-", "_")
            .replace(" ", "_")
        )

    # -------------------------------------------------------------------------

    def is_loaded(
        self,
        dataset_name: str,
    ) -> bool:

        dataset_name = self.normalize_name(
            dataset_name
        )

        return dataset_name in self._cache

    # -------------------------------------------------------------------------

    def get_cached(
        self,
        dataset_name: str,
    ) -> DatasetSchema | None:

        dataset_name = self.normalize_name(
            dataset_name
        )

        return self._cache.get(
            dataset_name
        )

    # -------------------------------------------------------------------------

    def load_module(
        self,
        dataset_name: str,
    ):

        dataset_name = self.normalize_name(
            dataset_name
        )

        module_name = (
            f"{self.SCHEMA_PACKAGE}.{dataset_name}"
        )

        logger.info(
            "Loading schema: %s",
            module_name,
        )

        try:

            module = importlib.import_module(
                module_name
            )

        except ModuleNotFoundError as exc:

            raise SchemaNotFoundError(

                f"Schema '{dataset_name}' not found."

            ) from exc

        return module
        # -------------------------------------------------------------------------
    # Validate Schema Dictionary
    # -------------------------------------------------------------------------

    REQUIRED_KEYS = {
        "name",
        "header",
        "columns",
        "target_column",
        "required_columns",
        "numeric_columns",
        "categorical_columns",
        "numeric_ranges",
        "allowed_categories",
        "metadata",
    }

    def validate_schema_dict(
        self,
        schema: dict[str, Any],
    ) -> None:
        """
        Validate schema dictionary before converting it.
        """

        if not isinstance(schema, dict):

            raise InvalidSchemaError(
                "Schema must be a dictionary."
            )

        missing = self.REQUIRED_KEYS - set(schema.keys())

        if missing:

            raise InvalidSchemaError(
                f"Missing schema keys: {sorted(missing)}"
            )

        if not isinstance(schema["columns"], list):

            raise InvalidSchemaError(
                "'columns' must be a list."
            )

        if schema["target_column"] not in schema["columns"]:

            raise InvalidSchemaError(
                "Target column not present in columns."
            )

        required = set(schema["required_columns"])

        columns = set(schema["columns"])

        if not required.issubset(columns):

            missing_required = required - columns

            raise InvalidSchemaError(

                f"Required columns missing from schema: "

                f"{sorted(missing_required)}"

            )

    # -------------------------------------------------------------------------
    # Convert Dictionary → DatasetSchema
    # -------------------------------------------------------------------------

    def build_schema(
        self,
        schema: dict[str, Any],
    ) -> DatasetSchema:
        """
        Convert schema dictionary into DatasetSchema object.
        """

        self.validate_schema_dict(schema)

        return DatasetSchema(

            name=schema["name"],

            header=schema["header"],

            columns=schema["columns"],

            target_column=schema["target_column"],

            required_columns=schema["required_columns"],

            numeric_columns=schema["numeric_columns"],

            categorical_columns=schema["categorical_columns"],

            numeric_ranges=schema["numeric_ranges"],

            allowed_categories=schema["allowed_categories"],

            metadata=schema["metadata"],

        )

    # -------------------------------------------------------------------------
    # Load Schema
    # -------------------------------------------------------------------------

    def load(
        self,
        dataset_name: str,
    ) -> DatasetSchema:
        """
        Load schema from cache or import dynamically.
        """

        dataset_name = self.normalize_name(
            dataset_name
        )

        cached = self.get_cached(
            dataset_name
        )

        if cached is not None:

            logger.info(
                "Using cached schema: %s",
                dataset_name,
            )

            return cached

        module = self.load_module(
            dataset_name
        )

        if not hasattr(module, "SCHEMA"):

            raise InvalidSchemaError(

                f"{dataset_name} has no SCHEMA object."

            )

        schema = self.build_schema(
            module.SCHEMA
        )

        self._cache[
            dataset_name
        ] = schema

        logger.info(
            "Schema '%s' loaded successfully.",
            dataset_name,
        )

        return schema

    # -------------------------------------------------------------------------
    # Cache Operations
    # -------------------------------------------------------------------------

    def clear_cache(self) -> None:

        self._cache.clear()

        logger.info(
            "Schema cache cleared."
        )

    def cache_size(self) -> int:

        return len(
            self._cache
        )

    def loaded_schemas(self) -> list[str]:

        return sorted(
            self._cache.keys()
        )
    # ==============================================================================
# Global Loader
# ==============================================================================

_loader = SchemaLoader()


# ==============================================================================
# Public API
# ==============================================================================

def load_schema(
    dataset_name: str,
) -> DatasetSchema:
    """
    Public helper to load a dataset schema.

    Parameters
    ----------
    dataset_name : str
        Dataset name.

    Returns
    -------
    DatasetSchema
    """

    return _loader.load(dataset_name)


def reload_schema(
    dataset_name: str,
) -> DatasetSchema:
    """
    Reload a schema from disk.

    Useful during development.
    """

    dataset_name = _loader.normalize_name(
        dataset_name
    )

    if _loader.is_loaded(dataset_name):

        del _loader._cache[
            dataset_name
        ]

    return _loader.load(dataset_name)


# ==============================================================================
# Utilities
# ==============================================================================

def available_schema_files() -> list[str]:
    """
    Return available schema modules.
    """

    schema_directory = (
        Path(__file__).parent
        / "schemas"
    )

    modules = []

    if not schema_directory.exists():

        return modules

    for file in schema_directory.glob("*.py"):

        if file.name.startswith("__"):

            continue

        modules.append(
            file.stem
        )

    return sorted(modules)


def schema_exists(
    dataset_name: str,
) -> bool:
    """
    Check whether a schema exists.
    """

    dataset_name = (
        _loader.normalize_name(
            dataset_name
        )
    )

    return (
        dataset_name
        in available_schema_files()
    )


# ==============================================================================
# Command Line Test
# ==============================================================================

def main():

    print()

    print("=" * 70)
    print("MEDIGENIE SCHEMA LOADER")
    print("=" * 70)

    print()

    print("Available Schemas")

    for schema in available_schema_files():

        print(f" • {schema}")

    print()

    try:

        schema = load_schema(
            "heart_disease"
        )

        print(
            "Heart Disease schema loaded successfully."
        )

        print()

        print(
            f"Dataset : {schema.name}"
        )

        print(
            f"Columns : {len(schema.columns)}"
        )

        print(
            f"Target  : {schema.target_column}"
        )

        print()

        print(
            "Required Columns"
        )

        for column in schema.required_columns:

            print(
                f" - {column}"
            )

    except Exception as exc:

        logger.exception(exc)

    print()

    print("=" * 70)


# ==============================================================================
# Entry Point
# ==============================================================================

if __name__ == "__main__":
    main()