from __future__ import annotations

from typing import Any
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path

TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "templates"

env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
)


def list_report_templates() -> list[str]:
    """List available clinical report HTML templates."""
    templates = []
    for glob_pattern in ["report_template.html", "report_*_template.html"]:
        templates.extend(
            [path.name for path in TEMPLATES_DIR.glob(glob_pattern) if path.is_file()]
        )
    return sorted(set(templates))


def render_report_html(report: dict[str, Any], template_name: str = "report_template.html") -> str:
    """Render the clinical report as HTML using Jinja2 templates."""
    template = env.get_template(template_name)
    return template.render(report=report)
