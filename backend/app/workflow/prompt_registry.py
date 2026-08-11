"""
Prompt Registry
===============
Versioned prompt store for all MediGenie AI agents.

Features
--------
- Store prompts with semantic versioning (v1, v2, ...)
- Promote / rollback any prompt version
- Render prompts with variable substitution
- Register test cases per prompt
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).resolve().parents[3] / "prompts"
PROMPTS_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class PromptVersion:
    """A single versioned snapshot of a prompt template."""
    version: int
    template: str
    variables: list[str]
    description: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    active: bool = False


@dataclass
class PromptEntry:
    """All versions of a named prompt."""
    name: str
    category: str           # e.g. "risk_agent", "knowledge_agent"
    versions: list[PromptVersion] = field(default_factory=list)
    active_version: int = 1

    def get_active(self) -> PromptVersion | None:
        for v in self.versions:
            if v.version == self.active_version:
                return v
        return None

    def render(self, variables: dict[str, Any] | None = None) -> str:
        """Render the active prompt template with variable substitution."""
        active = self.get_active()
        if active is None:
            raise ValueError(f"No active version for prompt '{self.name}'")
        template = active.template
        if variables:
            for key, value in variables.items():
                template = template.replace(f"{{{{{key}}}}}", str(value))
        return template


@dataclass
class PromptTestCase:
    """A single test case for a prompt."""
    name: str
    input_vars: dict[str, Any]
    expected_keywords: list[str]
    min_length: int = 50
    max_length: int = 4000
    description: str = ""


@dataclass
class PromptTestResult:
    """Result of running prompt test cases."""
    prompt_name: str
    version: int
    total: int
    passed: int
    failed: int
    score: float                   # 0.0 – 1.0
    details: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

class PromptRegistry:
    """
    Central prompt registry for all MediGenie agents.

    Stores prompts in memory with optional persistence to JSON files.
    """

    def __init__(self) -> None:
        self._store: dict[str, PromptEntry] = {}
        self._test_cases: dict[str, list[PromptTestCase]] = {}
        self._load_builtin_prompts()

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(
        self,
        name: str,
        category: str,
        template: str,
        variables: list[str] | None = None,
        description: str = "",
    ) -> PromptEntry:
        """Register a new prompt or add version to existing."""
        if name not in self._store:
            version_num = 1
            entry = PromptEntry(name=name, category=category)
        else:
            entry = self._store[name]
            version_num = max(v.version for v in entry.versions) + 1

        # Deactivate old active
        for v in entry.versions:
            v.active = False

        new_version = PromptVersion(
            version=version_num,
            template=template,
            variables=variables or [],
            description=description,
            active=True,
        )
        entry.versions.append(new_version)
        entry.active_version = version_num
        self._store[name] = entry
        logger.info("Registered prompt '%s' v%d", name, version_num)
        return entry

    def promote_version(self, name: str, version: int) -> bool:
        """Promote a specific version to active."""
        if name not in self._store:
            return False
        entry = self._store[name]
        for v in entry.versions:
            v.active = (v.version == version)
        entry.active_version = version
        logger.info("Promoted prompt '%s' to v%d", name, version)
        return True

    def get(self, name: str) -> PromptEntry | None:
        return self._store.get(name)

    def render(self, name: str, variables: dict[str, Any] | None = None) -> str:
        entry = self._store.get(name)
        if entry is None:
            raise ValueError(f"Prompt '{name}' not found in registry")
        return entry.render(variables)

    def list_prompts(self) -> list[dict[str, Any]]:
        result = []
        for name, entry in self._store.items():
            active = entry.get_active()
            result.append({
                "name": name,
                "category": entry.category,
                "active_version": entry.active_version,
                "total_versions": len(entry.versions),
                "variables": active.variables if active else [],
                "description": active.description if active else "",
            })
        return result

    # ------------------------------------------------------------------
    # Test Cases
    # ------------------------------------------------------------------

    def add_test_case(self, prompt_name: str, test_case: PromptTestCase) -> None:
        self._test_cases.setdefault(prompt_name, []).append(test_case)

    def run_tests(self, prompt_name: str) -> PromptTestResult:
        """Execute all registered test cases for a prompt."""
        entry = self._store.get(prompt_name)
        if entry is None:
            return PromptTestResult(
                prompt_name=prompt_name,
                version=0,
                total=0,
                passed=0,
                failed=0,
                score=0.0,
                warnings=[f"Prompt '{prompt_name}' not found"],
            )

        cases = self._test_cases.get(prompt_name, [])
        if not cases:
            return PromptTestResult(
                prompt_name=prompt_name,
                version=entry.active_version,
                total=0,
                passed=0,
                failed=0,
                score=1.0,
                warnings=["No test cases registered for this prompt"],
            )

        passed = 0
        details = []
        for tc in cases:
            try:
                rendered = entry.render(tc.input_vars)
                failures = []
                # Keyword checks
                for kw in tc.expected_keywords:
                    if kw.lower() not in rendered.lower():
                        failures.append(f"Missing keyword: '{kw}'")
                # Length checks
                if len(rendered) < tc.min_length:
                    failures.append(f"Too short: {len(rendered)} < {tc.min_length}")
                if len(rendered) > tc.max_length:
                    failures.append(f"Too long: {len(rendered)} > {tc.max_length}")

                ok = len(failures) == 0
                if ok:
                    passed += 1
                details.append({
                    "test": tc.name,
                    "passed": ok,
                    "failures": failures,
                    "rendered_length": len(rendered),
                })
            except Exception as exc:
                details.append({"test": tc.name, "passed": False, "failures": [str(exc)]})

        total = len(cases)
        score = round(passed / total, 4) if total > 0 else 1.0
        return PromptTestResult(
            prompt_name=prompt_name,
            version=entry.active_version,
            total=total,
            passed=passed,
            failed=total - passed,
            score=score,
            details=details,
        )

    # ------------------------------------------------------------------
    # Built-in Prompts
    # ------------------------------------------------------------------

    def _load_builtin_prompts(self) -> None:
        """Register core agent prompts at startup."""

        self.register(
            name="risk_assessment",
            category="risk_agent",
            template=(
                "You are a clinical risk assessment AI.\n"
                "Patient: {{patient_name}}, Age: {{age}}, Gender: {{gender}}.\n"
                "Symptoms: {{symptoms}}.\n"
                "Assess the risk of {{disease}} and provide a structured clinical summary."
            ),
            variables=["patient_name", "age", "gender", "symptoms", "disease"],
            description="Core risk assessment prompt for all disease agents",
        )

        self.register(
            name="knowledge_query",
            category="knowledge_agent",
            template=(
                "You are a medical knowledge retrieval AI with access to PubMed, WHO guidelines, and clinical databases.\n"
                "Query: {{query}}\n"
                "Patient context: {{context}}\n"
                "Return evidence-based information with source citations. "
                "Do not fabricate medical claims. Flag any uncertainty explicitly."
            ),
            variables=["query", "context"],
            description="Knowledge retrieval prompt with hallucination guardrails",
        )

        self.register(
            name="drug_safety",
            category="drug_agent",
            template=(
                "You are a clinical pharmacist AI.\n"
                "Patient medications: {{medications}}.\n"
                "Patient allergies: {{allergies}}.\n"
                "Analyze for drug-drug interactions, contraindications, and dosage safety.\n"
                "Reference established pharmacological databases."
            ),
            variables=["medications", "allergies"],
            description="Drug safety and interaction analysis prompt",
        )

        self.register(
            name="recommendation",
            category="recommendation_agent",
            template=(
                "You are a clinical decision support AI following evidence-based medicine.\n"
                "Disease risks identified: {{disease_risks}}.\n"
                "Patient profile: {{patient_profile}}.\n"
                "Generate personalized clinical recommendations aligned with AHA, ADA, WHO, and KDIGO guidelines.\n"
                "Include: lifestyle modifications, medication adjustments, follow-up schedule, and preventive care."
            ),
            variables=["disease_risks", "patient_profile"],
            description="Clinical recommendation generation prompt",
        )

        self.register(
            name="report_summary",
            category="report_agent",
            template=(
                "You are a medical report synthesis AI.\n"
                "Compile a structured clinical report from the following agent outputs:\n"
                "Risk Assessment: {{risk_summary}}\n"
                "Drug Safety: {{drug_summary}}\n"
                "Recommendations: {{recommendations}}\n"
                "Knowledge Evidence: {{knowledge_summary}}\n"
                "Produce a clear, physician-readable summary with priority action items."
            ),
            variables=["risk_summary", "drug_summary", "recommendations", "knowledge_summary"],
            description="Final report synthesis prompt",
        )

        # Register test cases for built-in prompts
        self.add_test_case("risk_assessment", PromptTestCase(
            name="basic_render_test",
            input_vars={"patient_name": "John", "age": "45", "gender": "Male",
                        "symptoms": "chest pain, fatigue", "disease": "Heart Disease"},
            expected_keywords=["John", "45", "Heart Disease", "clinical"],
            min_length=100,
        ))

        self.add_test_case("knowledge_query", PromptTestCase(
            name="knowledge_render_test",
            input_vars={"query": "HbA1c targets in Type 2 Diabetes", "context": "patient with CKD"},
            expected_keywords=["Query", "PubMed", "citations", "uncertainty"],
            min_length=100,
        ))

        self.add_test_case("drug_safety", PromptTestCase(
            name="drug_render_test",
            input_vars={"medications": "Metformin, Lisinopril", "allergies": "Penicillin"},
            expected_keywords=["medications", "allergies", "interactions"],
            min_length=80,
        ))

        logger.info("PromptRegistry: loaded %d built-in prompts", len(self._store))


# Singleton
prompt_registry = PromptRegistry()
