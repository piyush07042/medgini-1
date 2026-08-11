"""
Custom Exceptions for MediGenie AI Agents.

Every agent should raise one of these exceptions instead of the
generic Exception class.

Benefits
--------
- Easier debugging
- Better logging
- Supervisor can decide whether to retry or stop
- Cleaner API responses
"""


class AgentExecutionError(Exception):
    """Base exception for all agent failures."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class ValidationError(AgentExecutionError):
    """Raised when an agent receives invalid input."""


class SupervisorError(AgentExecutionError):
    """Raised by the Supervisor Agent."""


class OCRAgentError(AgentExecutionError):
    """Raised during OCR processing."""


class MedicalReportAnalysisError(AgentExecutionError):
    """Raised while extracting information from reports."""


class DiseaseRiskError(AgentExecutionError):
    """Raised by the Disease Risk Agent."""


class KnowledgeRetrievalError(AgentExecutionError):
    """Raised by the Medical Knowledge Agent."""


class DrugSafetyError(AgentExecutionError):
    """Raised by the Drug Safety Agent."""


class RecommendationError(AgentExecutionError):
    """Raised by the Recommendation Agent."""


class ReportGenerationError(AgentExecutionError):
    """Raised while generating PDF/FHIR reports."""


class DatabaseError(AgentExecutionError):
    """Raised for database-related issues."""


class AuthenticationError(AgentExecutionError):
    """Raised during authentication."""


class ConfigurationError(AgentExecutionError):
    """Raised for missing or invalid configuration."""


class ModelLoadingError(AgentExecutionError):
    """Raised when an AI/ML model cannot be loaded."""


class VectorStoreError(AgentExecutionError):
    """Raised when FAISS/Vector DB operations fail."""


class LLMServiceError(AgentExecutionError):
    """Raised when an LLM provider call fails."""