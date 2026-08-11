"""
Dashboard API schemas.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class DashboardStatSchema(BaseModel):
    title: str
    value: str
    trend: str
    positive: bool
    label: str


class RecentPatientSchema(BaseModel):
    id: int
    name: str
    age: int
    gender: str
    lastVisit: str


class RecentReportSchema(BaseModel):
    id: int
    filename: str
    uploadedAt: str
    status: str


class RecentPredictionSchema(BaseModel):
    id: int
    patient: str
    disease: str
    risk: str
    confidence: str
    date: str


class SystemStatusSchema(BaseModel):
    service: str
    status: str
    description: str


class ActivityEventSchema(BaseModel):
    id: int
    title: str
    description: str
    time: str


class PieSliceSchema(BaseModel):
    name: str
    value: int


class LinePointSchema(BaseModel):
    month: str
    predictions: int
    reports: int


class BarSliceSchema(BaseModel):
    category: str
    value: int


class AreaDataSchema(BaseModel):
    month: str
    generated: int


class DashboardSummarySchema(BaseModel):
    pending_reports: int
    high_risk_patients: int
    text: str


class DashboardDataSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    stats: list[DashboardStatSchema]
    recent_patients: list[RecentPatientSchema]
    recent_reports: list[RecentReportSchema]
    recent_predictions: list[RecentPredictionSchema]
    system_status: list[SystemStatusSchema]
    activity: list[ActivityEventSchema]
    prediction_distribution: list[PieSliceSchema]
    monthly_trends: list[LinePointSchema]
    risk_distribution: list[BarSliceSchema]
    reports_area: list[AreaDataSchema]
    summary: DashboardSummarySchema
