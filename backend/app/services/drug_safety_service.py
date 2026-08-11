from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Set


KNOWN_INTERACTIONS = [
    {
        "pair": {"aspirin", "warfarin"},
        "severity": "Major",
        "explanation": "Concomitant use significantly increases the risk of major bleeding.",
        "recommendation": "Avoid co-prescribing aspirin with warfarin and choose an alternative analgesic or anticoagulant based on clinical context.",
    },
    {
        "pair": {"metformin", "contrast_media"},
        "severity": "Major",
        "explanation": "Iodinated contrast media may precipitate acute renal failure and metformin-associated lactic acidosis.",
        "recommendation": "Hold metformin before and after contrast exposure until renal function is confirmed stable.",
    },
    {
        "pair": {"lisinopril", "spironolactone"},
        "severity": "Moderate",
        "explanation": "This combination increases the risk of hyperkalemia and renal dysfunction.",
        "recommendation": "Monitor potassium and renal function closely or choose an alternative antihypertensive regimen.",
    },
    {
        "pair": {"ciprofloxacin", "theophylline"},
        "severity": "Moderate",
        "explanation": "Ciprofloxacin can raise theophylline concentrations, increasing toxicity risk.",
        "recommendation": "Avoid the combination or reduce theophylline dose with frequent monitoring.",
    },
    {
        "pair": {"ibuprofen", "lisinopril"},
        "severity": "Moderate",
        "explanation": "NSAIDs can blunt the antihypertensive effect of ACE inhibitors and impair renal perfusion.",
        "recommendation": "Use acetaminophen for pain control or monitor blood pressure and renal function closely.",
    },
    {
        "pair": {"aspirin", "ibuprofen"},
        "severity": "Moderate",
        "explanation": "Concomitant use of aspirin and ibuprofen increases gastrointestinal bleeding risk and ibuprofen may attenuate aspirin's cardioprotective effect.",
        "recommendation": "Space ibuprofen administration (take ibuprofen at least 30-120 minutes after or 8 hours before immediate-release aspirin) or use acetaminophen for pain.",
    },
]

DRUG_ALLERGY_MAP = {
    "penicillin": ["amoxicillin", "ampicillin", "piperacillin", "penicillin", "amoxicillin/clavulanate"],
    "sulfa": ["sulfamethoxazole", "trimethoprim-sulfamethoxazole", "sulfasalazine", "sulfadiazine"],
    "nsaid": ["ibuprofen", "naproxen", "aspirin", "ketorolac", "diclofenac"],
}

DRUG_PREGNANCY_SAFETY = {
    "acetaminophen": ("Safe", "Recommended as the preferred analgesic in pregnancy when clinically indicated."),
    "ibuprofen": ("Use with caution", "Avoid in the third trimester and use only after consultation with a clinician."),
    "warfarin": ("Contraindicated", "Associated with fetal bleeding and teratogenicity; use alternative anticoagulation."),
    "lisinopril": ("Contraindicated", "ACE inhibitors are contraindicated in pregnancy due to fetal renal and cardiac toxicity."),
    "metformin": ("Use with caution", "Continue only under obstetric supervision for gestational diabetes management."),
    "ciprofloxacin": ("Contraindicated", "Fluoroquinolones are generally avoided during pregnancy due to potential musculoskeletal effects."),
    "prednisone": ("Use with caution", "Use the lowest effective dose and limit duration when possible."),
    "aspirin": ("Use with caution", "Low-dose aspirin may be appropriate in selected pregnancies; avoid higher doses without supervision."),
}

CONTRAINDICATION_RULES = {
    "heart_disease": [
        {
            "drugs": ["ibuprofen", "naproxen", "ketorolac"],
            "severity": "Major",
            "explanation": "NSAIDs may worsen heart failure symptoms and promote fluid retention.",
            "recommendation": "Prefer acetaminophen or other non-NSAID therapies for pain management in patients with heart disease.",
        },
        {
            "drugs": ["pseudoephedrine"],
            "severity": "Moderate",
            "explanation": "Sympathomimetic decongestants can raise blood pressure and heart rate.",
            "recommendation": "Avoid pseudoephedrine in patients with heart disease, especially if uncontrolled hypertension is present.",
        },
    ],
    "hypertension": [
        {
            "drugs": ["ibuprofen", "naproxen", "ketorolac"],
            "severity": "Moderate",
            "explanation": "NSAIDs may elevate blood pressure and reduce the effectiveness of antihypertensive therapy.",
            "recommendation": "Use acetaminophen or non-pharmacologic therapy for mild pain in hypertension.",
        },
        {
            "drugs": ["pseudoephedrine"],
            "severity": "Major",
            "explanation": "Decongestants can cause severe hypertension and tachycardia.",
            "recommendation": "Avoid pseudoephedrine when possible and choose safer nasal decongestants.",
        },
    ],
    "diabetes": [
        {
            "drugs": ["prednisone", "dexamethasone"],
            "severity": "Moderate",
            "explanation": "Systemic corticosteroids may significantly raise blood glucose levels.",
            "recommendation": "Use the lowest effective corticosteroid dose or consider steroid-sparing alternatives.",
        },
        {
            "drugs": ["propranolol"],
            "severity": "Moderate",
            "explanation": "Non-selective beta-blockers can mask hypoglycemia symptoms.",
            "recommendation": "Prefer cardioselective beta-blockers when beta-blockade is required.",
        },
    ],
    "kidney disease": [
        {
            "drugs": ["metformin", "lisinopril", "ibuprofen", "nitrofurantoin"],
            "severity": "Major",
            "explanation": "These medications can accumulate or worsen renal function in kidney disease.",
            "recommendation": "Review dosing carefully and consider renal-safe alternatives for patients with chronic kidney disease.",
        },
    ],
    "liver disease": [
        {
            "drugs": ["acetaminophen", "statins", "warfarin", "amiodarone"],
            "severity": "Major",
            "explanation": "Hepatically metabolized drugs may require dose adjustment or avoidance in liver impairment.",
            "recommendation": "Monitor liver tests closely and select lower-risk medications whenever possible.",
        },
    ],
    "asthma": [
        {
            "drugs": ["propranolol", "nadolol"],
            "severity": "Major",
            "explanation": "Non-selective beta-blockers can trigger bronchospasm and worsen asthma control.",
            "recommendation": "Prefer cardioselective beta-blockers or other antihypertensives in patients with asthma.",
        },
    ],
    "pregnancy": [
        {
            "drugs": ["warfarin", "lisinopril", "ciprofloxacin"],
            "severity": "Major",
            "explanation": "These medications are known to be harmful in pregnancy and should be avoided when possible.",
            "recommendation": "Replace with pregnancy-safe alternatives and consult obstetrics if continuing therapy is required.",
        },
    ],
    "elderly": [
        {
            "drugs": ["diazepam", "lorazepam"],
            "severity": "Major",
            "explanation": "Long-acting benzodiazepines increase fall risk and cognitive impairment in older adults.",
            "recommendation": "Use shorter-acting agents or non-pharmacologic therapies for anxiety and insomnia.",
        },
        {
            "drugs": ["ibuprofen", "naproxen"],
            "severity": "Moderate",
            "explanation": "NSAIDs increase the risk of renal injury and gastrointestinal bleeding in elderly patients.",
            "recommendation": "Use acetaminophen or topical analgesics when appropriate.",
        },
    ],
}

RENAL_SENSITIVE_DRUGS = {
    "metformin": "Reduce dose or hold in moderate-to-severe renal impairment; monitor eGFR before continuation.",
    "lisinopril": "Use caution and consider dose reduction with eGFR below 60 mL/min/1.73m2.",
    "gabapentin": "Reduce dose according to renal function and monitor for dizziness or sedation.",
    "nitrofurantoin": "Avoid in patients with eGFR below 60 mL/min/1.73m2 due to reduced efficacy.",
}

LIVER_SENSITIVE_DRUGS = {
    "acetaminophen": "Limit total daily dose and avoid prolonged use in patients with elevated liver enzymes.",
    "statin": "Monitor liver enzymes and consider a lower starting dose in liver disease.",
    "warfarin": "Monitor INR closely and adjust dosing in patients with liver dysfunction.",
    "amiodarone": "Use cautiously due to hepatic metabolism and risk of liver injury.",
}

NORMALIZED_CONDITION_ALIASES = {
    "heart disease": ["heart disease", "cardiovascular disease", "cad", "coronary artery disease"],
    "hypertension": ["hypertension", "high blood pressure"],
    "diabetes": ["diabetes", "type 2 diabetes", "type 1 diabetes", "t2dm", "dm"],
    "kidney disease": ["kidney disease", "chronic kidney disease", "ckd", "renal disease"],
    "liver disease": ["liver disease", "hepatic impairment", "cirrhosis"],
    "asthma": ["asthma"],
    "pregnancy": ["pregnancy", "pregnant", "gestation"],
    "elderly": ["elderly", "age 65", "age >= 65", "age >= 65 years"],
}


class DrugSafetyService:
    """Centralized service for deterministic drug safety assessment."""

    def __init__(self) -> None:
        self._initialized = True

    def analyze(
        self,
        medications: List[str],
        patient_allergies: List[str],
        patient_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        medications_clean = self._normalize_medications(medications)
        allergies_clean = self._normalize_allergies(patient_allergies)
        conditions = self._extract_patient_conditions(patient_context)

        interactions = self._build_interactions(medications_clean)
        allergies = self._build_allergy_conflicts(medications_clean, allergies_clean)
        contraindications = self._build_contraindications(medications_clean, conditions)
        pregnancy = self._build_pregnancy_safety(medications_clean, conditions)
        renal_adjustment = self._build_renal_adjustment(medications_clean, patient_context, conditions)
        liver_adjustment = self._build_liver_adjustment(medications_clean, patient_context, conditions)
        overall_risk = self._calculate_overall_risk(
            interactions=interactions,
            contraindications=contraindications,
            allergies=allergies,
            pregnancy=pregnancy,
            renal_adjustment=renal_adjustment,
            liver_adjustment=liver_adjustment,
        )

        assessment = {
            "status": "PASS" if overall_risk == "Low" else "FLAGGED",
            "overall_risk": overall_risk,
            "severity_score": self._calculate_severity_score(interactions, contraindications, allergies),
            "medications_checked": [self._render_medication(med) for med in medications_clean],
            "interactions": interactions,
            "contraindications": contraindications,
            "allergies": allergies,
            "pregnancy": pregnancy,
            "renal_adjustment": renal_adjustment,
            "liver_adjustment": liver_adjustment,
            "patient_conditions": sorted(list(conditions)),
            "alternative_medications": self._suggest_alternatives(medications_clean, interactions, contraindications, conditions),
            "recommendation": self._build_overall_recommendation(
                overall_risk,
                interactions,
                contraindications,
                allergies,
                pregnancy,
                renal_adjustment,
                liver_adjustment,
            ),
        }

        return {"drug_safety_assessment": assessment}

    def _calculate_severity_score(
        self,
        interactions: List[Dict[str, Any]],
        contraindications: List[Dict[str, Any]],
        allergies: List[Dict[str, Any]],
    ) -> int:
        """Return a 0–10 composite severity score for the full drug safety assessment."""
        score = 0
        severity_weights = {"Major": 3, "Moderate": 2, "Minor": 1}
        for item in (interactions + contraindications + allergies):
            sev = item.get("severity", "Minor")
            score += severity_weights.get(sev, 1)
        return min(score, 10)

    def _suggest_alternatives(
        self,
        medications: List[str],
        interactions: List[Dict[str, Any]],
        contraindications: List[Dict[str, Any]],
        conditions: set,
    ) -> List[Dict[str, Any]]:
        """Suggest safer alternative medications for flagged drugs."""
        _ALTERNATIVES: Dict[str, Dict[str, str]] = {
            "ibuprofen": {
                "alternative": "Acetaminophen",
                "reason": "Safer analgesic/antipyretic without cardiovascular or renal risk.",
            },
            "naproxen": {
                "alternative": "Acetaminophen",
                "reason": "Avoids NSAID-related cardiovascular and renal concerns.",
            },
            "warfarin": {
                "alternative": "Direct oral anticoagulant (DOAC, e.g., apixaban)",
                "reason": "DOACs have a more predictable pharmacokinetic profile and fewer interactions.",
            },
            "metformin": {
                "alternative": "SGLT-2 inhibitor or GLP-1 agonist",
                "reason": "Preferred in patients with moderate-to-severe renal impairment.",
            },
            "ciprofloxacin": {
                "alternative": "Azithromycin or doxycycline",
                "reason": "Avoids fluoroquinolone-associated drug interactions and tendinopathy risk.",
            },
            "diazepam": {
                "alternative": "Short-acting benzodiazepine (e.g., lorazepam 0.5 mg) or melatonin",
                "reason": "Reduces fall and cognitive impairment risk in elderly patients.",
            },
            "propranolol": {
                "alternative": "Cardioselective beta-blocker (e.g., bisoprolol or metoprolol)",
                "reason": "Avoids bronchospasm risk in asthma and masks hypoglycemia less in diabetes.",
            },
        }

        flagged_drugs: set = set()
        for item in interactions:
            for d in item.get("drugs_involved", []):
                flagged_drugs.add(d.lower().replace(" ", "_").replace("-", "_"))
        for item in contraindications:
            med = item.get("medication", "")
            if med:
                flagged_drugs.add(med.lower().replace(" ", "_").replace("-", "_"))

        suggestions: List[Dict[str, Any]] = []
        seen: set = set()
        for drug in flagged_drugs:
            norm_drug = drug.replace("_", "")
            for key, alt_info in _ALTERNATIVES.items():
                if key.replace("_", "") in norm_drug or norm_drug in key.replace("_", ""):
                    if key not in seen:
                        suggestions.append({
                            "original_medication": self._render_medication(drug),
                            "suggested_alternative": alt_info["alternative"],
                            "reason": alt_info["reason"],
                        })
                        seen.add(key)
                    break

        return suggestions


    def build_agent_output(self, assessment: Dict[str, Any]) -> tuple[List[str], List[str]]:
        warnings: List[str] = []
        evidence: List[str] = []

        for interaction in assessment.get("interactions", []):
            warnings.append(
                f"Interaction: {', '.join(interaction.get('drugs_involved', []))} - {interaction.get('severity')} severity."
            )
            evidence.append(
                f"{interaction.get('severity')} interaction between {', '.join(interaction.get('drugs_involved', []))}."
            )

        for allergy in assessment.get("allergies", []):
            warnings.append(
                f"Allergy: {allergy.get('medication')} - {allergy.get('severity')} severity."
            )
            evidence.append(
                f"Allergy conflict for {allergy.get('medication')} due to {allergy.get('allergy_type')} allergy."
            )

        for contraindication in assessment.get("contraindications", []):
            warnings.append(
                f"Contraindication: {contraindication.get('medication')} with {contraindication.get('condition')} - {contraindication.get('severity')} severity."
            )
            evidence.append(
                f"Contraindication detected for {contraindication.get('medication')} in {contraindication.get('condition')} patients."
            )

        if assessment.get("pregnancy", {}).get("category"):
            evidence.append(
                f"Pregnancy safety: {assessment['pregnancy'].get('category')} - {assessment['pregnancy'].get('explanation')}"
            )

        if assessment.get("renal_adjustment", {}).get("recommendations"):
            evidence.extend(
                [item.get("recommendation", "Renal dose adjustment recommended.") for item in assessment["renal_adjustment"].get("recommendations", [])]
            )

        if assessment.get("liver_adjustment", {}).get("recommendations"):
            evidence.extend(
                [item.get("recommendation", "Liver dose adjustment recommended.") for item in assessment["liver_adjustment"].get("recommendations", [])]
            )

        return warnings, evidence

    def _normalize_medications(self, medications: List[str]) -> List[str]:
        return [self._normalize_text(str(m)) for m in medications if str(m).strip()]

    def _normalize_allergies(self, allergies: List[str]) -> List[str]:
        return [self._normalize_text(str(a)) for a in allergies if str(a).strip()]

    def _normalize_text(self, value: str) -> str:
        cleaned = re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()
        return cleaned

    def _render_medication(self, medication: str) -> str:
        return medication.replace("_", " ").title()

    def _extract_patient_conditions(self, patient_context: Optional[Dict[str, Any]]) -> Set[str]:
        conditions: Set[str] = set()
        if not patient_context:
            return conditions

        values: List[str] = []

        def collect(value: Any) -> None:
            if isinstance(value, str):
                values.append(value.lower())
            elif isinstance(value, dict):
                for child in value.values():
                    collect(child)
            elif isinstance(value, list):
                for child in value:
                    collect(child)

        collect(patient_context.get("medical_history") or patient_context.get("history") or patient_context.get("conditions") or patient_context.get("diagnoses") or patient_context)

        age_value = patient_context.get("age")
        if isinstance(age_value, (int, float)) and age_value >= 65:
            conditions.add("elderly")

        gender = str(patient_context.get("gender", "")).lower()
        pregnancy_flag = patient_context.get("pregnancy")
        if isinstance(pregnancy_flag, bool) and pregnancy_flag:
            conditions.add("pregnancy")
        elif isinstance(pregnancy_flag, str) and pregnancy_flag.lower() in {"yes", "pregnant", "positive"}:
            conditions.add("pregnancy")
        elif "pregnant" in gender or "pregnancy" in gender:
            conditions.add("pregnancy")

        joined = " ".join(values)
        for normalized, aliases in NORMALIZED_CONDITION_ALIASES.items():
            for alias in aliases:
                if alias in joined:
                    conditions.add(normalized)
                    break

        return conditions

    def _build_interactions(self, medications: List[str]) -> List[Dict[str, Any]]:
        interactions: List[Dict[str, Any]] = []
        for i in range(len(medications)):
            for j in range(i + 1, len(medications)):
                drug1, drug2 = medications[i], medications[j]
                for interaction in KNOWN_INTERACTIONS:
                    if {drug1, drug2} == interaction["pair"]:
                        interactions.append(
                            {
                                "drugs_involved": [self._render_medication(drug1), self._render_medication(drug2)],
                                "severity": interaction["severity"],
                                "explanation": interaction["explanation"],
                                "recommendation": interaction["recommendation"],
                            }
                        )
        return interactions

    def _build_allergy_conflicts(self, medications: List[str], allergies: List[str]) -> List[Dict[str, Any]]:
        conflicts: List[Dict[str, Any]] = []
        for drug in medications:
            for allergy in allergies:
                if allergy == drug or allergy in drug or drug in allergy:
                    conflicts.append({
                        "medication": self._render_medication(drug),
                        "allergy_type": self._render_medication(allergy),
                        "severity": "Major",
                        "recommendation": f"Avoid {self._render_medication(drug)} due to documented {self._render_medication(allergy)} allergy.",
                        "explanation": f"Patient history indicates allergy to {self._render_medication(allergy)}, and the prescribed drug may cross-react.",
                    })
                elif allergy in DRUG_ALLERGY_MAP:
                    if drug in DRUG_ALLERGY_MAP[allergy]:
                        conflicts.append({
                            "medication": self._render_medication(drug),
                            "allergy_type": f"Class: {self._render_medication(allergy)}",
                            "severity": "Major",
                            "recommendation": f"Avoid {self._render_medication(drug)} because it belongs to the {self._render_medication(allergy)} drug class.",
                            "explanation": f"Medication is part of a drug class that historically cross-reacts with {self._render_medication(allergy)} allergy.",
                        })
        # Deduplicate by medication + allergy_type
        unique: List[Dict[str, Any]] = []
        seen: Set[str] = set()
        for item in conflicts:
            key = f"{item['medication']}|{item['allergy_type']}"
            if key not in seen:
                unique.append(item)
                seen.add(key)
        return unique

    def _build_contraindications(self, medications: List[str], conditions: Set[str]) -> List[Dict[str, Any]]:
        contraindications: List[Dict[str, Any]] = []
        for condition in conditions:
            rules = CONTRAINDICATION_RULES.get(condition, [])
            for rule in rules:
                for drug in medications:
                    if drug in rule["drugs"]:
                        contraindications.append(
                            {
                                "medication": self._render_medication(drug),
                                "condition": condition.replace("_", " ").title(),
                                "severity": rule["severity"],
                                "explanation": rule["explanation"],
                                "recommendation": rule["recommendation"],
                            }
                        )
        return contraindications

    def _build_pregnancy_safety(self, medications: List[str], conditions: Set[str]) -> Dict[str, Any]:
        pregnancy_data: Dict[str, Any] = {
            "category": "Not Applicable",
            "explanation": "Pregnancy safety evaluation is not indicated when pregnancy is not present.",
            "medications": [],
        }
        if "pregnancy" not in conditions:
            return pregnancy_data

        categories: Set[str] = set()
        medication_summary: List[Dict[str, Any]] = []
        for drug in medications:
            category, explanation = DRUG_PREGNANCY_SAFETY.get(
                drug,
                ("Use with caution", "Limited pregnancy safety data; use only if benefits outweigh risks."),
            )
            categories.add(category)
            medication_summary.append(
                {
                    "medication": self._render_medication(drug),
                    "category": category,
                    "explanation": explanation,
                }
            )

        if "Contraindicated" in categories:
            overall = "Contraindicated"
        elif "Use with caution" in categories:
            overall = "Use with caution"
        else:
            overall = "Safe"

        return {
            "category": overall,
            "explanation": (
                "Medication safety in pregnancy is based on the most restrictive drug in the regimen. "
                "Review the listed medications for obstetric guidance."
            ),
            "medications": medication_summary,
        }

    def _build_renal_adjustment(
        self,
        medications: List[str],
        patient_context: Optional[Dict[str, Any]],
        conditions: Set[str],
    ) -> Dict[str, Any]:
        renal_data = {
            "egfr": None,
            "creatinine": None,
            "ckd_stage": None,
            "recommendations": [],
            "avoid_drugs": [],
            "monitoring_advice": "Obtain renal function data if available to optimize dosing of renally cleared medications.",
        }
        if not patient_context:
            renal_data["monitoring_advice"] = "Renal function data unavailable. Confirm eGFR or creatinine before finalizing doses."
            return renal_data

        egfr = self._extract_numeric(patient_context.get("eGFR") or patient_context.get("egfr"))
        creatinine = self._extract_numeric(patient_context.get("creatinine"))
        ckd_stage = patient_context.get("ckd_stage")
        if isinstance(ckd_stage, str) and ckd_stage.isdigit():
            ckd_stage = int(ckd_stage)
        elif isinstance(ckd_stage, (int, float)):
            ckd_stage = int(ckd_stage)

        if egfr is not None and ckd_stage is None:
            ckd_stage = self._estimate_ckd_stage(egfr)

        renal_data["egfr"] = egfr
        renal_data["creatinine"] = creatinine
        renal_data["ckd_stage"] = ckd_stage

        for drug in medications:
            if drug not in RENAL_SENSITIVE_DRUGS:
                continue
            advice = RENAL_SENSITIVE_DRUGS[drug]
            if ckd_stage is None:
                renal_data["recommendations"].append(
                    {
                        "medication": self._render_medication(drug),
                        "recommendation": advice,
                        "avoid_drug": False,
                    }
                )
                continue

            if ckd_stage >= 4:
                renal_data["avoid_drugs"].append(self._render_medication(drug))
                renal_data["recommendations"].append(
                    {
                        "medication": self._render_medication(drug),
                        "recommendation": f"Avoid {self._render_medication(drug)} in moderate-to-severe renal impairment.",
                        "avoid_drug": True,
                    }
                )
            elif ckd_stage == 3:
                renal_data["recommendations"].append(
                    {
                        "medication": self._render_medication(drug),
                        "recommendation": f"Reduce dose of {self._render_medication(drug)} and monitor renal function frequently.",
                        "avoid_drug": False,
                    }
                )
            else:
                renal_data["recommendations"].append(
                    {
                        "medication": self._render_medication(drug),
                        "recommendation": advice,
                        "avoid_drug": False,
                    }
                )

        if renal_data["recommendations"]:
            renal_data["monitoring_advice"] = (
                "Adjust dosing for renally cleared medications based on eGFR/CKD stage and repeat renal labs as clinically indicated."
            )
        return renal_data

    def _build_liver_adjustment(
        self,
        medications: List[str],
        patient_context: Optional[Dict[str, Any]],
        conditions: Set[str],
    ) -> Dict[str, Any]:
        liver_data = {
            "alt": None,
            "ast": None,
            "bilirubin": None,
            "recommendations": [],
            "avoid_drugs": [],
            "monitoring_advice": "Obtain liver function tests if available to guide dose adjustment of hepatically cleared medications.",
        }
        if not patient_context:
            liver_data["monitoring_advice"] = "Liver function data unavailable. Confirm ALT, AST, or bilirubin before finalizing doses."
            return liver_data

        alt = self._extract_numeric(patient_context.get("ALT") or patient_context.get("alt"))
        ast = self._extract_numeric(patient_context.get("AST") or patient_context.get("ast"))
        bilirubin = self._extract_numeric(patient_context.get("bilirubin"))
        has_liver_disease = "liver disease" in conditions

        liver_data["alt"] = alt
        liver_data["ast"] = ast
        liver_data["bilirubin"] = bilirubin

        threshold_flag = (
            (alt is not None and alt > 2.5 * 40)
            or (ast is not None and ast > 2.5 * 40)
            or (bilirubin is not None and bilirubin > 1.2)
            or has_liver_disease
        )

        for drug in medications:
            if drug not in LIVER_SENSITIVE_DRUGS:
                continue
            advice = LIVER_SENSITIVE_DRUGS[drug]
            if threshold_flag:
                liver_data["avoid_drugs"].append(self._render_medication(drug))
                liver_data["recommendations"].append(
                    {
                        "medication": self._render_medication(drug),
                        "recommendation": f"Avoid {self._render_medication(drug)} in patients with liver impairment or abnormal liver tests.",
                        "avoid_drug": True,
                    }
                )
            else:
                liver_data["recommendations"].append(
                    {
                        "medication": self._render_medication(drug),
                        "recommendation": advice,
                        "avoid_drug": False,
                    }
                )

        if liver_data["recommendations"]:
            liver_data["monitoring_advice"] = (
                "Monitor liver enzymes and bilirubin regularly when using hepatically metabolized medications."
            )
        return liver_data

    def _calculate_overall_risk(
        self,
        interactions: List[Dict[str, Any]],
        contraindications: List[Dict[str, Any]],
        allergies: List[Dict[str, Any]],
        pregnancy: Dict[str, Any],
        renal_adjustment: Dict[str, Any],
        liver_adjustment: Dict[str, Any],
    ) -> str:
        if any(item.get("severity") == "Major" for item in interactions):
            return "High"
        if any(item.get("severity") == "Major" for item in contraindications):
            return "High"
        if any(item.get("severity") == "Major" for item in allergies):
            return "High"
        if pregnancy.get("category") == "Contraindicated":
            return "High"
        if renal_adjustment.get("avoid_drugs"):
            return "High"
        if liver_adjustment.get("avoid_drugs"):
            return "High"

        if any(item.get("severity") == "Moderate" for item in interactions):
            return "Medium"
        if any(item.get("severity") == "Moderate" for item in contraindications):
            return "Medium"
        if any(item.get("severity") == "Moderate" for item in allergies):
            return "Medium"
        if pregnancy.get("category") == "Use with caution":
            return "Medium"

        renal_ckd_stage = renal_adjustment.get("ckd_stage")
        has_renal_lab_or_stage = renal_adjustment.get("egfr") is not None or renal_adjustment.get("creatinine") is not None or renal_ckd_stage is not None
        if renal_ckd_stage == 3:
            return "Medium"
        if renal_ckd_stage is not None and renal_ckd_stage >= 4:
            return "High"

        liver_has_abnormal_data = (
            liver_adjustment.get("alt") is not None
            or liver_adjustment.get("ast") is not None
            or liver_adjustment.get("bilirubin") is not None
        )
        has_liver_disease = any(
            condition in {"liver disease", "hepatic impairment", "cirrhosis"}
            for condition in (liver_adjustment.get("patient_conditions") or [])
        )
        if liver_adjustment.get("avoid_drugs"):
            return "High"
        if liver_has_abnormal_data or has_liver_disease:
            if liver_adjustment.get("recommendations"):
                return "Medium"

        return "Low"

    def _build_overall_recommendation(
        self,
        overall_risk: str,
        interactions: List[Dict[str, Any]],
        contraindications: List[Dict[str, Any]],
        allergies: List[Dict[str, Any]],
        pregnancy: Dict[str, Any],
        renal_adjustment: Dict[str, Any],
        liver_adjustment: Dict[str, Any],
    ) -> str:
        if overall_risk == "High":
            return (
                "Patient medication regimen contains high-risk drug safety issues. "
                "Review interacting drugs, contraindications, allergies, and organ function adjustments before proceeding."
            )
        if overall_risk == "Medium":
            return (
                "Moderate drug safety concerns identified. Review recommendations and monitor organ function while continuing therapy."
            )
        return "Drug safety review indicates low overall risk. Continue therapy with routine monitoring."

    def _extract_numeric(self, value: Any) -> Optional[float]:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        try:
            return float(str(value).strip())
        except ValueError:
            return None

    def _estimate_ckd_stage(self, egfr: float) -> int:
        if egfr >= 90:
            return 1
        if egfr >= 60:
            return 2
        if egfr >= 30:
            return 3
        if egfr >= 15:
            return 4
        return 5


_service: Optional[DrugSafetyService] = None


def get_drug_safety_service() -> DrugSafetyService:
    global _service
    if _service is None:
        _service = DrugSafetyService()
    return _service
