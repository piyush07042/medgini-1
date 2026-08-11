import re
from typing import Any


def _normalize_text(text: str) -> str:
    return re.sub(r"[\r\n]+", "\n", (text or "")).strip()


def _parse_float(raw: str) -> float | None:
    if not raw:
        return None
    raw = raw.strip().replace(",", ".")
    number_match = re.search(r"(-?\d+(?:\.\d+)?)", raw)
    if not number_match:
        return None
    try:
        return float(number_match.group(1))
    except ValueError:
        return None


def _bool_to_gender(value: str) -> str:
    if not value:
        return ""
    normalized = value.strip().upper()
    if normalized in {"M", "MALE"}:
        return "Male"
    if normalized in {"F", "FEMALE"}:
        return "Female"
    return value.capitalize()


def _find_first_match(text: str, patterns: list[str]) -> re.Match | None:
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match
    return None


def _extract_unit(text: str) -> str | None:
    normalized = text.lower()
    if "mmhg" in normalized:
        return "mmHg"
    if "mmol" in normalized:
        return "mmol/L"
    if "mg/dl" in normalized:
        return "mg/dL"
    if "bpm" in normalized or "beats/min" in normalized or "/min" in normalized:
        return "bpm"
    if "%" in normalized:
        return "%"
    return None


def _extract_reference_range(text: str) -> str | None:
    match = re.search(
        r"(?:Ref(?:erence)?(?:\s*Range)?|Range|Normal\s*Range)\s*[:\-]?\s*([0-9.]+(?:\s*[–-]\s*[0-9.]+)?(?:\s*(?:mg/dL|mg/dl|mmol/L|mmHg|bpm|%))?)",
        text,
        re.IGNORECASE,
    )
    if match:
        return match.group(1).strip()
    return None


def _contains_missing_value(text: str) -> bool:
    return bool(re.search(r"\b(?:not\s+available|n/a|na|unknown|invalid|pending|none|not\s+reported)\b", text, re.IGNORECASE))


def _extract_labeled_number(text: str, patterns: list[str]) -> float | None:
    if not text or _contains_missing_value(text):
        return None
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value = _parse_float(match.group(1))
            if value is not None:
                return value
    return None


def _extract_ecg(lines: list[str]) -> str | None:
    for line in lines:
        if re.search(r"\b(?:ECG|EKG|Electrocardiogram)\b", line, re.IGNORECASE):
            match = re.search(
                r"\b(?:ECG|EKG|Electrocardiogram)\b(?:\s*(?:Report|Finding|Result)s?)?\s*[:\-]?\s*(.*)",
                line,
                re.IGNORECASE,
            )
            if match:
                value = match.group(1).strip()
                if value:
                    return value
            cleaned = re.sub(r"\b(?:ECG|EKG|Electrocardiogram)\b", "", line, flags=re.IGNORECASE).strip(" :-")
            if cleaned:
                return cleaned
    return None


def _extract_patient_metrics(text: str) -> dict[str, Any]:
    metrics: dict[str, Any] = {}
    normalized_text = _normalize_text(text)
    if not normalized_text:
        return metrics

    lines = [line.strip() for line in normalized_text.splitlines() if line.strip()]
    collapsed_text = " ".join(lines)

    pid_match = _find_first_match(
        collapsed_text,
        [r"\b(?:Patient\s*ID|PID|Patient\s*Number|MRN|ID)\b\s*[:\-]?\s*([A-Z0-9-]+)\b"],
    )
    if pid_match:
        metrics["patient_id"] = pid_match.group(1).strip()

    age_sex_match = _find_first_match(
        collapsed_text,
        [r"\bAge\s*/\s*Sex\s*[:\-]?\s*(\d{1,3})\s*/\s*(Male|Female|M|F)\b"],
    )
    if age_sex_match:
        metrics["age"] = int(age_sex_match.group(1))
        metrics["sex"] = _bool_to_gender(age_sex_match.group(2))
        metrics["gender"] = metrics["sex"]

    age_match = _find_first_match(
        collapsed_text,
        [
            r"\bAge\b\s*[:\-]?\s*(\d{1,3})\b",
            r"\b(\d{1,3})\s*years?\s*old\b",
        ],
    )
    if age_match and "age" not in metrics:
        metrics["age"] = int(age_match.group(1))

    sex_match = _find_first_match(
        collapsed_text,
        [r"\b(?:Sex|Gender)\b\s*[:\-]?\s*(Male|Female|M|F)\b"],
    )
    if sex_match and "sex" not in metrics:
        metrics["sex"] = _bool_to_gender(sex_match.group(1))
        metrics["gender"] = metrics["sex"]

    for line in lines:
        if re.search(r"\b(?:systolic|sbp)\b", line, re.IGNORECASE):
            systolic = _extract_labeled_number(line, [r"\b(?:systolic|sbp)\b[^\d-]*(\-?\d{2,3})"])
            if systolic is not None:
                metrics["systolic_bp"] = systolic
        elif re.search(r"\b(?:diastolic|dbp)\b", line, re.IGNORECASE):
            diastolic = _extract_labeled_number(line, [r"\b(?:diastolic|dbp)\b[^\d-]*(\-?\d{2,3})"])
            if diastolic is not None:
                metrics["diastolic_bp"] = diastolic
        elif re.search(r"\b(?:bp|blood\s*pressure)\b", line, re.IGNORECASE) and not _contains_missing_value(line):
            bp_match = re.search(r"(\d{2,3})\s*/\s*(\d{2,3})", line)
            if bp_match:
                systolic = _parse_float(bp_match.group(1))
                diastolic = _parse_float(bp_match.group(2))
                if systolic is not None:
                    metrics["systolic_bp"] = systolic
                if diastolic is not None:
                    metrics["diastolic_bp"] = diastolic
                if systolic is not None and diastolic is not None:
                    metrics["blood_pressure"] = f"{int(systolic)}/{int(diastolic)}"
                    metrics["blood_pressure_unit"] = _extract_unit(line) or "mmHg"

    if "systolic_bp" in metrics and "diastolic_bp" in metrics and "blood_pressure" not in metrics:
        metrics["blood_pressure"] = f"{int(metrics['systolic_bp'])}/{int(metrics['diastolic_bp'])}"
        metrics["blood_pressure_unit"] = "mmHg"

    for line in lines:
        glucose = _extract_labeled_number(line, [
            r"\b(?:fbs|fasting\s*blood\s*sugar|blood\s*sugar|random\s*blood\s*sugar|rbs|serum\s*glucose|glucose)\b[^\d-]*(\-?\d+(?:\.\d+)?)",
        ])
        if glucose is not None:
            metrics["glucose"] = glucose
            unit = _extract_unit(line)
            if unit:
                metrics["glucose_unit"] = unit
            else:
                metrics["glucose_unit"] = "mg/dL"
            break

    for line in lines:
        hba1c = _extract_labeled_number(line, [r"\b(?:hba1c|a1c)\b[^\d-]*(\-?\d+(?:\.\d+)?)"])
        if hba1c is not None:
            metrics["hba1c"] = hba1c
            break

    for line in lines:
        bmi = _extract_labeled_number(line, [r"\b(?:bmi|body\s*mass\s*index)\b[^\d-]*(\-?\d+(?:\.\d+)?)"])
        if bmi is not None:
            metrics["bmi"] = bmi
            break

    for line in lines:
        cholesterol = _extract_labeled_number(line, [
            r"\b(?:cholesterol(?:\s+total)?|serum\s*cholesterol|tc)\b[^\d-]*(\-?\d+(?:\.\d+)?)",
        ])
        if cholesterol is not None:
            metrics["cholesterol"] = cholesterol
            break

    for line in lines:
        heart_rate = _extract_labeled_number(line, [
            r"\b(?:heart\s*rate|hr|pulse)\b[^\d-]*(\-?\d{2,3})",
        ])
        if heart_rate is not None:
            metrics["heart_rate"] = heart_rate
            metrics["heart_rate_unit"] = _extract_unit(line) or "bpm"
            break

    for line in lines:
        if re.search(r"\b(?:reference\s*range|ref(?:erence)?|normal\s*range)\b", line, re.IGNORECASE):
            reference = _extract_reference_range(line)
            if reference:
                metrics.setdefault("reference_ranges", {})
                metrics["reference_ranges"].setdefault("glucose", {"text": reference})
                break

    ecg_value = _extract_ecg(lines)
    if ecg_value:
        metrics["ecg"] = ecg_value

    return metrics


def extract_patient_metrics(text: str) -> dict:
    return _extract_patient_metrics(text)


class Parser:
    """
    Backward-compatible wrapper used by MedicalReportAnalysisAgent.
    """

    @staticmethod
    def parse(text: str) -> dict:
        return extract_patient_metrics(text)

    @staticmethod
    def extract(text: str) -> dict:
        return extract_patient_metrics(text)

    @staticmethod
    def extract_patient_metrics(text: str) -> dict:
        return extract_patient_metrics(text)