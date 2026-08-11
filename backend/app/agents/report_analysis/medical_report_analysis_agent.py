from __future__ import annotations

import time

from app.agents.base.base_agent import BaseAgent
from app.agents.base.agent_result import AgentResult
from app.agents.base.agent_state import AgentState

from app.services.ocr.ocr_service import OCRService
from app.services.ocr.parser import Parser


class MedicalReportAnalysisAgent(BaseAgent):
    """
    Medical Report Analysis Agent

    Responsibilities
    ----------------
    1. Extract text from uploaded reports.
    2. Parse clinical values.
    3. Store results into AgentState.
    """

    agent_name = "MedicalReportAnalysisAgent"

    async def run(self, state: AgentState) -> AgentResult:

        start = time.perf_counter()

        # Accept either uploaded report files or raw report text for tests
        if not state.uploaded_reports and not state.raw_report_text:
            return AgentResult(
                agent=self.agent_name,
                status="FAILED",
                confidence=0.0,
                result={},
                warnings=["No medical reports uploaded or raw report text provided."],
            )

        extracted_reports = []
        parsed_metrics = {}
        warnings: list[str] = []

        ocr = OCRService()
        parser = Parser()

        reports = list(state.uploaded_reports) or [None]
        for report in reports:
            if report is None:
                text = state.raw_report_text or ""
                source_name = "raw_report_text"
            else:
                try:
                    text = ocr.extract_text(report)
                except TypeError:
                    text = ""
                source_name = report

            metrics = parser.parse(text)
            if not text.strip():
                warnings.append("OCR returned no extractable text for the provided report.")
            elif not metrics:
                warnings.append("OCR text was extracted but no structured metrics could be parsed.")
            elif not any(key in metrics for key in {"patient_id", "age", "sex", "gender", "glucose", "bmi", "cholesterol", "systolic_bp", "diastolic_bp", "heart_rate", "ecg"}):
                warnings.append("OCR text was extracted but no structured metrics could be parsed.")

            extracted_reports.append({"report": report, "text": text, "metrics": metrics})
            if metrics:
                for key, value in metrics.items():
                    parsed_metrics.setdefault(key, value)
                state.report_text = text
            else:
                state.report_text = "\n\n".join(item["text"] for item in extracted_reports if item["text"])

        state.ocr_result = extracted_reports
        state.extracted_metrics = parsed_metrics

        if parsed_metrics:
            patient_payload = {
                k: v
                for k, v in parsed_metrics.items()
                if k in {"patient_id", "age", "sex", "gender", "bmi", "glucose", "cholesterol", "systolic_bp", "diastolic_bp", "blood_pressure", "heart_rate", "ecg"}
            }
            for key, value in patient_payload.items():
                state.patient.setdefault(key, value)

        elapsed = round(time.perf_counter() - start, 3)

        state.set_agent_output(
            self.agent_name,
            parsed_metrics,
            confidence=0.95,
            execution_time=elapsed,
        )

        print("DEBUG_WARNINGS", warnings, parsed_metrics, text)

        return AgentResult(
            agent=self.agent_name,
            status="SUCCESS",
            confidence=0.95,
            result=parsed_metrics,
            warnings=warnings,
            metadata={
                "reports_processed": len(extracted_reports),
                "execution_time": elapsed,
            },
        )