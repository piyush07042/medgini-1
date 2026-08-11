"""
Reusable validation helpers.
"""

from __future__ import annotations

import re

EMAIL_PATTERN = re.compile(
    r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
)


def validate_age(age: int) -> int:
    if age < 0 or age > 120:
        raise ValueError(
            "Age must be between 0 and 120."
        )
    return age


def validate_glucose(value: float) -> float:
    if value <= 0:
        raise ValueError(
            "Glucose must be positive."
        )
    return value


def validate_bmi(value: float) -> float:
    if value <= 0:
        raise ValueError(
            "BMI must be positive."
        )
    return value


def validate_systolic_bp(value: float) -> float:
    if value <= 0:
        raise ValueError(
            "Blood pressure must be positive."
        )
    return value


def validate_email(email: str) -> str:
    if not EMAIL_PATTERN.match(email):
        raise ValueError(
            "Invalid email address."
        )
    return email