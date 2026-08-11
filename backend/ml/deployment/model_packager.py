"""
model_packager.py

Production deployment package creator.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import shutil

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


class PackagingError(Exception):
    """Base deployment packaging exception."""


class ArtifactNotFoundError(PackagingError):
    """Required artifact missing."""


@dataclass(slots=True)
class PackageConfig:
    model_path: Path
    schema_path: Path
    metadata_path: Path
    output_directory: Path
    scaler_path: Path | None = None
    encoder_path: Path | None = None
    preprocessor_path: Path | None = None
    feature_names_path: Path | None = None
    version: str = "1.0.0"
    requirements_path: Path | None = None


class ModelPackager:
    """Production deployment package creator."""

    def __init__(self, config: PackageConfig) -> None:

        self.config = config
        self.package_directory = self.config.output_directory

    def initialize(self) -> None:

        logger.info("Preparing deployment package...")
        self.package_directory.mkdir(parents=True, exist_ok=True)

    def copy_file(self, source: Path, destination_name: str) -> None:

        if not source.exists():
            raise ArtifactNotFoundError(f"Missing artifact: {source}")

        destination = self.package_directory / destination_name
        # If source and destination are the same file, skip copying.
        try:
            if source.resolve() == destination.resolve():
                logger.info("Skipping copy (same file): %s", destination_name)
                return
        except Exception:
            # If resolve fails for any reason, fall back to copying.
            pass

        shutil.copy2(source, destination)
        logger.info("Copied %s", destination_name)

    def copy_artifacts(self) -> None:

        self.copy_file(self.config.model_path, "model.joblib")

        if self.config.preprocessor_path:
            self.copy_file(self.config.preprocessor_path, "preprocessor.joblib")

        if self.config.feature_names_path:
            self.copy_file(self.config.feature_names_path, "feature_names.json")

        if self.config.scaler_path:
            self.copy_file(self.config.scaler_path, "scaler.joblib")

        if self.config.encoder_path:
            self.copy_file(self.config.encoder_path, "encoder.joblib")

        self.copy_file(self.config.schema_path, "schema.json")
        self.copy_file(self.config.metadata_path, "metadata.json")

        requirements_path = self.config.requirements_path or Path("backend/requirements.txt")

        if requirements_path.exists():
            self.copy_file(requirements_path, "requirements.txt")

    def sha256(self, file_path: Path) -> str:

        sha = hashlib.sha256()

        with open(file_path, "rb") as file:
            for chunk in iter(lambda: file.read(8192), b""):
                sha.update(chunk)

        return sha.hexdigest()

    def create_manifest(self) -> None:

        manifest = {
            "version": self.config.version,
            "created": datetime.utcnow().isoformat(),
            "artifacts": {},
        }

        for file in self.package_directory.iterdir():
            if file.is_file():
                manifest["artifacts"][file.name] = {
                    "size": file.stat().st_size,
                    "sha256": self.sha256(file),
                }

        manifest_path = self.package_directory / "manifest.json"

        with open(manifest_path, "w", encoding="utf-8") as fp:
            json.dump(manifest, fp, indent=4)

        logger.info("Manifest created: %s", manifest_path)

    def validate(self) -> None:

        required = [
            "model.joblib",
            "schema.json",
            "metadata.json",
            "requirements.txt",
            "manifest.json",
        ]

        if self.config.preprocessor_path is not None:
            required.append("preprocessor.joblib")

        if self.config.feature_names_path is not None:
            required.append("feature_names.json")

        for name in required:
            path = self.package_directory / name
            if not path.exists():
                raise PackagingError(f"{name} missing.")

        logger.info("Deployment package validated.")

    def run(self) -> None:

        logger.info("=" * 70)
        logger.info("Packaging deployment model...")

        self.initialize()
        self.copy_artifacts()
        self.create_manifest()
        self.validate()

        logger.info("=" * 70)
        logger.info("Deployment package ready.")


def build_parser() -> argparse.ArgumentParser:

    parser = argparse.ArgumentParser(description="MediGenie deployment packager")
    parser.add_argument("--model", required=True)
    parser.add_argument("--schema", required=True)
    parser.add_argument("--metadata", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--scaler")
    parser.add_argument("--encoder")
    parser.add_argument("--version", default="1.0.0")
    return parser


def main() -> None:

    args = build_parser().parse_args()

    config = PackageConfig(
        model_path=Path(args.model),
        scaler_path=Path(args.scaler) if args.scaler else None,
        encoder_path=Path(args.encoder) if args.encoder else None,
        schema_path=Path(args.schema),
        metadata_path=Path(args.metadata),
        output_directory=Path(args.output),
        version=args.version,
    )

    ModelPackager(config).run()


if __name__ == "__main__":
    main()