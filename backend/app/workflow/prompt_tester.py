"""
Prompt Tester
=============
Automated prompt testing framework for MediGenie agents.

Loads test suites from backend/prompts/tests/*.json and executes
structural, keyword, and length validation checks.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.workflow.prompt_registry import prompt_registry, PromptTestCase, PromptTestResult

logger = logging.getLogger(__name__)

TESTS_DIR = Path(__file__).resolve().parents[3] / "prompts" / "tests"
TESTS_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class PromptSuiteResult:
    """Aggregated result of running all prompt test suites."""
    total_prompts: int
    total_tests: int
    total_passed: int
    total_failed: int
    overall_score: float
    results: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class PromptTester:
    """
    Executes automated test suites against registered prompts.

    Test cases can be loaded from:
    1. Prompts already registered in PromptRegistry (built-in)
    2. JSON files in backend/prompts/tests/*.json

    JSON format:
    {
        "prompt_name": "risk_assessment",
        "tests": [
            {
                "name": "test_name",
                "input_vars": {"key": "value"},
                "expected_keywords": ["word1", "word2"],
                "min_length": 100,
                "max_length": 4000
            }
        ]
    }
    """

    def __init__(self) -> None:
        self._load_json_test_cases()

    def _load_json_test_cases(self) -> None:
        """Load test cases from JSON files in prompts/tests/."""
        loaded = 0
        for test_file in TESTS_DIR.glob("*.json"):
            try:
                data = json.loads(test_file.read_text(encoding="utf-8"))
                prompt_name = data.get("prompt_name", "")
                tests = data.get("tests", [])
                for tc in tests:
                    prompt_registry.add_test_case(
                        prompt_name,
                        PromptTestCase(
                            name=tc.get("name", "unnamed"),
                            input_vars=tc.get("input_vars", {}),
                            expected_keywords=tc.get("expected_keywords", []),
                            min_length=tc.get("min_length", 50),
                            max_length=tc.get("max_length", 4000),
                            description=tc.get("description", ""),
                        ),
                    )
                    loaded += 1
            except Exception as exc:
                logger.warning("Failed to load test file %s: %s", test_file, exc)
        if loaded:
            logger.info("PromptTester: loaded %d external test cases", loaded)

    def run_prompt(self, prompt_name: str) -> PromptTestResult:
        """Run tests for a single named prompt."""
        return prompt_registry.run_tests(prompt_name)

    def run_all(self) -> PromptSuiteResult:
        """Run tests for all registered prompts."""
        all_prompts = prompt_registry.list_prompts()
        results = []
        total_tests = 0
        total_passed = 0
        total_failed = 0
        warnings = []

        for p in all_prompts:
            name = p["name"]
            result = prompt_registry.run_tests(name)
            total_tests += result.total
            total_passed += result.passed
            total_failed += result.failed
            if result.warnings:
                warnings.extend(result.warnings)
            results.append({
                "prompt_name": name,
                "category": p["category"],
                "version": result.version,
                "score": result.score,
                "passed": result.passed,
                "failed": result.failed,
                "details": result.details,
            })

        overall_score = round(total_passed / total_tests, 4) if total_tests > 0 else 1.0

        return PromptSuiteResult(
            total_prompts=len(all_prompts),
            total_tests=total_tests,
            total_passed=total_passed,
            total_failed=total_failed,
            overall_score=overall_score,
            results=results,
            warnings=warnings,
        )


# Singleton
prompt_tester = PromptTester()
